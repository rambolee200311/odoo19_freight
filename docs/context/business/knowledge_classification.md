# 知识分类登记（Fact / Assumption / Unknown）

分类定义：

- CODE_FACT：代码当前实现，不代表业务规定。
- BUSINESS_FACT：用户确认的业务事实。
- DECISION：已登记的架构/业务决策。
- CONSTRAINT：刚性约束。
- TECHNICAL_DEBT：已知债务，允许修复。
- UNKNOWN：需要确认，禁止自行补全。
- ASSUMPTION：方案/推测，未经确认。

## 已确认业务事实（BUSINESS_FACT）

| ID | 内容 | 来源 |
|---|---|---|
| B-01 | 收入 = shipper + consignee 服务开票金额；成本 = vendor 服务账单金额 | 2026-08-11 用户确认 |
| B-02 | 费用可分可合，费用行指定开票对象 | 2026-08-11 用户确认 |
| B-03 | 本位币人民币，允许外币报价/开票 | 2026-08-11 用户确认 |
| B-04 | 不含税单价 + 税率录入，税额/含税可手改，费用类型可配默认税率 | 2026-08-11 用户确认 |
| B-05 | 开票时点由操作员决定 | 2026-08-11 用户确认 |
| B-06 | 无网上银行，财务登记收付款，不做复杂核销 | 2026-08-11 用户确认 |
| B-07 | 利润 = 已开票收入 − 已确认成本 − 税费 | 2026-08-11 用户确认（税费解释见 A-3） |
| B-08 | 不强制状态机，不做精细报价管理 | 2026-08-11 用户确认 |
| B-09 | 报表/权限后定，遗留兼容保留 | 2026-08-11 用户确认 |
| B-10 | 数据检查用 odoo shell，禁止直连数据库 | 2026-08-11 用户确认 |
| B-11 | 模块升级常驻 + XML-RPC + log 检查 | 2026-08-11 用户确认 |
| B-12 | 业务范围：客户主体=中国天津出口代理货代；核心业务=报价/订舱/货运单全生命周期；财务核心=收入/成本/应收/应付核算与对账 | 项目初始约束（用户 2026-08-11） |
| B-13 | 菜单范围：Customers/Vendors/Fleets/Services 收拢到 Archive 菜单，Packages 保留独立入口，其他菜单不动 | 2026-08-11 用户确认（U-10） |
| B-14 | Invoicing 菜单范围：应收/应付发票仅显示 freight_operation_id 有值单据 | 2026-08-11 用户确认（U-11） |
| B-23 | 对账单折算默认取当前汇率，允许用户录入结算汇率覆盖（Sprint3-002 确认） | 2026-08-12 用户确认（U-02） |
| B-24 | 费用行整行进一张发票，禁止行内分批/部分开票（Sprint3-002 确认） | 2026-08-12 用户确认（U-01） |
| B-25 | 利润公式中“税费”净额 = 销项税 − 进项税（Sprint3-002 确认） | 2026-08-12 用户确认（U-03） |
| B-26 | 服务/产品档案新增税目编码、税目名称字段；手工调整税额按 tax_amount 权威落账（B-19） | 2026-08-12 用户确认（U-04） |
| B-27 | PDF 对账单需求以 docs/reports/应收对账单原始单据.md 为输入 | 2026-08-12 用户确认（U-05） |
| B-28 | 当前不建设角色权限与 portal 收敛，保持现状 | 2026-08-12 用户确认（U-06） |
| B-29 | 标准 Accounting 创建入口当前不纳入收敛，Sprint4 只收敛 tk_freight 业务开票入口 | 2026-08-12 用户确认（U-23） |
| B-30 | 旧开票入口采用隐藏策略，保留方法与兼容调用能力 | 2026-08-12 用户确认（U-24） |
| B-31 | Statement 编号规则：STM/年月/4位流水码 | 2026-08-12 用户确认（U-25） |
| B-32 | 历史数据不迁移，对账单从新数据开始 | 2026-08-12 用户确认（U-26） |
| B-33 | 自动生成费用行通过对账单状态管理，客户确认后生成发票 | 2026-08-12 用户确认（U-27） |
| B-34 | 不需要调整申请/审批角色流程 | 2026-08-12 用户确认（U-28） |
| B-35 | 供应商成本行排除在客户对账单外 | 2026-08-12 用户确认（U-29） |
| B-36 | 客户 reject 的对账单作废，释放费用为可修改状态（SUPERSEDED_BY B-54/B-55，历史保留） | 2026-08-12 用户确认（U-30） |
| B-37 | confirmed 后强制版本化，已确认版本不可原地修改 | 2026-08-12 用户确认（U-31） |
| B-38 | 不建立 Statement Line ↔ Invoice Line 行级关联，仅 header 级 statement ↔ invoice 关联 | 2026-08-12 用户确认（U-32） |
| B-39 | 生成结算单使用向导，在列表行勾选费用行生成结算单 | 2026-08-12 用户确认 |
| B-40 | 客户拒绝后费用修改必须回到 freight.shipment / freight.service，结算单本身不可编辑费用 | 2026-08-12 用户确认 |
| B-41 | 客户接受后生成草稿应收发票（account.move draft），草稿不代表已过账 | 2026-08-12 用户确认 |
| B-42 | 开票申请为预留业务节点，本 Sprint 不开发模型/按钮/审批流/状态机/权限 | 2026-08-12 用户确认 |
| B-43 | 对账单/发票两个 Page 位于 Accountancy 页之后，先对账单后发票 | 2026-08-12 用户确认（U-33） |
| B-44 | 对账单 Page 不放置操作按钮，仅提供查看/打开 | 2026-08-12 用户确认（U-34） |
| B-45 | 发票 Page 不拆分应收/应付子页，合并一页并按 move_type 区分 | 2026-08-12 用户确认（U-35） |
| B-46 | 客户结算单费用范围 = customer-side revenue charges（shipper/consignee）；vendor cost 不进入客户结算单；Vendor Bill 为供应商自有账单，我方不创建（对齐 B-35/BR-35） | 2026-08-12 用户确认 |
| B-47 | 结算单生成入口沿用现有 wizard 模式（Services 页 Generate Statement → 勾选费用行），不新建独立入口 | 2026-08-12 用户确认（U-37） |
| B-48 | 客户拒绝 = 当前 draft 结算单进入 voided 终态，不作废原单修改；费用修改回到 freight.shipment / freight.service；重新生成新结算单并创建全新 statement.line 快照；版本链 statement_root_id + version_no + previous_statement_id（版本根引用沿用 Sprint4-2 定义，不做字段重命名），旧结算单永久不可变 | 2026-08-12 用户确认 |
| B-49 | voided_reason 为可选字段，不强制录入，不作为 Sprint4-3 编码阻塞项 | 2026-08-12 用户确认（U-38） |
| B-50 | Draft 结算单在费用再次修改后重新生成：旧 Draft 作废（voided）并永久留存，新结算单生成新 version_no；不允许原地刷新/重建同版本（draft 引用费用即 used，修改需先作废旧 Draft，见 B-55/B-59） | 2026-08-12 用户确认（U-39） |
| B-51 | 客户接受后 Statement 进入 Confirmed 并锁定，不可直接修改；Voided 不可恢复、不可修改，仅作为历史记录；Draft 允许修改/删除/增加费用并重新生成 | 2026-08-13 用户确认 |
| B-52 | 费用层部分锁定：仅 confirmed / draft_invoice 结算单关联的 freight.service 费用不可修改、不可删除；draft 结算单关联费用与未进入结算单费用保持可编辑；voided 结算单关联费用解除锁定，可再次用于新结算单（对齐 Sprint4-3 作废释放语义）（SUPERSEDED_BY B-54/B-55，历史保留） | 2026-08-13 用户确认（U-40） |
| B-53 | 费用显式状态四态：draft / confirmed / used / canceled；draft 可编辑/删除/取消；confirmed 不可编辑/删除且可生成 statement；被任一非 voided Statement 占用 → used；statement 作废 → confirmed；canceled 终态；费用表单增加状态栏与状态切换按钮 | 2026-08-13 用户确认 |
| B-54 | confirmed 费用可 unconfirm 退回 draft，条件为不存在任何非 voided Statement 引用（历史 voided 引用不阻塞）；退回后可编辑和作废 | 2026-08-13 用户确认（U-41） |
| B-55 | used = 费用已被任一非 voided Statement 占用（包括 draft Statement）：不可编辑、不可取消；仅当所有关联 Statement 均为 voided 后，才可由 Statement 作废流程释放回 confirmed；费用表单禁止直接执行 used → confirmed | 2026-08-13 用户确认（U-42） |
| B-56 | 不修改存量费用业务数据（B-32）；fee_state 初始化按既有业务事实映射：已有非 voided Statement 引用 → used；否则 invoiced=True → used；否则 draft。该初始化仅用于建立 fee_state，不视为业务迁移 | 2026-08-13 用户确认（U-43） |
| B-57 | canceled 费用不可恢复、不可编辑/删除，可通过复制为新 draft 继续使用 | 2026-08-13 用户确认（U-44） |
| B-58 | 历史未进入非 voided Statement、且未开票的存量费用初始化为 draft；业务人员需 Confirm 后方可进入新的 Statement 流程 | 2026-08-13 评审确认 |
| B-59 | 作废后如需修改费用，唯一修改路径为：Statement voided → fee confirmed → unconfirm → draft → 修改 → confirm → 重新生成新 Statement；不得直接修改 confirmed/used 费用（作废后费用无错时可直接重新进入新 Statement） | 2026-08-13 评审确认 |
| B-60 | Create Statement 向导：列表仅显示所选客户 fee_state=confirmed 的应收费用（shipper/consignee）；shipment_id 只读不可重选；切换 customer_id 重置费用列表；费用行可勾选/去勾选后生成结算单 | 2026-08-13 用户确认 |

## 已取代决策（SUPERSEDED）

| 原决策 | 状态 | 取代为 | 生效 | 历史记录 |
|---|---|---|---|---|
| B-36 | SUPERSEDED | B-54 / B-55 | false | retained（作废释放语义以 B-54/B-55 为准） |
| B-52 | SUPERSEDED | B-54 / B-55 | false | retained（draft 引用费用即 used，不可编辑） |

## 引用规范

- `B-*`：已确认业务事实/决策（本文件 B 清单）；`B-08` 为当前阶段决策，范围=当前项目/当前阶段，未来可重新讨论。
- `TD-*`：技术债（`mymodules/tk_freight/docs/technical_debt.md`），分类见该文件。
- `U-*`：历史 UNKNOWN / 未确认需求编号（本文件 U 清单）；已确认项收敛为 `B-*`（如 U-10 → B-13、U-11 → B-14），不再以 U 编号表达 CONFIRMED 决策。
- `CODE_FACT`：代码现状，不代表业务规定。
- `DOMAIN_REFERENCE`：行业通用参考（`business/reference/`），仅用于理解领域，不等于项目需求、决策、代码事实或 Forbidden Change。
- `BR-*`：机器可读业务规则（`business/business_rules.yaml`），状态 CONFIRMED / ASSUMPTION / UNKNOWN / DECISION_CONFIRMED，供 verify 对比器使用。

## 推测/方案（ASSUMPTION / NEEDS_CONFIRMATION）

| ID | 内容 | 关联 |
|---|---|---|
| A-1 | 费用行整行进一张发票，不做行级分批 | 已被 B-24 确认 |
| A-2 | 收入/成本按单据日汇率，收付款按登记日汇率 | 原口径3 的延伸；对账单折算已被 B-23 替代 |
| A-3 | 税费净额 = 销项税 − 进项税 | 已被 B-25 确认 |
| A-4 | 手工税额开票用定额税码（未确认；当前系统无税目编码/名称字段，产品档案仅可维护标准税率） | finance_flow 税费规则 |
| A-5 | 开票生成 Odoo 草稿单据 | 原口径5 的延伸 |
| A-6 | 服务行缺 partner 禁止开票 | 原流程铁律 |
| A-7 | 发票状态变化回写服务行与货单 | 原流程铁律 |
| A-8 | 财务字段按本位币展示、发票不改口径 | 原数据铁律 |

## 未知事项（UNKNOWN / NEEDS_CONFIRMATION）

| ID | 事项 |
|---|---|
| U-08 | 货单序列 transport→operation 映射是否保留 |
| U-09 | 路由生成拣货单 pickup/delivery 类型映射语义 |

## Sprint4 实施状态（2026-08-12）

`CODE_FACT` Sprint4 已按 `INT-FREIGHT-SPRINT4-001` 实施：

- `freight.statement / freight.statement.line`（状态机 draft → voided / confirmed → draft_invoice，版本链 `statement_id + version_no + previous_statement_id`）。
- `freight.statement.wizard / freight.statement.wizard.line`（列表勾选费用行生成结算单，B-39）。
- `product.template.tax_code / tax_name`（B-26）；结算单行 `tax_rate / tax_amount / amount_untaxed / amount_total / settlement_rate`，手工调整以 `tax_amount` 为权威。
- `account.move.freight_statement_id` header 级来源追溯（B-38），不做行级关联。
- 旧 `action_create_invoice` 保留方法但 UI 隐藏、直调拦截；遗留 server action 取消列表绑定（B-30）。
- 未开发：开票申请（B-42）、Vendor Bill 生成、dispute/partially_invoiced/invoiced/adjusted、分批开票、confirmed 后原地修改。

## 代码事实（CODE_FACT）

| ID | 内容 |
|---|---|
| C-01 | `action_create_vendor_bill` 使用 `data.sale` 计价（TD-001） |
| C-02 | `_compute_total_amount` 直接累加 `amount_total_signed`（TD-002） |
| C-03 | `service.status='quotation'` 为非法状态值（TD-008） |
| C-04 | `ir_actions_server_freight_create_*` 缩进错误（TD-006） |
| C-05 | `foce_Save`、`placeholer` 拼写残留（TD-021） |

代码事实不代表业务规定；修复按技术债分类执行。

## 技术债分类（TECHNICAL_DEBT）

见 `mymodules/tk_freight/docs/technical_debt.md`（TD-001 ~ TD-025，含 Known Debt / Risk / Confirmed Bug / Unknown 分类）。
