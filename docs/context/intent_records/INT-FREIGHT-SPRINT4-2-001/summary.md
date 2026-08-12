# Intent 执行记录：INT-FREIGHT-SPRINT4-2-001

## 结果

- 契约固化结算单生成流程：Shipment → 费用行 → Generate Statement → wizard 勾选 → Statement Draft。
- 费用范围 B-46：仅 customer-side revenue charges（shipper/consignee），vendor cost 排除；Vendor Bill 为供应商自有账单，我方不创建。
- 生成入口沿用现有 wizard 模式（B-47），无新建入口。
- 运行时验收：wizard 可选费用仅 shipper/consignee、vendor 排除；Shipment 表单 Generate Statement 入口可用；可生成 STM 编号 draft；同一业务键重复生成被阻止；空选择被阻止；结算单行无 vendor 行；金额等于所选费用行合计。
- 本 Sprint 无业务代码变更（Sprint4 已实现对应 wizard），完成契约确认与验收记录。

## 状态

PASS（context_loader 0.1.48 基线 + verify 全门禁 + button_immediate_upgrade + 10/10 断言 + log clean）
