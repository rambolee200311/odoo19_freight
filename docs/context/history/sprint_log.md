# Sprint 迭代日志

## Sprint0-Context-Baseline (2026-08-11)

**目标**: 让项目处于可控状态，建立认知资产与门禁引擎。

**成果**:
- 完成 tk_freight 现状梳理（模型、视图、报表、门户、权限、财务联动）
- 确认业务口径 9 条
- 登记技术债 TD-001 ~ TD-025
- 建立 docs/context 认知资产（architecture/business/history/constraints/cognition/governance/intent/profiles/validation）
- 建立 execution/scripts 门禁引擎（context_loader/verify/commit_guard/odoo_check/test_runner）

**验收**: 待 context_loader / verify 执行确认。

**下一步**: 按技术债优先级修复 P0 财务问题（TD-001/002/003/004/005/008/009）。

## Sprint1-Menu-Consolidation-Invoicing (2026-08-11)

**目标**: 整理 tk_freight 菜单，将 Customers/Vendors/Fleets/Services 收拢到 Archive，并新增 Invoicing 应收/应付发票入口。

**成果**:
- Archive 一级菜单建立，Customers/Vendors/Fleets/Services 及其子菜单收拢至 Archive
- Invoicing 一级菜单 + 应收发票/应付发票二级菜单
- 应收/应付发票通过 menu-scoped act_window wrapper 限定 `freight_operation_id` 有值单据
- zh_CN.po 新增 档案/发票管理/应收发票/应付发票 菜单文案

**验收**: verify.py 17/18 PASS（c15 受工作区存量越界变更影响）；XML-RPC 模块升级与菜单断言 PASS。

## Sprint2-Port-State-Optional (2026-08-11)

**目标**: 取消 freight.port 表单 State 字段必填。

**成果**:
- 确认模型层 `state_id` 无 `required`，必填约束仅存在于 `port_form_view`
- 移除视图层 `state_id required="1"`，State 可留空
- Name/Code/Street/City/Country 必填约束保持不变

**验收**: verify.py 17/18 PASS（c15 仅 flag Sprint2 Intent 契约文件本身）；XML-RPC 模块升级与视图 arch 断言 PASS。

## Sprint4-Statement-Invoice-Flow (2026-08-12)

**目标**: 货运单费用 → 结算单草稿/客户核对/作废 → 新结算单版本 → 客户接受 → 草稿应收发票。

**成果**:
- 新增 `freight.statement / freight.statement.line` 状态机（draft → voided / confirmed → draft_invoice）与版本链
- 新增结算单生成 wizard（列表勾选费用行，B-39），同一业务键仅一个非 voided 当前活动结算单
- 仅 confirmed 生成草稿应收发票，幂等且 header 级关联 `freight_statement_id`（B-38/B-41）
- `product.template` 新增税目编码/税目名称（B-26），结算单行记录税率/税额/含税/不含税，`tax_amount` 权威
- 旧 `action_create_invoice` 隐藏并拦截直调（B-30），遗留 server action 取消列表绑定，Vendor Bill 保留兼容
- 未开发开票申请（B-42）、Vendor Bill 生成、dispute/adjusted、分批开票、行级追溯

**验收**: context_loader PASS；verify.py 全部强制门禁 PASS；XML-RPC 模块升级 + 结算单状态流转与发票幂等断言 PASS。

## Sprint4-1-Shipment-Form-Pages (2026-08-12)

**目标**: `freight.shipment` 表单新增对账单与发票两个只读 Page，建立 Shipment 财务观察窗口。

**成果**:
- Statements Page：展示该货运单全部结算单版本（含 voided），无操作按钮，仅行跳转打开
- Invoices Page：展示 `freight_operation_id` 关联的 `account.move`（客户发票/供应商账单按类型区分），无操作按钮
- `freight.shipment.invoice_ids` 只读 One2many（inverse `freight_operation_id`），仅用于展示
- 页面位于 Accountancy 之后，先对账单后发票（B-43/B-44/B-45）
- 未改结算单状态机、开票/追溯逻辑、Vendor Bill 创建、菜单、权限、报表、`__manifest__.py`

**验收**: context_loader 0.1.46 基线 PASS；verify.py 全部强制门禁 PASS；常驻升级 + 27/27 视图断言 + log clean PASS。

## Sprint4-2-Statement-Generation (2026-08-12)

**目标**: 固化 Shipment → 费用行 → Generate Statement → Statement Draft，明确客户结算单费用范围。

**成果**:
- 契约写入费用范围 B-46：仅 shipper/consignee 客户应收费用，vendor cost 排除
- 明确 Vendor Bill 为供应商自有账单，我方不创建，不作为技术债/流程对象
- 生成入口沿用现有 wizard 模式（B-47/B-39）
- 运行时验收：可选费用仅 shipper/consignee、vendor 排除、draft 生成、金额正确、重复/空选择拦截
- 本 Sprint 无业务代码变更（沿用 Sprint4 已实现 wizard）

**验收**: context_loader 0.1.48 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 10/10 断言 + log clean PASS。

## Sprint4-3-Statement-Void-Revision (2026-08-12)

**目标**: 客户拒绝 → 作废 → 修改费用 → 重新生成新结算单（不可变版本重建）。

**成果**:
- 新增 `voided_reason` 可选字段与 `action_void(reason)` 审计（voided_uid / voided_date / voided_reason）
- 作废为 voided 终态：draft 可作废，voided/confirmed/draft_invoice 禁止作废；header 与 statement.line 不可变
- 作废不回写 freight.service；重新生成时从当前费用创建全新 statement.line 快照
- 版本链沿用 `statement_id（根）/ previous_statement_id / version_no`，未做 schema rename
- B-50：旧 Draft 作废永久留存，新结算单生成新 version_no，不允许原地刷新
- 未实现客户接受确认（Sprint4-4）、开票、Vendor Bill

**验收**: context_loader 0.1.52 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 12/12 断言（快照隔离/反向污染/重复生成拦截）+ log clean PASS。

## Sprint4-4-Statement-Confirm (2026-08-13)

**目标**: 客户接受 → Statement Confirmed（业务锁点）+ 费用层部分锁定。

**成果**:
- `freight.service` 新增 `statement_locked`：confirmed / draft_invoice 结算单关联费用锁定
- `FreightService.write / unlink` 模型层拦截已锁定费用修改/删除（B-52）
- Draft 关联费用可编辑；Voided 关联费用解除锁定可再次用于新结算单
- `freight.service` 表单对锁定费用只读；Statement 表单展示 confirmed_uid / confirmed_date
- 未新增 security group（B-28）；未实现草稿发票生成（Sprint4-5）、Vendor Bill

**验收**: context_loader 0.1.54 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 14/14 断言 + log clean PASS。

## Sprint4-4-1-Fee-State-Management (2026-08-13)

**目标**: 费用显式状态管理（draft/confirmed/used/canceled）+ 与 Statement 生命周期严格联动。

**成果**:
- `freight.service.fee_state` 四态与 Confirm/Unconfirm/Cancel/Copy as Draft 动作
- 写锁以 fee_state 为准；confirmed/used/canceled 不可编辑删除
- wizard 仅 `fee_state == confirmed` 费用可选；Statement 创建→used（同事务）；作废→confirmed（无其他非 voided 引用）
- 存量费用初始化：非 voided 引用或 invoiced → used，其余 draft（B-56/B-58）
- 费用表单新增状态栏与操作按钮

**验收**: context_loader 0.1.59 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 25/25 断言 + log clean PASS。
