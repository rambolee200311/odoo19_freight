# Intent 执行记录：INT-FREIGHT-SPRINT4-3-001

## 结果

- 新增 `freight.statement.voided_reason` 可选字段，`action_void(reason)` 记录 voided_uid / voided_date / voided_reason。
- 作废为 voided 终态：draft 可作废；voided / confirmed / draft_invoice 禁止作废；header 与 statement.line 不可变。
- 作废不回写或重置 freight.service 费用事实；重新生成时由现有费用选择规则重新计算可纳入费用，并创建全新 statement.line 快照。
- 版本链沿用 `statement_id（根）/ previous_statement_id / version_no`，未做字段重命名。
- B-50：旧 Draft 作废并永久留存，新结算单生成新 version_no，不允许原地刷新/重建同版本。
- 未实现客户接受确认（Sprint4-4）、开票、Vendor Bill、schema rename。

## 状态

PASS（context_loader 0.1.52 基线 + verify 全门禁 + button_immediate_upgrade + 12/12 断言 + log clean）
