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
