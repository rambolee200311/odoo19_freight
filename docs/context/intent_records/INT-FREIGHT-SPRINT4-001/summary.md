# Intent 执行记录：INT-FREIGHT-SPRINT4-001

## 结果

- 新增 `freight.statement / freight.statement.line`，实现 `draft → voided / confirmed → draft_invoice` 状态机、版本链与不可变快照。
- 新增结算单生成 wizard（列表勾选 `freight.service` 费用行，B-39）；同一业务键仅一个非 voided 当前活动结算单。
- 客户拒绝作废结算单并释放费用（B-36/B-40），费用修改回 `freight.shipment / freight.service` 后重新生成新版本。
- 仅 confirmed 生成草稿应收发票（B-41），按币种分组且幂等，重复动作返回已有草稿发票；发票 header 关联 `freight_statement_id`（B-38）。
- `product.template` 新增 `tax_code / tax_name`（B-26）；结算单行记录税率/税额/含税/不含税，手工调整以 `tax_amount` 为权威。
- 旧 `action_create_invoice` 从 UI 隐藏并拦截直调（B-30）；两个遗留 server action 取消列表绑定；`action_create_vendor_bill` 保留兼容。
- 未开发开票申请（B-42）、Vendor Bill 生成、dispute/partially_invoiced/invoiced/adjusted、分批开票、行级追溯、confirmed 后原地改费用。

## 状态

PASS（context_loader 基线 + verify.py 全部强制门禁 + XML-RPC 模块升级 + odoo shell 状态流转断言）
