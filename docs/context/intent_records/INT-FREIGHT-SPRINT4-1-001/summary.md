# Intent 执行记录：INT-FREIGHT-SPRINT4-1-001

## 结果

- `freight.shipment` 表单 notebook 新增两个只读 Page：
  - Statements：展示该货运单全部结算单版本（draft/voided/confirmed/draft_invoice），含编号、客户、状态、版本、结算日期、合计金额、发票数。
  - Invoices：展示 `freight_operation_id` 关联的 `account.move`（客户发票/供应商账单），含发票号、类型、客户、日期、状态、金额。
- `freight.shipment.invoice_ids` 新增只读 One2many（inverse `freight_operation_id`），仅用于页面展示。
- 两个 Page 均无操作按钮，仅行跳转打开明细；位置在 Accountancy 页之后，先对账单后发票（B-43/B-44/B-45）。
- 未修改结算单状态机、开票/幂等/追溯逻辑、Vendor Bill 创建、菜单、权限、报表、`__manifest__.py`。

## 状态

PASS（context_loader 0.1.46 基线 + verify 全门禁 + 常驻升级 + 27/27 视图断言 + log clean）
