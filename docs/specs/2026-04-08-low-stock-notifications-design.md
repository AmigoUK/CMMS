# Low-Stock Notifications & Stock Management

## Context

The CMMS already tracks parts inventory with `quantity_on_hand`, `minimum_stock`, and `maximum_stock` fields on the Part model. Stock is deducted when parts are logged against work orders via PartUsage. However, there is **no visibility** when stock drops below minimum -- no alerts, no dashboard indicators, no navbar badges. Additionally, the only way to add stock back is to manually edit the part form, leaving no audit trail. This feature adds the notification layer and proper stock management tools.

## Scope

1. **Flash alerts** on part usage when stock drops below minimum or hits zero
2. **Dashboard section** showing low-stock parts (stat card + alert table)
3. **Navbar badge** showing low-stock count on every page
4. **Stock adjustment** (restock) with audit trail via new `StockAdjustment` model
5. **Part usage reversal** to undo mistaken entries and return stock
6. **Seed data** updates for demo visibility
7. **Translations** (EN + PL)

## Design

### 1. Flash Alerts on Part Usage

**File:** `blueprints/workorders/routes.py` - `add_part()` route (line 420)

Replace the generic `flash("Part recorded.", "success")` at line 451 with conditional logic:

- `quantity_on_hand == 0` after deduction: `flash("Part recorded. WARNING: '{name}' is now OUT OF STOCK.", "danger")`
- `is_low_stock` after deduction: `flash("Part recorded. '{name}' is below minimum stock ({qty} remaining, minimum {min}).", "warning")`
- Otherwise: `flash("Part recorded.", "success")` (unchanged)

The `minimum_stock == 0` (not configured) case is safe -- `is_low_stock` returns `False`. Zero stock still triggers even without a minimum configured.

### 2. Dashboard Low-Stock Section

**Files:** `blueprints/dashboard/routes.py`, `templates/dashboard/index.html`

**Backend:** Add query for technician+ users in `index()`:
```python
low_stock_parts = Part.query.filter(
    db.or_(Part.site_id == site_id, Part.site_id.is_(None)),
    Part.is_active == True,
    Part.minimum_stock > 0,
    Part.quantity_on_hand <= Part.minimum_stock,
).order_by(Part.quantity_on_hand.asc(), Part.name).limit(10).all()
```

**Template - stat card:** 4th card in the top row, `bg-danger`, icon `bi-box-seam`, links to `parts.list_parts?show=reorder`. Only shown when `low_stock_count > 0` and user is technician+.

**Template - alert table:** Card section (border-danger, header bg-danger bg-opacity-10) with columns: Part Name (linked), On Hand, Minimum, Status badge (OUT OF STOCK vs Low Stock). "View All" button links to reorder view. Placed after triage queue, before "My Assigned Work Orders".

### 3. Navbar Badge

**Files:** `app.py` (context processor), `templates/partials/_navbar.html`

**Context processor** (`inject_globals()` at line 173): Add `low_stock_count` to context for technician+ users. Single COUNT query per request -- negligible cost.

```python
ctx["low_stock_count"] = 0
if site and current_user.has_role_at_least("technician"):
    ctx["low_stock_count"] = Part.query.filter(...).count()
```

**Navbar:**
- Supervisors/admins: append `<span class="badge bg-danger">N</span>` to existing Parts nav link
- Technicians (who can't see Parts link): standalone warning icon `bi-exclamation-triangle-fill` with badge, linking to dashboard

### 4. StockAdjustment Model (Audit Trail)

**File:** `models/part.py`

```python
class StockAdjustment(db.Model):
    __tablename__ = "stock_adjustments"

    id              - Integer PK
    part_id         - FK parts.id, NOT NULL
    adjustment_type - String(20): 'restock', 'correction', 'return', 'reversal'
    quantity        - Integer (positive = add, negative = remove)
    quantity_before - Integer
    quantity_after  - Integer
    reason          - String(500)
    part_usage_id   - FK part_usages.id, nullable (for reversals)
    adjusted_by_id  - FK users.id, NOT NULL
    created_at      - DateTime UTC
```

Relationships: `part`, `adjusted_by`, `part_usage`

### 5. Stock Adjustment Route

**File:** `blueprints/parts/routes.py`

`POST /parts/<id>/adjust` (supervisor_required):
- Form fields: `quantity` (int, required), `adjustment_type` (restock/correction), `reason` (text)
- Creates StockAdjustment record with before/after quantities
- Updates `part.quantity_on_hand`
- Flash confirmation message

**UI:** Add a collapsible "Adjust Stock" form on the part detail page (`templates/parts/detail.html`) visible to supervisors.

### 6. Part Usage Reversal

**File:** `models/part.py` - add `is_reversed` Boolean to PartUsage (default False)

**File:** `blueprints/workorders/routes.py`

`POST /workorders/<id>/part/<usage_id>/reverse` (supervisor_required):
- Marks PartUsage.is_reversed = True
- Returns quantity to Part.quantity_on_hand
- Creates StockAdjustment with type='reversal'
- Flash confirmation

**UI:** Add a small "Reverse" button on each part usage row in the WO detail page, visible to supervisors only, hidden for already-reversed entries. Reversed entries shown with strikethrough styling.

### 7. Helper Module

**File:** `utils/stock.py` (NEW)

Functions:
- `get_low_stock_parts(site_id, limit=None)` - returns Part query results
- `get_low_stock_count(site_id)` - COUNT query for context processor
- `adjust_stock(part, quantity, adjustment_type, reason, user_id, part_usage_id=None)` - creates StockAdjustment + updates part

### 8. Model Additions

**File:** `models/part.py`

Add to Part:
```python
@property
def is_out_of_stock(self):
    return self.quantity_on_hand == 0 and self.minimum_stock > 0
```

Add to PartUsage:
```python
is_reversed = db.Column(db.Boolean, default=False)
```

Export `StockAdjustment` from `models/__init__.py`.

### 9. Seed Data

**File:** `seed_demo.py`

Set 5 parts to low/zero stock for demo:
- Thermal Overload: qty=2, min=2 (at minimum)
- Mixer Bowl Seal: qty=0, min=1 (out of stock)
- Oven Element: qty=1, min=1 (at minimum)
- Door Gasket: qty=1, min=2 (below minimum)
- Bearing 6205: qty=4, min=5 (below minimum)

Add `maximum_stock` values to a few parts for better progress bar display.

### 10. Translations

**File:** `seed_translations.py`

New keys (EN + PL):
- `ui.label.low_stock_parts`, `ui.label.low_stock_alert`, `ui.label.out_of_stock`
- `ui.label.adjust_stock`, `ui.label.add_stock`, `ui.label.adjustment_reason`
- `ui.button.reverse_usage`
- `flash.stock_adjusted`, `flash.part_usage_reversed`

## Files Summary

| File | Action |
|------|--------|
| `models/part.py` | Add `is_out_of_stock` prop, `is_reversed` on PartUsage, `StockAdjustment` model |
| `models/__init__.py` | Export StockAdjustment |
| `utils/stock.py` | NEW - query helpers + adjust_stock() |
| `app.py` | Extend context processor with low_stock_count |
| `blueprints/workorders/routes.py` | Conditional flash on add_part, add reverse_part_usage route |
| `blueprints/dashboard/routes.py` | Add low-stock query to index() |
| `blueprints/parts/routes.py` | Add adjust_stock route |
| `templates/dashboard/index.html` | Stat card + alert table |
| `templates/partials/_navbar.html` | Badge on Parts link + technician indicator |
| `templates/parts/detail.html` | Adjust stock form (supervisor) |
| `templates/workorders/detail.html` | Reverse button on part usage rows |
| `static/css/style.css` | .row-low-stock border-left, reversed usage styling |
| `seed_demo.py` | Low-stock demo data |
| `seed_translations.py` | New translation keys |

## Verification

1. Seed the demo data, verify 5 parts show as low stock
2. Log in as technician -- check dashboard shows stat card + alert table
3. Log in as supervisor -- check navbar badge on Parts link
4. Go to a work order, add a part that has low stock -- verify warning flash
5. Add a part until stock hits 0 -- verify danger flash
6. As supervisor, go to part detail, adjust stock upward -- verify audit trail
7. As supervisor, reverse a part usage on a work order -- verify stock restored
8. Switch sites -- verify low-stock counts are site-scoped
