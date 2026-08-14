# Decision Note — 决策笔记

## Sprint0: 上下文基线建设

**契约**: INT-FREIGHT-SPRINT0-001
**时间**: 2026-08-11

### 决策1：项目认知资产体系沿用 odoo18_tms 框架

**背景**: `docs/context` 原为 odoo18_tms 残留资产，与本项目不符。

**决策**: 整体替换为 `odoo19_freight / tk_freight` 版本，保留参考项目的目录结构与引擎命名（`execution/scripts`），内容全部按本项目重写。

### 决策2：业务口径固化

**决策**: 收入/成本/币种/税费/开票/收付款/利润/状态/兼容 9 条口径登记为业务铁律，写入 `business/freight_rule.md`，后续改动必须先更新决策笔记。

### 决策3：财务联动采用 Odoo account 标准模型

**决策**: 发票/账单使用 `account.move`，收付款使用 `account.payment` 登记，不做复杂核销；利润公式为“含税收入 − 含税成本 − 税费净额”。

### 决策4：技术债集中登记

**决策**: 所有已知问题统一登记到 `mymodules/tk_freight/docs/technical_debt.md`（TD-001 ~ TD-025），`docs/context/business/business_debt_register.md` 只保留与业务口径强相关的摘要。

### 决策5：兼容保留策略

**决策**: 遗留字段、`shipment.invoice` 向导、deprecated 方法保留兼容不删除；`commit_guard.py` 不自动 `git add .`、不默认 push。

### 决策6：汇率与利润微调口径

**决策**: 默认“收入/成本按单据日汇率、收付款按登记日汇率”折算；利润按“含税收入 − 含税成本 − 税费净额”。若业务后续调整，先更新本决策再改代码。

### 决策7：模块升级铁律

**决策**: 模块升级一律用常驻方式启动 Odoo，通过 XML-RPC 调用 `button_immediate_upgrade` 升级；升级失败必须检查 `debug_logs/odoo_190.log`；禁止仅用 `-u --stop-after-init` 作为最终验证。同步改造 `odoo_check.py` 与 `odo-validate-loop` 技能。

### 决策8：事实与推测分类基线

**决策**: 建立 `business/knowledge_classification.md`，对业务知识统一标注 CODE_FACT / BUSINESS_FACT / DECISION / CONSTRAINT / TECHNICAL_DEBT / UNKNOWN / ASSUMPTION；决策6 中的汇率与利润默认口径标记为 ASSUMPTION / NEEDS_CONFIRMATION，不再作为已确认事实表述。

### 决策9：防偏离 Guard 补齐

**决策**: 新增五项防偏离机制：intent scope 越界检查（c15）、机器可读业务规则表 `business_rules.yaml` 与口径对比（c13/c16）、`business/*` 变更强制同步 decision_note（c17）、UNKNOWN 未确认不得进入代码开发（c18）、每个 Sprint 结束执行独立审计对账（治理规则）。这些机制只约束开发流程，不改变已确认业务口径。

### 决策10：Sprint1 Intent 起草

**决策**: 起草 `INT-FREIGHT-SPRINT1-001`（菜单整理 + Invoicing 应收/应付发票菜单）。登记开放项 U-10（档案收拢范围）与 U-11（发票菜单范围），未确认前不得进入代码开发；本迭代仅限视图/菜单层。

### 决策11：Sprint1 菜单范围确认

**决策**: U-10 确认：Customers/Vendors/Fleets/Services 收拢到 Archive 菜单，Packages 保留独立入口，其他菜单不动。U-11 确认：应收/应付发票菜单仅显示 `freight_operation_id` 有值的货代相关发票。登记为 B-13 / B-14 / BR-13 / BR-14，契约进入可开发状态。

### 决策12：Sprint1 契约 Harness 化修订

**决策**: 按独立评审将 `INT-FREIGHT-SPRINT1-001` 重构为可执行结构：`scope_paths` 收窄为 `scope.allowed_files`，新增 `forbidden_paths` / `forbidden_changes` / `invariants` / `unknown_policy` / `context_policy`，验收与验证分离，停止条件增加 `scope_violation` / `new_unknown`。development Profile 补充 `required` 资产语义，verify / context_loader 兼容新旧 Intent 结构。业务范围与 B-13 / B-14 / BR-13 / BR-14 不变。

### 决策13：Sprint1 契约第二轮 Harness 化修订

**决策**: 按第二轮评审消除契约歧义：新增 `change_boundary` / `menu_relocation` / `translation_constraints` / `menu_assertions` / `success_definition`；明确 account action 为“引用”而非修改；明确 Archive / Invoicing parent 为 `tk_freight.freight_root`；`affected_assets` 与 `execution_artifacts` 分离；`stop_condition` 拆分 `success / hard_stop`；confirmed_decisions 改用 B-13 / B-14 并保留 U-10 / U-11 追溯。业务范围不变。

### 决策14：Sprint1 发票菜单 domain 技术实现

**决策**: Odoo 19 `menuitem` 不支持 `domain` 属性。为满足应收/应付发票菜单 domain 限定，在 `views/menus.xml` 新增两个 menu-scoped `ir.actions.act_window` wrapper：`action_freight_invoice_receivable` / `action_freight_invoice_payable`，复用 account 标准视图与 move_type domain，追加 `freight_operation_id != False` 过滤。不新增模型/业务逻辑，不修改 account action。

### 决策15：Sprint2 Intent 起草

**决策**: 起草 `INT-FREIGHT-SPRINT2-001`：取消 `freight.port` 表单 State 字段必填。检查确认模型层 `state_id` 无 `required`，必填仅来自 `port_form_view` 视图层 `required="1"`；拟定仅移除视图层约束，不修改模型定义。待业务负责人确认后进入编码。

### 决策16：Sprint2 执行确认

**决策**: 业务负责人确认 Sprint2 契约后下达开发指令。执行完成：移除 `port_form_view` 中 `state_id` 的 `required="1"`，模型层与其他必填字段保持不变。

### 决策17：Sprint3 Intent 起草

**决策**: 起草 `INT-FREIGHT-SPRINT3-001`：货运单费用录入 → 对账单草稿/异议/确认 → 发票生成 → 开票后调整。当前代码直接从 `freight.service` 生成 `account.move`，无对账单状态机；本 Intent 新增 `freight.statement` / `freight.statement.line` 状态机并重构开票入口。待业务负责人确认后进入编码。

### 决策18：Sprint3 契约开放项确认

**决策**: 业务负责人确认 Sprint3 契约开放项：对账单按“货运单 + 客户”一单一账（B-15）、修订保留完整快照（B-16）、已确认对账单允许分批/按费用行开票（B-17）、开票后调整仅允许红冲/贷项通知单（B-18）、费用无税率默认不含税且对账单记录税率/税额/含税/不含税并可手工调整（B-19）。契约开放项已清空，待下达开发指令后进入编码。

### 决策19：Sprint3 契约按 L3 评审修订

**决策**: 按独立评审重构 `INT-FREIGHT-SPRINT3-001`：状态机补充 `partially_invoiced` 并给出可执行状态转移矩阵；修订明确为不可变版本链（`revision_of` / `version_no`）；唯一业务键明确为 `freight_operation_id + customer_id`；补充 `tax_policy`（手工调整以 `tax_amount` 为权威）、`billing_traceability`、`legacy_invoice_entry`、`permission_policy`、并发与币种规则；删除 `menu_assertions`；收窄 `unchanged_business_behavior` 与文件语义范围；明确不新建 `data/` XML。登记开放项 U-17（客户/供应商对账单范围）、U-18（多币种 Statement）、U-19（开票后 adjusted 语义），确认前不得进入编码。

### 决策20：Sprint3 契约开放项确认

**决策**: 业务负责人确认 Sprint3 契约开放项：对账单仅限客户（AR），供应商账单沿用既有 `action_create_vendor_bill`（U-17 → B-20）；对账单明细行允许本币/原币，按币种分别汇总本币与原币金额，禁止跨币种合并汇总（U-18 → B-21）；开票后全部调整完成才进入 `adjusted`，`adjusted` 为终态（U-19 → B-22）。契约 `unresolved_unknowns` 已清空，可进入编码执行。

### 决策21：Sprint3 实施契约暂存为 Sprint4

**决策**: 因 Sprint3 调整为“财务流程现状分析”阶段（禁止修改代码），原 `INT-FREIGHT-SPRINT3-001`（费用对账与发票生成实施契约）整体暂存为 Sprint4：文件改为 `docs/context/intent/intent_sprint4_statement_invoice_flow.yaml`，契约 ID 改为 `INT-FREIGHT-SPRINT4-001`，执行记录目录改为 `docs/context/intent_records/INT-FREIGHT-SPRINT4-001/`。业务决策 B-15 ~ B-22 及 BR-15 ~ BR-22 引用保持不变。新的 Sprint3 仅输出现状分析报告，不修改 Context。

### 决策22：Sprint3 分析阶段意图契约登记

**决策**: 登记 `INT-FREIGHT-SPRINT3-002`（Sprint3-Finance-Flow-Analysis）作为现状分析阶段意图契约；交付物为 `docs/reports/sprint3_finance_flow_analysis.md`，包含现状流程、代码调用链、认知资产冲突、Gap Matrix、旧开票依赖、对账单/版本/调整/发票追溯设计建议、风险清单与 UNKNOWN 清单。分析阶段禁止修改业务代码，UNKNOWN（含 U-23 ~ U-29 新增项）待业务负责人确认后再进入 Sprint4 实施。

### 决策23：Sprint3-002 分析契约按评审修订

**决策**: 按评审修订 `INT-FREIGHT-SPRINT3-002`：`unchanged_business_behavior` 不再引用 Sprint4 候选规则；新增 `analysis_constraints` / `design_advisory_policy` / `analysis_report.required_sections`；`unknown_policy` 改为允许发现并记录 UNKNOWN（`record_and_continue`），禁止自行解决或转为 CONFIRMED，`hard_stop` 移除 `new_unknown`；`context_policy` 增加 `update_policy` 限制；`change_boundary` 增加 `security` / `database` 空边界并强化 `forbidden_changes`；报告重构为 13 个必需章节，设计建议统一标注 `PROPOSAL / INFERENCE / UNKNOWN`，不写入业务铁律。

### 决策24：Sprint3-002 分析执行完成

**决策**: Sprint3-002 逆向分析执行完成：交付 `docs/reports/sprint3_finance_flow_analysis.md`（14 个必需章节），完成现状流程、代码调用链、`account.move` 创建链、开票入口、认知资产规则与冲突、Gap Matrix、旧开票依赖、设计候选方案、风险与 UNKNOWN 清单、分 Sprint 方案；未修改业务代码/模型/视图/权限/数据库。执行记录归档至 `docs/context/intent_records/INT-FREIGHT-SPRINT3-002/`，UNKNOWN 待业务负责人确认后进入 Sprint4。

### 决策25：Sprint3-002 分析报告按评审修订

**决策**: 按评审修订 `docs/reports/sprint3_finance_flow_analysis.md`：候选规则 B-15 ~ B-22 不再作为设计前提，推荐改为条件式表述；U-01 与 B-17 明确为“待确认重叠”而非冲突；旧入口策略与 U-24 去矛盾，改为“当前判断 + 候选方案 + UNKNOWN”；分 Sprint 方案标记 `PROPOSAL / NON-BINDING`；术语统一为 `freight.service`（不得另建 `shipment.fee`）；明确版本快照 ≠ 审计日志；追溯链扩展为 Shipment → Statement → Statement Line → Invoice → Invoice Line，关联基数登记 U-32；新增 CODE_FACT 证据等级章节，报告扩展为 14 章；U-23（标准 Accounting 创建入口）提升为 LEVEL4 / BLOCKING UNKNOWN。

### 决策26：Sprint3-002 分析报告补充运行时核验

**决策**: 通过 odoo shell 对 `freight.shipment(1)` / `freight.service(1)` / `account.move(1)` 及关联记录进行运行时核验，结果写入分析报告 FACT-B：费用行-发票双向追溯字段实际为空（TD-003 确认）；`total_invoiced=32500` 为公司本位币 signed 口径（USD 4500 × 7 + CNY 1000），并非失真；`total_bills=-970` 为供应商账单按原币登记的 signed 金额，供应商账单由供应商开具原件、业务侧登记，不视为我方技术债；`account.move / account.move.line` 上 `statement_id / statement_line_id` 为 Odoo 标准银行流水字段，Sprint4 对账单字段必须避免命名冲突；`freight.statement` 系列模型与 `shipment.fee` 均不存在；`freight.multiple.invoice` 为空表。

### 决策27：移除 U8C 历史残留

**决策**: 本项目为纯 Odoo 项目，代码与决策记录中不存在任何 U8C 集成。U-07（U8C/外部财务接口）为历史基线残留，已从 `knowledge_classification.md`、`business_rules.yaml`、`export_freight_coverage.md`、`business_debt_register.md`、`forbidden_change.yaml`、`technical_debt.md` 与 Sprint3-002 分析报告中移除；后续未知项编号不再保留 U-07 槽位。

### 决策28：U-02 汇率口径确认

**决策**: 业务负责人确认对账单折算口径（U-02 → B-23 / BR-23）：对账单默认取系统当前汇率，允许用户录入结算汇率覆盖；录入结算汇率后按结算汇率计算本币金额。现系统曾用 2026-08-10 汇率折算 2026-03-19 发票，Sprint4 需按 B-23 口径实现取数与覆盖逻辑。知识资产 `knowledge_classification.md` / `business_rules.yaml` 已同步，Sprint3-002 报告第 13 节 UNKNOWN 清单移除 U-02。

### 决策29：U-04 税目字段范围澄清

**决策**: 运行时核验确认当前 `account.tax` / `product.product` / `product.template` 均无“税目编码/税目名称”字段，产品档案只能通过标准字段 `taxes_id` / `supplier_taxes_id` 维护销售/采购税率（现有税仅为 13%/9%/6%）。若业务需要税目编码/税目名称，必须在 Sprint4 新增字段（产品模板或 `freight.service` 扩展），并与手工调整税额的落账机制一并设计；U-04 保持 UNKNOWN，范围收窄为“税目字段设计 + 手工调整税额落账机制”。

### 决策30：U-01 费用行开票粒度确认

**决策**: 业务负责人确认费用行整行进一张发票，禁止行内分批/部分开票（U-01 → B-24 / BR-24）；分批开票仅按费用行粒度进行。

### 决策31：U-03 税费净额确认

**决策**: 业务负责人确认利润公式中“税费”净额 = 销项税 − 进项税（U-03 → B-25 / BR-25），A-3 由 ASSUMPTION 转为 CONFIRMED。

### 决策32：Sprint3-002 剩余开放项确认

**决策**: 业务负责人确认 Sprint3-002 剩余开放项（U-04 ~ U-32 → B-26 ~ B-38 / BR-26 ~ BR-38）：

- U-04 → B-26：服务/产品档案新增税目编码、税目名称；手工调整税额按 tax_amount 权威落账。
- U-05 → B-27：PDF 对账单以 `docs/reports/应收对账单原始单据.md` 为需求输入。
- U-06 → B-28：当前不建设角色权限与 portal 收敛，保持现状。
- U-23 → B-29：标准 Accounting 创建入口不纳入收敛，Sprint4 只收敛 tk_freight 业务入口。
- U-24 → B-30：旧开票入口隐藏，保留方法与兼容调用能力。
- U-25 → B-31：Statement 编号规则 STM/年月/4位流水码。
- U-26 → B-32：历史数据不迁移。
- U-27 → B-33：自动生成费用行通过对账单状态管理，客户确认后生成发票。
- U-28 → B-34：不需要调整申请/审批角色流程。
- U-29 → B-35：供应商成本行排除在客户对账单外。
- U-30 → B-36：客户 reject 的对账单作废，释放费用为可修改状态。
- U-31 → B-37：confirmed 后强制版本化。
- U-32 → B-38：不建立 Statement Line ↔ Invoice Line 行级关联，仅 header 级关联。

至此 Sprint3-002 全部开放项已确认，Sprint4 实施契约按 B-23 ~ B-38 修订。

### 决策33：Sprint3-002 目标工作流与结算单向导确认

**决策**: 业务负责人确认目标工作流：录入费用 → 向导列表勾选费用行生成结算单 → 客户核对 → 客户拒绝则作废结算单并释放费用为可修改 → 修改费用后重新生成新结算单 → 客户接受 →（开票申请，当前暂不设置开发任务）→ 生成草稿发票。生成结算单使用 wizard 勾选费用行，登记为 B-39 / BR-39；开票申请环节不纳入 Sprint4 开发任务。

### 决策34：Sprint4 契约按评审重写

**决策**: 按评审重写 `INT-FREIGHT-SPRINT4-001`：状态机改为 `draft → voided / confirmed → draft_invoice`，删除 `dispute / partially_invoiced / invoiced / adjusted`；明确客户拒绝 = 当前结算单作废、费用修改回到 `freight.shipment / freight.service`、重新生成新结算单（`statement_id + version_no + previous_statement_id`）；仅 confirmed 结算单生成草稿应收发票；开票申请为预留业务节点（B-42），本 Sprint 不开发；Vendor Bill 降级为背景事项（TD-001 标记延期）；登记 B-40 / BR-40（费用修改回费用层）、B-41 / BR-41（草稿发票不代表过账）、B-42 / BR-42（开票申请不开发）。

### 决策35：Sprint4 契约按第二轮评审修订

**决策**: 按第二轮评审修订 `INT-FREIGHT-SPRINT4-001`：draft 明确为 `editable: false / editable_scope: metadata_only`（货运单费用可继续修改）；confirmed 增加 `allowed_actions: generate_draft_invoice`，状态与动作分离；`draft_invoice` 明确 `meaning` 与 `invoice_state: account.move.state = draft`；结算单唯一性改为“同一业务键仅一个非 voided 当前活动结算单”，并补幂等规则；新增 `wizard_constraints`、`statement_line_eligibility`、`tax_master_scope`（product.template tax_code/tax_name）、`invoice_idempotency`、`audit_events`、`non_inference_rules`、`file_scope_constraints`；`action_create_invoice` 从隐藏升级为“直接调用被拦截并提示走 Statement 流程”；来源追溯明确为 header 级。

### 决策36：Sprint4 实施契约执行完成

**决策**: 按 `INT-FREIGHT-SPRINT4-001` 完成实施并验证（2026-08-12）：

- 新增 `freight.statement / freight.statement.line`，状态机 `draft → voided / confirmed → draft_invoice`，draft 费用快照不可直接编辑，仅允许税额/结算汇率元数据调整（B-40 口径）。
- 生成结算单使用 wizard 勾选 `freight.service` 费用行（B-39）；同一 `freight_operation_id + customer_id` 仅一个非 voided 当前活动结算单，重复生成被阻止。
- 客户拒绝 = 作废（voided），旧快照不可变；费用修改回 `freight.shipment / freight.service` 后重新生成新版本（`statement_id + version_no + previous_statement_id`）。
- 仅 confirmed 结算单可生成草稿应收发票（account.move draft，B-41）；按币种生成且幂等，重复动作返回已有草稿发票；发票 header 级关联 `freight_statement_id`（B-38），不建立行级关联。
- `product.template` 新增 `tax_code / tax_name`（B-26）；结算单行记录税率/税额/含税/不含税，手工调整后 `tax_amount` 为权威字段，发票行按结算单合计金额落账。
- 旧 `action_create_invoice` 从业务 UI 隐藏，直接调用被拦截并提示走 Statement 流程（B-30）；两个遗留 server action 取消列表绑定；`action_create_vendor_bill` 保留兼容（B-35/TD-001 延期）。
- 未开发开票申请（B-42）、Vendor Bill 生成、dispute/partially_invoiced/invoiced/adjusted、分批开票、行级追溯、confirmed 后原地改费用。
- 验证：context_loader PASS；verify.py 全部强制门禁 PASS（c15 在 Sprint3-002 存量归档提交后通过）；XML-RPC 常驻升级 + odoo shell 状态流转断言 PASS。

### 决策37：Sprint4-1 契约起草（货运单表单新增对账单/发票 Page）

**决策**: 起草 `INT-FREIGHT-SPRINT4-1-001`（Sprint4-1-Shipment-Form-Pages）：在 `freight.shipment` 表单 notebook 内新增两个只读展示 Page：对账单页展示该货运单全部结算单版本（含作废），发票页展示该货运单关联的应收/应付发票；页面仅展示与行跳转，不写业务数据。

- 范围：`freight_shipment.py` 仅新增 `invoice_ids` One2many（inverse `freight_operation_id`）；`freight_shipment_view.xml` 仅新增两个 Page；i18n 与 manifest 版本递增。
- 禁止：修改结算单状态机、开票/幂等/追溯逻辑、菜单、权限、报表、Controller、前端静态资源；禁止页面内直接建删对账单/发票。
- 开放项：U-33（页面位置顺序，默认 Accountancy 后先对账单后发票）、U-34（对账单页是否放操作按钮，评审推荐不放）、U-35（发票页是否拆分应收/应付，默认合并按类型列区分）。
- 未确认前禁止进入编码（verify c18 / unknown_policy.coding_gate）。

### 决策38：门禁引擎支持 sprint 子编号契约选择

**决策**: 升级 `execution/scripts/context_loader.py` 与 `execution/scripts/verify.py` 的契约选择逻辑：`sprint(\d+)` 解析扩展为支持 `sprint4_1` / `sprint4-1` / `sprint4.1` 子编号，按 `(主编号, 子编号)` 元组取最新契约；Sprint4-1 契约文件名由 `intent_sprint5_shipment_form_pages.yaml` 改回 `intent_sprint4_1_shipment_form_pages.yaml`。该改动仅影响门禁引擎选契约，不改变业务口径。

### 决策39：Sprint4-1 契约按评审修订

**决策**: 按评审意见修订 `INT-FREIGHT-SPRINT4-1-001`，核心原则为“只建立 Shipment → 财务对象观察窗口，不建立流程操作入口”：

- `invoice_ids` 不作为强制新增字段：允许提供发票关联展示字段/关联关系，但优先复用现有关联，仅在现有模型无法满足视图展示时才允许新增只读 One2many。
- 移除“来源结算单”列要求：本 Sprint 不新增、不回填 `account.move → freight.statement` 关联。
- 明确 Statements Page 仅展示现有 `freight.statement` 数据及版本关系，不改变状态/版本/快照语义，voided 历史必须可见。
- 明确 Vendor Bill 只展示、不创建；Invoices Page 仅展示 `freight_operation_id` 关联的 `account.move`（客户发票/供应商账单按类型列区分）。
- 删除 U-36，全状态展示直接定义为 `display_rule`；开放项收敛为 U-33 / U-34 / U-35，`decision_gate` 映射为 U-33→B-43、U-34→B-44、U-35→B-45。
- `business_rules.yaml` 与 `__manifest__.py` 移出契约范围；`context_audit` 仅保留 decision_note / sprint_log / context_version / intent_records / test_exec_records。

### 决策40：Sprint4-1 开放项确认

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-1-001` 三个开放项：

- U-33 → B-43：对账单/发票两个 Page 位于 Accountancy 页之后，先对账单后发票。
- U-34 → B-44：对账单 Page 不放置操作按钮，仅提供查看/打开。
- U-35 → B-45：发票 Page 不拆分应收/应付子页，合并一页并按 move_type 区分。

契约 `unresolved_unknowns` 清空，`decision_gate.status = satisfied`，可以进入编码。

### 决策52：Sprint4-4-1 契约按评审修订

**决策**: 按评审意见修订 `INT-FREIGHT-SPRINT4-4-1-001`，明确 fee_state 是费用“可用性/锁定状态”而非费用版本状态：

- `used` 统一定义为“费用被任一非 voided Statement（含 draft）引用”；Statement + statement.line 创建与费用 used 写回必须同一事务，任一步失败全部回滚。
- `used → confirmed` 仅由 Statement Void 动作触发，费用表单禁止直接操作（不允许 Revert Used 按钮）。
- `unconfirm` 条件收紧为“不存在任何非 voided Statement 引用”，历史 voided 引用不阻塞。
- 存量初始化优先级：已有非 voided Statement 引用 → used；否则 invoiced=True → used；否则 draft；不视为业务迁移。
- `fee_state` 是费用可编辑性的唯一权威状态；`statement_locked` 不参与状态机决策，仅辅助一致性校验。
- wizard 列表过滤不是最终约束，Statement 创建事务内重新校验（并发防御）。
- Copy as Draft 只复制业务字段，不复制 fee_state、Statement 引用、开票信息、审计字段。
- Delete 仅用于无业务引用的纯草稿；Cancel 用于业务废弃并留记录；不开发独立费用版本（audit_log 继续）。

### 决策53：Sprint4-4-1 契约按第二轮评审定稿

**决策**: 按第二轮评审（APPROVE WITH MINOR CHANGES）修订 `INT-FREIGHT-SPRINT4-4-1-001`：

- `used` 定义为“费用已被任一非 voided Statement 占用（包括 draft Statement）”；仅当所有关联 Statement 均为 voided 后，才可由 Statement 作废流程释放回 confirmed。
- `used → confirmed` 释放条件收紧：仅当该费用不存在任何非 voided Statement 引用时允许；费用表单禁止直接操作。
- Statement header/line 创建、费用引用建立与 fee_state=used 必须原子提交，任一步失败全部回滚。
- 新增并发业务不变量：同一费用最多只能被一个非 voided Statement 占用。
- 登记 B-58：历史未进入非 voided Statement、且未开票的存量费用初始化为 draft，业务人员需 Confirm 后方可进入新 Statement 流程。
- Delete 仅用于无业务引用的纯草稿；Cancel 用于业务废弃并留记录。
- `fee_state == confirmed` 为进入 Statement 的权威业务条件；legacy `invoiced / vendor_invoiced` 仅作兼容安全校验。
- `freight_shipment.py` 改为条件性修改（仅当现有调用链需要时）。
- 新增 `invariants` 章节（used 等价关系、并发唯一、Void 释放条件、Statement 确认不改状态、audit_log 边界）。

### 决策54：Sprint4-4-1 实施完成

**决策**: 按 `INT-FREIGHT-SPRINT4-4-1-001` 完成实施并验证（2026-08-13）：

- `freight.service.fee_state` 四态（draft / confirmed / used / canceled）与 Confirm / Unconfirm / Cancel / Copy as Draft 动作。
- 写锁以 fee_state 为准：confirmed / used / canceled 不可编辑删除；draft 被 statement 引用时不可删除。
- wizard 仅 `fee_state == confirmed` 费用可选；Statement 创建后费用同事务写回 used。
- Statement 作废仅当费用无其他非 voided Statement 引用时释放回 confirmed。
- 存量费用初始化：非 voided 引用或 invoiced=True → used，其余 draft（B-56/B-58）。
- 费用表单新增 fee_state 状态栏与操作按钮。
- 验证：context_loader 基线 PASS；verify.py 全门禁 PASS；button_immediate_upgrade + 25/25 odoo shell 断言 + log clean PASS。

### 决策55：Sprint4-4-2 契约起草（契约矛盾收口与口径对齐）

**决策**: 起草 `INT-FREIGHT-SPRINT4-4-2-001`（Sprint4-4-2-Conflict-Resolution），把 Sprint4-3/4-4/4-4-1 评审发现的矛盾收口：

- B-36 / B-52 标记 `SUPERSEDED_BY B-54 / B-55`（或改写为一致口径）。
- B-50 / B-55 增加交叉引用；B-53 中“statement 创建成功 → used”统一为“被任一非 voided Statement 占用 → used”。
- Sprint4-3 业务流补充：作废 → confirmed → unconfirm → draft → 修改 → confirm → 重新生成；释放条件补充“仅当不存在其他非 voided Statement 引用”。
- Sprint4-4 契约清除“按 U-40 确认”残留文案。
- 版本根逻辑名 `statement_root_id` = 物理字段 `statement_id`（不做 schema rename）。
- “同一费用最多一个非 voided Statement”增加数据库级并发保护；`statement_locked` 标记 deprecated。
- 登记 B-59：作废后修改费用的唯一路径（作废 → confirmed → unconfirm → draft → 修改 → confirm → 重新生成）。

### 决策56：Sprint4-4-2 契约按评审修订

**决策**: 按评审意见修订 `INT-FREIGHT-SPRINT4-4-2-001`，定位为“契约收口 + 最小一致性修正”：

- `statement_locked` 明确 `DEPRECATED`：role=legacy_compatibility_only、business_authority=false、state_machine_authority=false、new_code_usage=forbidden、removal=future_sprint；本 Sprint 不删除，禁止新增业务逻辑依赖。
- 并发控制从“加锁”提升为业务约束 + 事务步骤：`statement_generation_transaction`（锁定费用 → 事务内校验 confirmed → 校验无非 voided 引用 → 创建 header/lines → 写 used → COMMIT，任一步失败全部回滚）；实现方式不绑定。
- 新增核心不变量 `fee_statement_invariant`：`fee_state = used iff 存在至少一个非 voided Statement 引用`；一个费用最多被一个非 voided Statement 占用。
- `supersession` 结构化：B-36/B-52 保留历史记录，`effective=false`，`superseded_by B-54/B-55`。
- `naming` 仅文档层：logical_concept=statement_root_id、physical_field=statement_id、schema_change=false。
- 新增 forbidden：不得新增费用版本号/revision/snapshot 字段、独立费用审计表、历史状态表、费用版本体系。
- 新增 4 个状态不变量验收测试（used/confirmed 直写拦截、voided 不阻塞复用、同一费用双有效 Statement 不可能）。

### 决策57：Sprint4-4-2 契约按第二轮评审修订

**决策**: 按第二轮评审修订 `INT-FREIGHT-SPRINT4-4-2-001`：

- `fee_statement_invariant` 重构为 `transaction_commit_boundary` 作用域 + 四条状态规则（draft/confirmed 不得有非 voided 引用；used 必须被恰好一个非 voided Statement 引用；canceled 不得有引用且不可恢复）+ 10 条细化规则。
- `used_to_confirmed` 结构化：trigger = 仅由关联非 voided Statement void；precondition = 当前 Statement 确实引用该费用 + void 后无其他非 voided 引用；result = confirmed。
- B-59 改写为“作废后**如需修改费用**才走 unconfirm 路径；费用无错时可直接重新进入新 Statement”。
- `statement_root_id ↔ statement_id` 降级为 documentation_only，不作为核心 deliverable。
- `statement_locked` 从 functional acceptance 移入 `technical_cleanup`（DEPRECATED、禁止新代码依赖、仅兼容读取）。
- 状态守卫测试从“金额”扩大为“业务字段整体”（confirmed/used/canceled 直写业务字段必须失败）。

### 决策58：Sprint4-4-2 实施完成

**决策**: 按 `INT-FREIGHT-SPRINT4-4-2-001` 完成实施并验证（2026-08-13）：

- 口径对齐：B-36/B-52 标记 SUPERSEDED（保留历史）；B-50/B-53 与 B-54/B-55 统一；Sprint4-3 业务流补 unconfirm 路径；Sprint4-4 清除 U-40 残留文案。
- statement 创建增加 `SELECT FOR UPDATE` 行锁 + 事务内 fee_state 二次校验（statement_generation_transaction）。
- `statement_locked` 标记 DEPRECATED（仅兼容过渡，不参与状态机决策）。
- 未改变费用/结算单业务行为口径，未新增费用版本体系。
- 验证：context_loader 基线 PASS；verify.py 全门禁 PASS；button_immediate_upgrade + 22/22 odoo shell 断言 + log clean PASS。

### 决策59：Sprint4-4-3 契约起草（Create Statement 向导改造）

**决策**: 起草 `INT-FREIGHT-SPRINT4-4-3-001`（Sprint4-4-3-Wizard-Refactor），登记 B-60：

- 点击 Create Statement 后 wizard 默认绑定当前货单，货单号只读、不可重选。
- 选择/切换客户后重置费用列表，列表仅显示该客户 `fee_state=confirmed` 的 shipper/consignee 应收费用。
- 费用行可勾选/去勾选，勾选后生成结算单草稿；未勾选任何费用被阻止。
- 取代 FIX-STATEMENT-WIZARD-001 的“列出全部费用”展示行为，回归“仅 confirmed 可列可勾”口径。
- 不改变费用状态机、Statement 状态机与 Sprint4-4-2 生成事务/并发保护。

### 决策60：Sprint4-4-3 实施完成

**决策**: 按 `INT-FREIGHT-SPRINT4-4-3-001` 完成实施并验证（2026-08-13）：

- wizard 列表仅显示所选客户 `fee_state=confirmed` 的应收费用（shipper/consignee）。
- `shipment_id` 视图只读；切换 `customer_id` 重置费用列表；费用行可勾选/去勾选后生成。
- 保留 `eligibility_summary` 可选费用说明与 Fee State 列。
- 未改变费用/Statement 状态机与 Sprint4-4-2 生成事务/并发保护。
- 验证：context_loader 基线 PASS；verify.py 全门禁 PASS；button_immediate_upgrade + 7/7 odoo shell 断言 + log clean PASS。

### 决策41：Sprint4-2 契约起草（结算单生成 + 费用范围确认）

**决策**: 起草 `INT-FREIGHT-SPRINT4-2-001`：Shipment → 费用行 → 生成客户结算单草稿（Customer Statement Draft）。

- 结算单费用范围直接写入契约（B-46）：仅取 customer-side revenue charges（service_type = shipper / consignee）；vendor cost 不进入客户结算单。
- Vendor Bill 为供应商自有账单，我方不创建，不作为本 Sprint 技术债或流程对象（对齐 B-35 / BR-35）。
- 流程：Shipment → 费用行（shipper / consignee）→ Generate Statement → wizard 勾选费用行 → Statement Draft。
- 开放项 U-37（生成入口交互，默认沿用 B-39 wizard），确认后登记 B-47。

### 决策42：Sprint4-2 开放项确认

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-2-001` 开放项 U-37：结算单生成入口沿用现有 wizard 模式（Services 页 Generate Statement → 勾选费用行），登记为 B-47。契约 `decision_gate.status = satisfied`，可以进入编码。

### 决策43：Sprint4-3 契约起草（客户拒绝 → 作废 → 修改费用 → 新结算单）

**决策**: 起草 `INT-FREIGHT-SPRINT4-3-001`，按业务负责人确认的设计方向登记 B-48：

- 客户拒绝 = 当前结算单作废（voided），不作废原单修改；旧结算单及其费用快照不可变。
- 费用修改必须回到 `freight.shipment / freight.service` 费用层。
- 重新生成新结算单，版本链 `statement_id（根）+ version_no + previous_statement_id`（等价 revision_of 语义）。
- 审计链：Shipment → Fees；Statement-001 [Void] → Statement-002 [Draft/Confirmed]。
- 客户接受确认（confirmed）与开票不在本 Sprint 范围。

### 决策44：Sprint4-3 契约按评审修订

**决策**: 按评审意见修订 `INT-FREIGHT-SPRINT4-3-001`：

- 作废边界不绑定 `draft`：客户拒绝仅允许对尚未确认、尚未开票的当前结算单执行作废，来源状态由现有状态机确定。
- “费用释放”改为“费用重新成为下一版结算单来源”：作废后原结算单快照不可变，对应 `freight.service` 恢复为可参与下一结算单生成的业务来源；不得通过修改/删除旧 `statement.line` 实现费用重新归属。
- 版本根字段重命名为 `statement_root_id`（既有 `statement_id` 同步重命名），版本链为 `statement_root_id + version_no + previous_statement_id`。
- `voided` 为终态：不允许重新激活、恢复、确认或直接转入下一状态；Void 必须通过 `action_void()` 统一方法执行。
- 客户拒绝动作不自动修改 `freight.service` 费用；费用修改必须由业务人员在费用层显式完成。
- 增加历史快照隔离测试与重复生成幂等测试。
- 开放项 U-38：`voided_reason` 是否强制录入（默认可选字段），确认后登记 B-49。

### 决策45：Sprint4-3 契约按第二轮评审修订

**决策**: 按第二轮评审修订 `INT-FREIGHT-SPRINT4-3-001`：

- 删除 `statement_id → statement_root_id` 字段重命名任务；版本根引用沿用 Sprint4-2 已确认定义，本 Sprint 不做 schema rename。
- `void_policy.allowed_source_states = [draft]`，禁止对 voided / confirmed / draft_invoice 作废；Void 必须经 `action_void()` 统一方法。
- 明确作废结算单不回写或重置 `freight.service` 费用事实；重新生成时由现有费用选择规则重新计算可纳入费用。
- 新增 `snapshot_invariants`：Statement.line 是不可变快照，不重新从 freight.service 计算覆盖，历史 line 不受费用后续修改影响，新版本必须创建新 line。
- U-38 确认：`voided_reason` 可选、不强制（B-49），不再阻塞编码。
- 新增开放项 U-39：Draft 结算单在费用再次修改后是原 Draft 重建/刷新，还是生成新的 version_no（确认后登记 B-50）。
- 新增历史快照反向污染测试与重复生成幂等测试。

### 决策46：Sprint4-3 开放项确认（U-39 → B-50）

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-3-001` 开放项 U-39：Draft 结算单在费用再次修改后重新生成时，旧 Draft 作废（voided）并永久留存，新结算单生成新 version_no，不允许原地刷新/重建同版本，登记为 B-50。契约 `decision_gate.status = satisfied`，可以进入编码。

### 决策47：Sprint4-4 契约起草（客户接受 → Confirmed）

**决策**: 起草 `INT-FREIGHT-SPRINT4-4-001`（Sprint4-4-Statement-Confirm），登记 B-51：

- Draft Statement：允许修改/删除/增加费用，允许重新生成。
- Confirmed Statement：结算单锁定，不可直接修改；关联费用不可被新结算单重复选择；禁止作废。
- Void Statement：不可恢复、不可修改，仅作为历史记录。
- 开放项 U-40：Confirmed 后 freight.service 费用层是否完全锁定（默认建议：模型层+视图层锁定普通用户修改，不新增 security group，保持 B-28 现状），确认后登记 B-52。
- 草稿发票生成（Sprint4-5）、Vendor Bill、权限组建设不在本 Sprint 范围。

### 决策48：Sprint4-4 开放项确认（U-40 → B-52）

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-4-001` 开放项 U-40：费用层部分锁定，只锁定已生成结算单的费用。登记 B-52：

- `confirmed / draft_invoice` 结算单关联的 `freight.service` 费用不可修改、不可删除。
- `draft` 结算单关联费用与未进入结算单的费用保持可编辑。
- `voided` 结算单关联费用解除锁定，可再次用于新结算单（对齐 Sprint4-3 作废释放语义）。

契约 `decision_gate.status = satisfied`，可以进入编码。

### 决策49：Sprint4-4-1 契约起草（费用状态管理）

**决策**: 起草 `INT-FREIGHT-SPRINT4-4-1-001`（Sprint4-4-1-Fee-State-Management），登记 B-53：费用显式状态四态 draft / confirmed / used / canceled；draft 可编辑/删除/取消；confirmed 不可编辑/删除且可生成 statement；statement 创建成功 → used；statement 作废 → confirmed；canceled 终态；费用表单增加状态栏与 Confirm/Cancel 按钮。

- 评估确认：费用显式状态比纯派生更直观，费用表单需要状态栏与按钮。
- 评估发现 4 个必须确认的开放项：
  - U-41：作废后回 confirmed 且 confirmed 不可编辑，与“作废→修改费用→新结算单”闭环冲突。
  - U-42：statement 创建即 used（含 draft）与 B-50“draft 期间修改费用重新生成”冲突。
  - U-43：存量费用 fee_state 初始化策略（历史数据不迁移 B-32）。
  - U-44：canceled 是否允许恢复/编辑/删除。

### 决策50：门禁引擎支持多级 sprint 子编号

**决策**: `context_loader.py` 与 `verify.py` 的 sprint 契约选择从“(主, 子)”升级为“任意层级数字元组”，支持 `sprint4_4_1` / `sprint4-4-1` / `sprint4.4.1` 文件名；`sprint4_4_1 > sprint4_4 > sprint4`。

### 决策51：Sprint4-4-1 开放项确认（U-41 ~ U-44 → B-54 ~ B-57）

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-4-1-001` 四个开放项：

- U-41 → B-54：confirmed 可 unconfirm 退回 draft（仅无 statement 引用时），退回后可编辑和作废。
- U-42 → B-55：被任何非 voided 结算单（含 draft）引用的费用即 used，不可编辑、不可取消；费用修改需先作废旧结算单使其回 confirmed。
- U-43 → B-56：存量费用不做迁移（B-32）；开发环境已开票（invoiced=True）费用统一 used，未开票费用默认 draft。
- U-44 → B-57：canceled 费用不可恢复、不可编辑/删除，可通过复制为新 draft 继续使用。

契约 `unresolved_unknowns` 清空，`decision_gate.status = satisfied`，可以进入编码。

### 决策61：Sprint4-4-4 契约起草（向导生命周期重构）

**决策**: 起草 `INT-FREIGHT-SPRINT4-4-4-001`（Sprint4-4-4-Wizard-Refactor），登记 B-61 ~ B-68：

- B-61：`wizard.line.service_id` 创建即绑定，禁止 name+qty+price 猜测恢复。
- B-62：create/onchange 强制行集合等于 eligible 且绑定 service_id；普通 write 保留用户 select。
- B-63：生成前强制校验 `selectable`。
- B-64：FOR UPDATE 行锁后全量重校验 eligible（fee_state / invoiced / 非 voided 占用 / 归属）。
- B-65：`customer_id` 必须是当前 shipment 的 shipper/consignee 显式 invariant。
- B-66：eligibility 收口为单一 helper，消除两套规则漂移。
- B-67：`tax_amount/settlement_rate` 补 readonly，Statement Line `sequence` 按 10 步进。
- B-68：费用占用唯一事实来源为 `fee_state`，statement 引用仅作迁移触发/防御。
- 开放项 U-45：打开向导默认勾选态，确认后登记 B-69。

### 决策62：Sprint4-4-4 开放项确认（U-45 → B-69）

**决策**: 业务负责人确认 `INT-FREIGHT-SPRINT4-4-4-001` 开放项 U-45：打开向导时 eligible 费用行默认全部勾选（select=True），用户去勾不需要的费用；默认不勾选不采用。登记 B-69。契约 `decision_gate.status = satisfied`，可以进入编码。
