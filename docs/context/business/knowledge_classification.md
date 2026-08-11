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

## 引用规范

- `B-*`：已确认业务事实/决策（本文件 B 清单）；`B-08` 为当前阶段决策，范围=当前项目/当前阶段，未来可重新讨论。
- `TD-*`：技术债（`mymodules/tk_freight/docs/technical_debt.md`），分类见该文件。
- `U-*`：UNKNOWN / 未确认需求（本文件 U 清单）。
- `CODE_FACT`：代码现状，不代表业务规定。
- `DOMAIN_REFERENCE`：行业通用参考（`business/reference/`），仅用于理解领域，不等于项目需求、决策、代码事实或 Forbidden Change。

## 推测/方案（ASSUMPTION / NEEDS_CONFIRMATION）

| ID | 内容 | 关联 |
|---|---|---|
| A-1 | 费用行整行进一张发票，不做行级分批 | 原 freight_rule 口径2 的延伸 |
| A-2 | 收入/成本按单据日汇率，收付款按登记日汇率 | 原口径3 的延伸 |
| A-3 | 税费净额 = 销项税 − 进项税 | 原口径7 的解释 |
| A-4 | 手工税额开票用定额税码 | finance_flow 税费规则 |
| A-5 | 开票生成 Odoo 草稿单据 | 原口径5 的延伸 |
| A-6 | 服务行缺 partner 禁止开票 | 原流程铁律 |
| A-7 | 发票状态变化回写服务行与货单 | 原流程铁律 |
| A-8 | 财务字段按本位币展示、发票不改口径 | 原数据铁律 |

## 未知事项（UNKNOWN / NEEDS_CONFIRMATION）

| ID | 事项 |
|---|---|
| U-01 | 费用行分批开票是否允许 |
| U-02 | 汇率折算日期口径 |
| U-03 | 利润公式中“税费”的净税解释 |
| U-04 | 手工税额的开票机制 |
| U-05 | 报表需求（对账/利润/账龄） |
| U-06 | 角色权限与门户写权限 |
| U-07 | U8C/外部财务接口是否恢复 |
| U-08 | 货单序列 transport→operation 映射是否保留 |
| U-09 | 路由生成拣货单 pickup/delivery 类型映射语义 |

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
