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
| B-36 | 客户 reject 的对账单作废，释放费用为可修改状态 | 2026-08-12 用户确认（U-30） |
| B-37 | confirmed 后强制版本化，已确认版本不可原地修改 | 2026-08-12 用户确认（U-31） |
| B-38 | 不建立 Statement Line ↔ Invoice Line 行级关联，仅 header 级 statement ↔ invoice 关联 | 2026-08-12 用户确认（U-32） |
| B-39 | 生成结算单使用向导，在列表行勾选费用行生成结算单 | 2026-08-12 用户确认 |
| B-40 | 客户拒绝后费用修改必须回到 freight.shipment / freight.service，结算单本身不可编辑费用 | 2026-08-12 用户确认 |
| B-41 | 客户接受后生成草稿应收发票（account.move draft），草稿不代表已过账 | 2026-08-12 用户确认 |
| B-42 | 开票申请为预留业务节点，本 Sprint 不开发模型/按钮/审批流/状态机/权限 | 2026-08-12 用户确认 |

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
| U-33 | 对账单/发票两个 Page 在货运单表单中的位置与顺序（默认：Accountancy 之后，先对账单后发票） |
| U-34 | 对账单 Page 是否直接放置操作按钮（默认：仅查看跳转，操作保留在结算单表单/服务页） |
| U-35 | 发票 Page 是否拆分应收/应付子页（默认：合并一页，按 move_type 区分） |
| U-36 | 发票 Page 是否展示全部状态（默认：全部展示，按状态列区分） |

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
