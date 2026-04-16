"""Enhanced reorder analysis: pending-inbound netting + cross-site surplus suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from extensions import db
from models import Part, PartTransfer


@dataclass(frozen=True)
class SurplusAt:
    site_id: int
    site_code: str
    quantity_on_hand: int
    maximum_stock: int


@dataclass
class ReorderRow:
    part: Part
    pending_inbound: int = 0
    surplus_elsewhere: list = None  # list of SurplusAt

    @property
    def adjusted_shortfall(self) -> int:
        """Units still needed after netting pending inbound transfers."""
        if self.part.minimum_stock <= 0:
            return 0
        gap = self.part.minimum_stock - (self.part.quantity_on_hand + self.pending_inbound)
        return max(0, gap)

    @property
    def needs_ordering(self) -> bool:
        return self.adjusted_shortfall > 0 and not self.surplus_elsewhere

    @property
    def has_transfer_option(self) -> bool:
        return self.adjusted_shortfall > 0 and bool(self.surplus_elsewhere)


def _pending_inbound_for(part_id: int) -> int:
    total = (
        db.session.query(db.func.coalesce(db.func.sum(PartTransfer.quantity), 0))
        .filter(
            PartTransfer.destination_part_id == part_id,
            PartTransfer.status == "pending",
        )
        .scalar()
    )
    return int(total or 0)


def _surplus_elsewhere(part: Part) -> list:
    """Parts with the same part_number in OTHER sites whose stock exceeds
    their own max. Returns SurplusAt rows sorted by most surplus first."""
    if not part.part_number:
        return []
    from models import Site
    rows = (
        db.session.query(Part, Site)
        .join(Site, Site.id == Part.site_id)
        .filter(
            Part.part_number == part.part_number,
            Part.site_id != part.site_id,
            Part.is_active == True,  # noqa: E712
            Part.maximum_stock > 0,
            Part.quantity_on_hand > Part.maximum_stock,
        )
        .all()
    )
    rows.sort(key=lambda r: (r[0].quantity_on_hand - r[0].maximum_stock), reverse=True)
    return [
        SurplusAt(
            site_id=s.id, site_code=s.code,
            quantity_on_hand=p.quantity_on_hand,
            maximum_stock=p.maximum_stock,
        )
        for (p, s) in rows
    ]


def enrich_reorder_rows(parts):
    """Given an iterable of low-stock Parts, return ReorderRow objects with
    pending-inbound netting and cross-site surplus suggestions attached.
    """
    rows = []
    for p in parts:
        row = ReorderRow(
            part=p,
            pending_inbound=_pending_inbound_for(p.id),
            surplus_elsewhere=_surplus_elsewhere(p),
        )
        rows.append(row)
    return rows
