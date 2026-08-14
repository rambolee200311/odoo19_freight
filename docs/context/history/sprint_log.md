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

## Sprint4-4-2-Conflict-Resolution (2026-08-13)

**目标**: Fee ↔ Statement 一致性收口（契约矛盾清理 + 核心不变量 + 并发保护）。

**成果**:
- B-36/B-52 标记 SUPERSEDED_BY B-54/B-55（历史保留）；B-50/B-53 口径统一
- Sprint4-3 业务流补 unconfirm 路径与释放条件；Sprint4-4 清除 U-40 残留文案
- statement 创建增加 `SELECT FOR UPDATE` 行锁 + 事务内 fee_state 二次校验
- `statement_locked` 标记 DEPRECATED（仅兼容，不参与状态机决策）
- 未新增费用版本体系

**验收**: context_loader 0.1.63 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 22/22 断言（口径扫描/并发锁/业务字段写拦截）+ log clean PASS。

## Sprint4-4-3-Wizard-Refactor (2026-08-13)

**目标**: Create Statement 向导改造（confirmed 费用列表 + 只读货单 + 客户重置 + 勾选生成）。

**成果**:
- wizard 列表仅显示所选客户 `fee_state=confirmed` 应收费用
- `shipment_id` 只读；切换客户重置列表；费用行可勾选/去勾选
- 保留 eligibility_summary 可选费用说明与 Fee State 列
- 未改费用/Statement 状态机与生成事务/并发保护

**验收**: context_loader 0.1.65 基线 PASS；verify.py 全部强制门禁 PASS；button_immediate_upgrade + 7/7 断言 + log clean PASS。

## Sprint4-4-4-Wizard-Refactor (2026-08-14)

**目标**: Create Statement 向导生命周期重构（行绑定、选择态、eligibility 单一引擎、锁后全量校验）。

**成果**:
- 契约起草：service_id 创建即绑定，禁止猜测式恢复（B-61）
- create/onchange 生命周期与 select 保留/重置语义（B-62）；默认全部勾选（U-45 → B-69）
- selectable 强制校验、FOR UPDATE 后全量 eligible 重校验（B-63/B-64）
- customer_id 归属显式校验、eligibility 单一 helper（B-65/B-66）
- snapshot readonly 与 sequence 步进；占用唯一事实来源 fee_state（B-67/B-68）

**验收**: context_loader 0.1.71 基线 PASS；verify.py 18/18 PASS；待编码后补充模块升级与运行时断言。

## Sprint4-4-4-Lessons-Learned (2026-08-14)

**目标**: 将 Sprint4-4-4 多轮返工复盘沉淀为可加载上下文资产。

**成果**:
- 新增 `history/lessons_learned.md` 独立复盘文档
- `governance/test_lessons.yaml` 新增 TL-FREIGHT-006/007/008
- 资产清单与版本基线同步（context 0.1.72）

**验收**: context_loader 0.1.72 基线 PASS；verify.py 18/18 PASS。

## Sprint4-4-4-Contract-V1.1-Review (2026-08-14)

**目标**: 按独立评审意见对 Sprint4-4-4 契约做 V1.1 收口，形式化 wizard 生命周期。

**成果**:
- 生命周期四事件与选择态保留/重置语义
- eligibility 三层模型与三态包含关系
- customer 语义、service 绑定边界、并发锁/锁协议、事务原子性
- 确定性排序、空选择/删除行行为、UI 验收策略

**验收**: context_loader 0.1.73 基线 PASS；verify.py 18/18 PASS。

## Sprint4-4-4-Contract-V2.0 (2026-08-14)

**目标**: 按第二轮独立评审将 Sprint4-4-4 契约重写为“生命周期重构契约”，约束 Agent 不要以打补丁冒充重构。

**成果**:
- before/after 生命周期与四类事件
- eligible/selectable/select 三态语义 + service_id 身份锚点
- rebuild matrix + method responsibility
- Phase 0 只读分析 / Phase 1 人审设计 / Phase 4 Refactor Review 门禁
- 结构验收、禁止实现模式、生命周期专项测试

**验收**: context_loader 0.1.74 基线 PASS；verify.py 18/18 PASS；待编码后执行 Phase 0~4。

## Sprint4-4-4-Wizard-Refactor-Implementation (2026-08-14)

**目标**: 按 V2.0 生命周期契约与 FRS 完成 wizard 重构（Phase 2 编码 + Phase 3 验证）。

**成果**:
- 单一 eligibility helper `_is_service_eligible`
- 删除 name+qty+price 猜测恢复；service_id 创建即绑定
- create/onchange 重建全选；普通 write 保留 select；结构性命令恢复权威集合
- customer invariant / selectable 校验 / 锁后全量 eligibility 重校验
- sequence 10 步进；snapshot 双层只读

**验收**: context_loader 0.1.75 基线 PASS；verify.py 18/18 PASS；生命周期专项测试 7/7 PASS；待 human browser acceptance。

## Sprint4-4-4-Rebuild-Select-Fix (2026-08-14)

**目标**: 修复网页端重建行命令导致 select 被重置为全选的问题。

**成果**:
- `write` 守卫区分重建命令与删除/清空命令
- 重建命令按 service_id 保留客户端 select；删除/清空恢复权威集合

**验收**: context_loader 0.1.76 基线 PASS；verify.py 18/18 PASS；odoo shell 实测 2/2 PASS；待 human browser acceptance。

## Sprint4-4-4-Rebuild-Recursion-Fix (2026-08-14)

**目标**: 修复 `_rebuild_lines` 递归触发 write 守卫导致 select 被重置的根因。

**成果**:
- 重建赋值自带 `wizard_rebuild` 上下文
- write 守卫先处理重建命令，再处理删除/清空

**验收**: context_loader 0.1.77 基线 PASS；verify.py 18/18 PASS；odoo shell 实测 4/4 PASS；待 human browser acceptance。

## Sprint4-5-Generate-Draft-Invoice (2026-08-14)

**目标**: 起草并经两轮评审修订“Confirmed Statement → 生成草稿发票”契约；开票申请不开发（B-42 保持）。

**成果**:
- Intent 契约登记 B-70/B-71/B-72（状态来源、行来源、幂等）
- BR-70 ~ BR-72 同步 business_rules.yaml
- 现状 action_generate_draft_invoice 已实现基础流程，进入编码前按契约硬化
- 按独立评审（决策70）补 idempotency_contract / tax_mapping_contract /
  invoice_header_contract / currency_contract / line_mapping /
  transaction_contract / return_contract，验收拆服务端 + 浏览器
- 按第二轮评审（决策71）补并发幂等（行锁串行）、tax_code 优先税映射并取消
  自动含税回退、draft_invoice⇒invoice_ids 非空不变量、按钮状态矩阵；B-73/B-74
- 实施完成（决策72）：freight_statement.py 最小硬化
  （FOR UPDATE 行锁、不变量拦截、税映射失败即停、单/多发票返回动作）
  - 服务端断言 7 组全 PASS（draft/voided 拦截、单币种、幂等、不变量、
    多币种两单、qty=0 拦截），全部事务回滚无数据残留
  - 待业务负责人浏览器验收（多币种必测）

**验收**: context_loader 0.1.86 基线 PASS；verify.py 18/18 PASS；服务端断言 7/7 PASS；待 human browser acceptance。
