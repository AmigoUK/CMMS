# Custom Fields Per Site

## Context

Different sites need different data on their assets. Transport (TR) needs MOT Date and Insurance Date for vans. Bakery Mazowsze (BM) might need Gas Safety Certificate Date. Each site should define up to 5 custom fields with configurable types, and every asset at that site gets those fields.

## Approach: Fixed Columns

Add 5 `custom_field_N` text columns to Asset and 15 definition columns to Site (label, type, required x5). No new tables, no new models. Matches existing codebase patterns exactly.

## Data Model

### Site additions (15 columns)

For N = 1..5:
- `custom_field_N_label` -- String(100), default="" -- field label (empty = not used)
- `custom_field_N_type` -- String(20), default="" -- "text", "long_text", "date", or "image"
- `custom_field_N_required` -- Boolean, default=False

Helper property on Site:
```python
@property
def custom_field_definitions(self):
    """Return list of active custom field defs as dicts."""
    defs = []
    for i in range(1, 6):
        label = getattr(self, f'custom_field_{i}_label', '')
        ftype = getattr(self, f'custom_field_{i}_type', '')
        if label:
            defs.append({
                'index': i,
                'label': label,
                'type': ftype or 'text',
                'required': getattr(self, f'custom_field_{i}_required', False),
                'field_name': f'custom_field_{i}',
            })
    return defs
```

### Asset additions (5 columns)

- `custom_field_1` through `custom_field_5` -- Text, default=""

All values stored as text: dates as ISO strings ("2026-06-15"), images as filenames, text/long_text directly.

Helper method on Asset:
```python
def get_custom_field(self, index):
    return getattr(self, f'custom_field_{index}', '')
```

## Admin UI

### Site edit page (`templates/admin/site_form.html`)

Add "Custom Fields" card below existing site info (only in edit mode, not create):
- 5 fixed rows, each with: Label (text input), Type (select: text/long_text/date/image), Required (checkbox)
- Empty label = field slot not used
- Same `<form>`, same submit button -- processed in existing `update_site()` route

### Admin route changes (`blueprints/admin/routes.py`)

In `update_site()`, loop through range(1,6) and set:
```python
site.custom_field_N_label = request.form.get(f'custom_field_{N}_label', '').strip()
site.custom_field_N_type = request.form.get(f'custom_field_{N}_type', '').strip()
site.custom_field_N_required = f'custom_field_{N}_required' in request.form
```

## Asset Form (`templates/assets/form.html`)

Add "Custom Fields" card after Description & Notes, before submit buttons. Only renders if `g.current_site.custom_field_definitions` is non-empty.

For each defined field, render input based on type:
- **text**: `<input type="text">`
- **long_text**: `<textarea rows="3">`
- **date**: `<input type="date">`
- **image**: `<input type="file">` with preview and remove checkbox

Values accessed via `getattr(asset, field_name)` or `asset.get_custom_field(index)`.

## Asset Detail (`templates/assets/detail.html`)

Add "Site-Specific Details" card after Description & Notes. Table with label/value rows:
- **text**: plain text
- **long_text**: `<div style="white-space: pre-wrap">`
- **date**: formatted with strftime
- **image**: `<img>` thumbnail

## Asset Routes (`blueprints/assets/routes.py`)

In `create()` and `update()`, after processing standard fields:
```python
for field_def in g.current_site.custom_field_definitions:
    fn = field_def['field_name']
    if field_def['type'] == 'image':
        # handle file upload to instance/uploads/custom/
    else:
        setattr(asset, fn, request.form.get(fn, '').strip())
```

## DB Migration

One-time ALTER TABLE (db.create_all() doesn't add columns to existing tables):

```sql
-- Site custom field definitions
ALTER TABLE sites ADD COLUMN custom_field_1_label VARCHAR(100) DEFAULT '';
ALTER TABLE sites ADD COLUMN custom_field_1_type VARCHAR(20) DEFAULT '';
ALTER TABLE sites ADD COLUMN custom_field_1_required TINYINT(1) DEFAULT 0;
-- ... repeat for 2-5

-- Asset custom field values  
ALTER TABLE assets ADD COLUMN custom_field_1 TEXT DEFAULT '';
-- ... repeat for 2-5
```

## Example Configuration

**TR (Transport):**
| # | Label | Type | Required |
|---|-------|------|----------|
| 1 | MOT Expiry Date | date | Yes |
| 2 | Insurance Expiry Date | date | Yes |
| 3 | Insurance Provider | text | No |
| 4 | Insurance Notes | long_text | No |
| 5 | Vehicle Photo | image | No |

**BM (Bakery Mazowsze):**
| # | Label | Type | Required |
|---|-------|------|----------|
| 1 | Gas Safety Certificate | date | No |
| 2 | Last PAT Test | date | No |
| 3 | | | |

## Files to Modify

| File | Changes |
|------|---------|
| `models/site.py` | Add 15 custom_field definition columns + helper property |
| `models/asset.py` | Add 5 custom_field value columns + helper method |
| `blueprints/admin/routes.py` | Handle custom field defs in update_site() |
| `templates/admin/site_form.html` | Add Custom Fields card (5-row table) |
| `blueprints/assets/routes.py` | Handle custom field values in create/update, image uploads |
| `templates/assets/form.html` | Add dynamic Custom Fields card |
| `templates/assets/detail.html` | Add Site-Specific Details card |
| `seed_translations.py` | ~10 new translation keys |

## Verification

1. Admin: edit TR site, define MOT Date (date, required) + Insurance Date (date)
2. Asset form on TR: shows MOT Date + Insurance Date inputs, not on BM/OB
3. Save asset with dates: values persist and display on detail page
4. Image custom field: upload, preview, remove works
5. Required validation: empty required field blocked
6. Date formatting: ISO in form, formatted on detail page
