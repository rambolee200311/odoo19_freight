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
