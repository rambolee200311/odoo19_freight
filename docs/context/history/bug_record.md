# Bug 记录

## BUG-TK-001: 服务端动作缩进错误

- 发现时间: 2026-08-11
- 根因文件: `views/freight_shipment_view.xml`（`ir_actions_server_freight_create_*`）
- 错误类型: Python IndentationError
- 状态: 🔴 待修复
- 关联债务: TD-006

## BUG-TK-002: 供应商账单按 sale 计价

- 发现时间: 2026-08-11
- 根因文件: `models/freight_shipment.py`（`action_create_vendor_bill`）
- 错误类型: 业务逻辑错误，成本口径错误
- 状态: 🔴 待修复
- 关联债务: TD-001

## BUG-TK-003: 多币种直接相加

- 发现时间: 2026-08-11
- 根因文件: `models/freight_shipment.py`（`_compute_total_amount`）
- 错误类型: 业务逻辑错误，未按本位币折算
- 状态: 🔴 待修复
- 关联债务: TD-002

## BUG-TK-004: 计费重量比率类型错误

- 发现时间: 2026-08-11
- 根因文件: `models/freight_configuration.py`、`freight_bookings.py`、`freight_quot.py`
- 错误类型: `ir.config_parameter` 返回字符串，参与比较/除法报错
- 状态: 🔴 待修复
- 关联债务: TD-011

完整技术债清单见 `mymodules/tk_freight/docs/technical_debt.md`。
