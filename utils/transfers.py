"""Inter-site part transfer service.

All transfer state changes go through this module. Route handlers must not
touch db.session directly for transfer mutations, so invariants (permission
gating, pessimistic locking, atomic status transitions) are enforced in one
place and also apply to CLI / scripts / tests.
"""

from datetime import datetime, timezone

from extensions import db
from models.part import Part, PartTransfer
from models.site import Site
from utils.stock import adjust_stock


class TransferError(Exception):
    """Base class for transfer errors. Routes map to 4xx responses."""


class PermissionDenied(TransferError):
    """Actor is not permitted to perform this transfer action."""


class InvalidTransferState(TransferError):
    """Attempted a state transition that is not allowed from the current status."""


class TransferAlreadyResolved(InvalidTransferState):
    """Transfer is already completed or cancelled; cannot be approved again."""


class InsufficientStock(TransferError):
    """Source part does not have enough quantity on hand to complete the transfer."""


class InvalidTransferRequest(TransferError):
    """Request itself is malformed (same source & destination site, bad quantity, etc.)."""


def _now():
    return datetime.now(timezone.utc)


def request_transfer(*, source_part, destination_site, quantity, notes, requested_by):
    """Create a pending PartTransfer. Caller is responsible for commit.

    Permission: requester must be supervisor at source site (or admin).
    """
    if source_part is None or destination_site is None:
        raise InvalidTransferRequest("Source part and destination site are required.")
    if source_part.site_id == destination_site.id:
        raise InvalidTransferRequest("Source and destination sites must differ.")
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvalidTransferRequest("Quantity must be a positive integer.")
    if quantity > (source_part.quantity_on_hand or 0):
        raise InsufficientStock(
            f"Source has only {source_part.quantity_on_hand} on hand, requested {quantity}."
        )
    if not requested_by.is_supervisor_at(source_part.site_id):
        raise PermissionDenied("Requester must be a supervisor at the source site.")

    transfer = PartTransfer(
        source_site_id=source_part.site_id,
        destination_site_id=destination_site.id,
        source_part_id=source_part.id,
        destination_part_id=None,
        part_number_snapshot=source_part.part_number or "",
        name_snapshot=source_part.name or "",
        quantity=quantity,
        unit_cost_at_transfer=source_part.unit_cost or 0.0,
        status="pending",
        notes=notes or "",
        requested_by_id=requested_by.id,
        requested_at=_now(),
    )
    db.session.add(transfer)
    return transfer


def _resolve_destination_part(source_part, destination_site):
    """Find an existing Part in destination_site with matching part_number,
    else create a new one copying catalog fields with zero stock.
    """
    if source_part.part_number:
        dst = (
            Part.query.filter_by(
                site_id=destination_site.id,
                part_number=source_part.part_number,
            )
            .first()
        )
        if dst is not None:
            return dst

    dst = Part(
        site_id=destination_site.id,
        name=source_part.name,
        part_number=source_part.part_number,
        description=source_part.description or "",
        category=source_part.category or "",
        unit=source_part.unit or "each",
        unit_cost=source_part.unit_cost or 0.0,
        quantity_on_hand=0,
        minimum_stock=source_part.minimum_stock or 0,
        maximum_stock=source_part.maximum_stock or 0,
        image=source_part.image or "",
        supplier_id=source_part.supplier_id,
        supplier_part_number=source_part.supplier_part_number or "",
        storage_location="",
        is_active=True,
    )
    db.session.add(dst)
    db.session.flush()  # so dst.id is available for locking/linking
    return dst


def approve_and_complete(*, transfer, approver):
    """Atomically complete a pending transfer.

    Steps: lock source Part, re-check status, verify sufficient stock,
    resolve/create destination Part, two stock adjustments, link adjustments,
    flip to completed. Commits the session on success; rolls back on failure.
    """
    if not approver.is_supervisor_at(transfer.destination_site_id):
        raise PermissionDenied(
            "Approver must be a supervisor at the destination site."
        )

    try:
        # Lock the transfer and source part to serialise concurrent approvals.
        # with_for_update is a no-op on SQLite but enforced on MariaDB.
        db.session.refresh(transfer, with_for_update=True)
        if transfer.status != "pending":
            raise TransferAlreadyResolved(
                f"Transfer #{transfer.id} is already {transfer.status}."
            )

        source = (
            Part.query.filter_by(id=transfer.source_part_id)
            .with_for_update()
            .one()
        )
        if (source.quantity_on_hand or 0) < transfer.quantity:
            raise InsufficientStock(
                f"Source now has {source.quantity_on_hand} on hand, "
                f"transfer requires {transfer.quantity}."
            )

        destination_site = db.session.get(Site, transfer.destination_site_id)
        destination = _resolve_destination_part(source, destination_site)
        # Deterministic lock order avoids deadlocks on MariaDB.
        if destination.id < source.id:
            Part.query.filter_by(id=destination.id).with_for_update().one()

        reason = f"Transfer #{transfer.id}"
        src_adj = adjust_stock(
            source, -transfer.quantity, "transfer_out", reason, approver.id
        )
        dst_adj = adjust_stock(
            destination, transfer.quantity, "transfer_in", reason, approver.id
        )
        db.session.flush()  # materialise adjustment ids before linking

        transfer.destination_part_id = destination.id
        transfer.source_adjustment_id = src_adj.id
        transfer.destination_adjustment_id = dst_adj.id
        transfer.approved_by_id = approver.id
        transfer.approved_at = _now()
        transfer.completed_at = _now()
        transfer.status = "completed"

        db.session.commit()
        return transfer
    except Exception:
        db.session.rollback()
        raise


def cancel_transfer(*, transfer, canceller, reason=""):
    """Cancel a pending transfer. No stock movement. Commits on success.

    Allowed: requester, supervisor at either side, admin.
    """
    if transfer.status != "pending":
        raise TransferAlreadyResolved(
            f"Transfer #{transfer.id} is already {transfer.status}."
        )

    allowed = (
        canceller.id == transfer.requested_by_id
        or canceller.is_supervisor_at(transfer.source_site_id)
        or canceller.is_supervisor_at(transfer.destination_site_id)
    )
    if not allowed:
        raise PermissionDenied(
            "Only the requester or a supervisor on either side may cancel."
        )

    transfer.status = "cancelled"
    transfer.cancelled_by_id = canceller.id
    transfer.cancelled_at = _now()
    transfer.cancellation_reason = reason or ""
    db.session.commit()
    return transfer
