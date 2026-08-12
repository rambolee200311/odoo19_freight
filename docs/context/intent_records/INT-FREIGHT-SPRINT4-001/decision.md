# 决策记录

- 决策36：Sprint4 实施契约执行完成（2026-08-12）。
  - 新增 `freight.statement / freight.statement.line`，状态机 `draft → voided / confirmed → draft_invoice`。
  - 结算单生成 wizard 勾选 `freight.service` 费用行（B-39）；同一业务键仅一个非 voided 当前活动结算单。
  - 客户拒绝 = 作废，费用修改回 `freight.shipment / freight.service`，重新生成新版本（`statement_id + version_no + previous_statement_id`）。
  - 仅 confirmed 生成草稿应收发票（B-41），幂等且 header 级关联 `freight_statement_id`（B-38）。
  - `product.template` 新增 `tax_code / tax_name`（B-26），`tax_amount` 权威落账。
  - 旧 `action_create_invoice` 隐藏并拦截直调（B-30），server action 取消列表绑定，Vendor Bill 保留兼容。
  - 未开发开票申请（B-42）、Vendor Bill 生成、dispute/adjusted、分批开票、行级追溯。
