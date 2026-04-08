# Supplier Management Module

## Context

Each Part currently stores supplier info as 3 plain text fields (`supplier`, `supplier_part_number`, `supplier_email`). In practice one supplier provides many parts, so this data should be normalized into a proper Supplier entity. The user also wants a link to the supplier's online shop/ordering system.

## Scope

1. New `Supplier` model -- global entity (no site scoping)
2. New `suppliers` blueprint with full CRUD (list, detail, create, edit, toggle active)
3. Part model: replace `supplier`/`supplier_email` text fields with `supplier_id` FK
4. Part form: dropdown supplier select + quick-create modal
5. Reorder report: group by FK relationship, show contact info + shop URL with "Order Online" button
6. Seed data: 5 UK-based demo suppliers assigned to all 15 parts
7. Translations: ~20 new keys (EN + PL)

## Data Model

### Supplier (new model: `models/supplier.py`)

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK |
| name | String(200) | NOT NULL, unique, indexed |
| contact_person | String(200) | default="" |
| email | String(200) | default="" |
| phone | String(50) | default="" |
| address | String(500) | default="" |
| shop_url | String(500) | default="" -- online shop/ordering portal |
| notes | Text | default="" -- payment terms, account number, etc. |
| is_active | Boolean | default=True |
| created_at | DateTime | UTC auto |
| updated_at | DateTime | UTC auto + onupdate |

Relationship: `parts = db.relationship("Part", backref="supplier_rel", lazy="select")`

Backref is `supplier_rel` (not `supplier`) to avoid collision with the old string column during transition.

### Part model changes

- ADD: `supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)`
- KEEP: `supplier_part_number` -- stays on Part (part-specific catalog number)
- REMOVE: `supplier` (String) -- moved to Supplier.name
- REMOVE: `supplier_email` (String) -- moved to Supplier.email

Since seed data has no supplier values populated, migration is clean: drop old columns, add new FK, re-seed.

## Blueprint: `/suppliers/`

### Routes (all `@supervisor_required`)

| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| GET | `/suppliers/` | list_suppliers | Paginated list with search |
| GET | `/suppliers/<id>` | detail | Supplier info + linked parts |
| GET | `/suppliers/new` | new | Create form |
| POST | `/suppliers/new` | create | Create supplier |
| GET | `/suppliers/<id>/edit` | edit | Edit form |
| POST | `/suppliers/<id>/edit` | update | Update supplier |
| POST | `/suppliers/<id>/toggle` | toggle | Activate/deactivate |
| POST | `/suppliers/quick-create` | quick_create | AJAX: create from part form |

### Templates

**`templates/suppliers/index.html`** -- List page
- Search by name, contact, email
- Filter tabs: Active (default) / Inactive
- Table: Name (linked), Contact Person, Email, Phone, Parts count (badge), Actions
- Pagination, empty state

**`templates/suppliers/form.html`** -- Create/Edit form
- Card with fields: name (required), contact_person, email, phone, address, shop_url, notes
- is_active checkbox (edit mode only)
- Save/Cancel buttons

**`templates/suppliers/detail.html`** -- Detail page
- Supplier info card: contact, email (mailto), phone, address, shop_url (external link), notes
- Parts card: table of linked parts with name, part number, supplier part number, stock level (progress bar), unit cost
- Low-stock alert banner if any parts need reorder

## Changes to Parts Module

### Part form (`templates/parts/form.html`)
Replace 3 text inputs (supplier name, email) with:
- `<select>` dropdown for `supplier_id` listing active suppliers
- "New" button opening a quick-create modal (AJAX POST to `/suppliers/quick-create`)
- Keep `supplier_part_number` text input

### Part detail (`templates/parts/detail.html`)
Replace `part.supplier` / `part.supplier_email` display with:
- Linked supplier name -> supplier detail page
- Show email, phone, shop_url from relationship
- If `supplier_rel.shop_url`: show "Order Online" link

### Part list (`templates/parts/index.html`)
- Supplier column: `part.supplier_rel.name` linked to supplier detail

### Part routes (`blueprints/parts/routes.py`)
- `list_parts()`: search filter joins Supplier.name instead of Part.supplier string
- `new()`/`edit()`: pass `suppliers` queryset to template
- `create()`/`update()`: read `supplier_id` from form
- `reorder_report()`: eager-load supplier_rel, order by supplier_id

### Reorder report (`templates/parts/reorder.html`)
- Main table: supplier column links to supplier detail
- Grouped section: group by `supplier_id`, header shows supplier name (linked), contact, email (mailto), phone, and **"Order Online" button** linking to `shop_url`
- Per-group subtotal for reorder cost

## Navigation

Add to navbar (`_navbar.html`) after Parts link, within `{% if current_user.is_supervisor %}` block:
```html
<li class="nav-item">
    <a class="nav-link ..." href="{{ url_for('suppliers.list_suppliers') }}">
        <i class="bi bi-truck me-1"></i>{{ _('ui.navbar.suppliers') }}
    </a>
</li>
```

## Seed Data

5 suppliers:
1. **Brammer Buck & Hickman** -- Electrical/Industrial (contactors, overloads, fuses) -- shop: uk.rs-online.com
2. **Fridgetech Supplies** -- Refrigeration (oil, filters, refrigerant) -- shop: fridgetechsupplies.co.uk
3. **BakerParts Direct** -- Bakery equipment (belts, bearings, seals, elements, gaskets) -- shop: bakerpartsdirect.co.uk
4. **Cromwell Industrial Tools** -- General supplies (fixings, sealants) -- shop: cromwell.co.uk
5. **LED Lighting Direct** -- Lighting (LED tubes) -- shop: ledlightingdirect.co.uk

All 15 parts assigned to appropriate suppliers.

## Files Summary

| File | Action |
|------|--------|
| `models/supplier.py` | NEW -- Supplier model |
| `models/part.py` | Add supplier_id FK, remove supplier/supplier_email columns |
| `models/__init__.py` | Export Supplier |
| `app.py` | Register suppliers blueprint |
| `blueprints/suppliers/__init__.py` | NEW -- blueprint init |
| `blueprints/suppliers/routes.py` | NEW -- CRUD + quick-create routes |
| `templates/suppliers/index.html` | NEW -- list page |
| `templates/suppliers/form.html` | NEW -- create/edit form |
| `templates/suppliers/detail.html` | NEW -- detail with parts list |
| `templates/partials/_navbar.html` | Add Suppliers link |
| `blueprints/parts/routes.py` | Update search, create, update, reorder |
| `templates/parts/form.html` | Supplier dropdown + quick-create modal |
| `templates/parts/detail.html` | Linked supplier display + shop URL |
| `templates/parts/index.html` | Supplier column from relationship |
| `templates/parts/reorder.html` | Group by FK, show contact + "Order Online" |
| `seed_demo.py` | Add 5 suppliers, assign to parts |
| `seed_translations.py` | ~20 new keys (EN + PL) |

## Verification

1. Seed demo data, verify 5 suppliers created, all 15 parts assigned
2. Supplier list: search, pagination, active/inactive filter
3. Supplier detail: shows linked parts with stock levels
4. Create/edit supplier: validation, duplicate name check
5. Part form: dropdown works, quick-create modal creates supplier and selects it
6. Reorder report: grouped by supplier FK with "Order Online" button
7. Navbar: Suppliers link visible for supervisor+, active state works
