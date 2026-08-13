# Intent 执行记录：INT-FREIGHT-SPRINT4-4-001

## 结果

- `freight.service` 新增 `statement_line_ids` / `statement_locked`：confirmed / draft_invoice 结算单关联费用标记锁定。
- `FreightService.write / unlink` 模型层拦截：已锁定费用不可修改、不可删除（B-52）。
- Draft 结算单关联费用保持可编辑；Voided 结算单关联费用解除锁定，可再次用于新结算单（对齐 Sprint4-3）。
- `freight.service` 表单对已锁定费用字段只读（`statement_locked`）。
- Statement 表单展示 confirmed_uid / confirmed_date。
- 未新增 security group；未实现草稿发票生成（Sprint4-5）、Vendor Bill。

## 状态

PASS（context_loader 0.1.54 基线 + verify 全门禁 + button_immediate_upgrade + 14/14 断言 + log clean）
