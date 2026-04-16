from extensions import db
from models.part import Part, StockAdjustment


def get_low_stock_count(site_id):
    """Count active parts at or below minimum stock for a site."""
    return Part.query.filter(
        Part.site_id == site_id,
        Part.is_active == True,
        Part.minimum_stock > 0,
        Part.quantity_on_hand <= Part.minimum_stock,
    ).count()


def get_low_stock_parts(site_id, limit=None):
    """Return active parts at or below minimum stock, ordered by severity."""
    query = Part.query.filter(
        Part.site_id == site_id,
        Part.is_active == True,
        Part.minimum_stock > 0,
        Part.quantity_on_hand <= Part.minimum_stock,
    ).order_by(
        Part.quantity_on_hand.asc(),
        Part.name,
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def adjust_stock(part, quantity, adjustment_type, reason, user_id, part_usage_id=None):
    """Adjust stock level and create an audit record.

    quantity: positive to add, negative to remove.
    Returns the StockAdjustment record.
    """
    before = part.quantity_on_hand
    part.quantity_on_hand = max(0, part.quantity_on_hand + quantity)
    after = part.quantity_on_hand

    adjustment = StockAdjustment(
        part_id=part.id,
        adjustment_type=adjustment_type,
        quantity=quantity,
        quantity_before=before,
        quantity_after=after,
        reason=reason,
        part_usage_id=part_usage_id,
        adjusted_by_id=user_id,
    )
    db.session.add(adjustment)
    return adjustment
