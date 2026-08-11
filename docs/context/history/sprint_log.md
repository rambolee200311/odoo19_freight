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
