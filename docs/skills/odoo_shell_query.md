---
name: odoo-shell-query
description: Query Odoo database records by ID or domain using the Odoo shell. Use when the user asks to check, inspect, or verify data stored in the Odoo database, or to confirm field values, relationships, or record existence.
metadata:
  short-description: Inspect Odoo database records via shell
---

# Odoo Shell Query

## Method 1: Odoo Shell (Preferred — First Choice)

### 标准命令（Odoo19 Freight 项目）

在项目根目录 `odoo19_freight` 下，先激活虚拟环境，再运行：

```bash
source venv/bin/activate
python3 odoo-bin shell -c odoo.conf
```

数据库名已写在 `odoo.conf`（`db_name = odoo19_freight`），因此不需要显式 `-d`。如需显式指定，可加：

```bash
python3 odoo-bin shell -c odoo.conf -d odoo19_freight
```

Use `echo` pipe to run non-interactive one-liners. This is the preferred method for all data queries.

### Syntax
```bash
echo "PYTHON_CODE" | python3 odoo-bin shell -c odoo.conf -d odoo19_freight
```

### 非交互 one-liner（推荐给 Codex / CI）
```bash
echo "res = env['MODEL'].browse(ID); print(res.NAME, res.FIELD, ...)" | \
  python3 odoo-bin shell -c odoo.conf -d odoo19_freight
```

**Important**: This requires `sandbox_permissions: require_escalated` — database access is sandboxed.

### Examples

#### Check a record
```python
res = env['freight.shipment'].browse(1)
print(f"ID={res.id} Name={res.name} Transport={res.transport} Stage={res.stage_id.name if res.stage_id else 'NONE'}")
```

#### Check multiple records with domain
```python
recs = env['freight.shipment'].search([('direction', '=', 'export')], limit=5)
for r in recs:
    print(r.id, r.name, r.transport, r.consignee_id.name if r.consignee_id else '-')
```

#### Check if an action external ID exists
```python
import ast
entry = env['ir.model.data'].sudo().search([('module', '=', 'tk_freight'), ('name', '=', 'freight_shipment_all_action')])
if entry:
    print(f"EXISTS: model={entry.model} res_id={entry.res_id}")
else:
    print("NOT FOUND")
```

## Method 2: psycopg2 Direct Query (Last Resort — Extreme Cases Only)

Only use when Odoo shell is genuinely unavailable. Odoo shell is always preferred.

```python
import psycopg2
conn = psycopg2.connect(host='127.0.0.1', port=5555, user='odoo', password='odoo', dbname='odoo19_freight')
cur = conn.cursor()
cur.execute("SELECT id, name, transport FROM freight_shipment WHERE id = %s", [1])
row = cur.fetchone()
conn.close()
```

## Common Table / Model Name Mappings

| Model (for shell) | Table (for raw SQL) |
|---|---|
| `freight.shipment` | `freight_shipment` |
| `shipment.quotation` | `shipment_quotation` |
| `shipment.freight.booking` | `shipment_freight_booking` |
| `freight.service` | `freight_service` |
| `freight.route` | `freight_route` |
| `account.move` | `account_move` |
| `res.partner` | `res_partner` |
| `stock.warehouse` | `stock_warehouse` |
| `ir.model.data` | `ir_model_data` |

## Quick Reference: Odoo ORM Shell

### Browse by ID
`env['model'].browse(id)` → single record

### Search by domain
`env['model'].search([('field', 'operator', value)])` → recordset

### Read fields
`record.field_name` → field value (including related/Many2one)

### Related fields (Many2one)
`record.consignee_id.name` → follow the relation

### One2many / inverse
`record.line_ids` → recordset of lines
`len(record.line_ids)` → count

### Check if record exists
`env['model'].search_count([('field', '=', 'value')])` → integer

### Check external ID
`env.ref('tk_freight.freight_shipment_all_action')` → record or raise ValueError
