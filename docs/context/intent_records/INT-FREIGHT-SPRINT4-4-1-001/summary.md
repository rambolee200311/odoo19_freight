# Intent 执行记录：INT-FREIGHT-SPRINT4-4-1-001

## 结果

- `freight.service.fee_state` 四态：draft / confirmed / used / canceled。
- 动作：Confirm（draft→confirmed）、Unconfirm（confirmed→draft，无活动 statement）、Cancel（draft→canceled）、Copy as Draft（canceled→新 draft）。
- 写锁：confirmed / used / canceled 不可编辑删除；draft 被 statement 引用时不可删除。
- wizard 仅 `fee_state == confirmed` 费用可选；Statement 创建后费用同事务写回 used（B-55）。
- Statement 作废仅当费用无其他非 voided Statement 引用时释放回 confirmed。
- 存量费用初始化：非 voided 引用或 invoiced=True → used，其余 draft（B-56/B-58）。
- 费用表单新增 fee_state 状态栏与 Confirm/Unconfirm/Cancel/Copy as Draft 按钮。

## 状态

PASS（context_loader 0.1.59 基线 + verify 全门禁 + button_immediate_upgrade + 25/25 断言 + log clean）
