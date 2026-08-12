# Sprint3-002 财务流程逆向分析与实施前设计输入

> 阶段：Analysis Only
> 规则：本报告不修改业务代码、模型、视图、权限或数据库结构；设计建议仅为候选方案。
> 标注：`CODE_FACT` 代码事实 / `BUSINESS_FACT` 已确认业务事实 / `DECISION` 已登记决策 / `CONSTRAINT` 刚性约束 / `ASSUMPTION` 未确认假设 / `PROPOSAL` 设计候选方案 / `UNKNOWN` 待确认事项 / `CONFLICT` 冲突。

---

## 1. 现状业务流程

### 1.1 术语统一（必须遵守）

```text
BUSINESS_TERM: 费用明细 / shipment fee
CODE_TERM:     freight.service
```

用户需求中“shipment fee”对应的实际代码模型是 `freight.service`。本报告后续一律以 `CODE_FACT` 实际模型 `freight.service` 为准；Sprint4 不得另建 `shipment.fee` 重复模型。

### 1.2 现状结论

`CODE_FACT` 当前**存在多个可创建 `account.move` 的入口**，其中主业务入口为“货运单直接开票”；整体架构尚未形成统一的发票入口治理：

```text
                     ┌─ action_create_invoice（货单表单）
                     │
freight.service ─────┼─ action_create_vendor_bill
                     │
                     ├─ server action（遗留，TD-006）
                     │
                     ├─ legacy methods（shipper/consignee）
                     │
                     └─ 标准 Accounting 手工创建
                              ↓
                         account.move
```

`CODE_FACT` 现状不存在：Draft 对账单、客户核对、异议、确认、费用锁定、版本、行级开票、Credit Note 专属流程。

---

## 2. 现状代码调用链

### 2.1 费用行入口

- `freight.shipment.freight_services` 内联编辑（`freight_shipment_view.xml` Services 页）。
- 订舱转货单：`freight_bookings.py` 自动生成 `freight.service`（service_type=consignee）。
- 包装费用：`freight_configuration.py action_insert_line_service` 生成 `charges_product_1` 服务行。
- 路由费用：`freight_configuration.py action_insert_line_service`（route）生成 `route_product_1` 服务行。
- 保险费用：`freight_shipment.py add_policy` 生成 `policy_product_1` 服务行。

### 2.2 费用字段

`CODE_FACT` `freight.service` 仅有 `service_type / service_id / name / qty / sale / cost / currency_id / shipper_id / consignee_id / vendor_id / customer_invoice / vendor_invoice / invoiced / vendor_invoiced / status`；无税率/税额/含税金额字段，无费用类型默认税率配置。

### 2.3 汇总

`CODE_FACT`

- `_compute_service_charges`：按 service_type 累加 `sale * qty`，不区分币种。
- `_compute_total_amount`：累加已过账 `amount_total_signed`（out_invoice 已为本位币 signed 口径，运行时确认）；供应商账单为供应商开具原件、业务侧按原币登记，不视为我方技术债；TD-002 表述需复核。
- `_compute_invoice`：按 `freight_operation_id` 统计 out_invoice / in_invoice 数量。

---

## 3. account.move 创建链

### 3.1 `action_create_invoice`

`CODE_FACT`

```text
表单按钮
  ↓
freight.shipment.action_create_invoice()
  ↓
按 shipper_id / consignee_id / currency_id 分组未开票 freight.service
  ↓
data.invoiced = True；data.status = 'invoice'
  ↓
account.move.create({
  move_type: 'out_invoice',
  partner_id, currency_id, freight_operation_id,
  invoice_line_ids: [{product_id, name, quantity, price_unit}]
})
```

问题：无幂等校验；不写 `customer_invoice`；发票行不追溯 `freight.service`；不校验客户/币种/税率。

### 3.2 `action_create_vendor_bill`

`CODE_FACT`

```text
表单按钮
  ↓
按 vendor_id / currency_id 分组未开票 vendor 费用
  ↓
data.vendor_invoiced = True；data.status = 'bill'
  ↓
account.move.create({move_type: 'in_invoice', price_unit: data.sale, ...})
```

问题：该入口为遗留创建路径；业务口径为供应商开具原件、业务侧登记；不写 `vendor_invoice`；无行级追溯。TD-001 已标记延期（供应商原始账单，不作为当前流程技术债）。

### 3.3 Server Action / 遗留方法

`CODE_FACT`

- `ir_actions_server_freight_create_shipper_invoice / ..._consignee_invoice` → `action_create_shipper_invoice / action_create_consignee_invoice`。
- 两个 server action 代码缩进错误（TD-006）。
- 遗留方法按货单总额生成一张发票（product=`freight_order_1`），并写 `freight.multiple.invoice`，非按费用行开票。

### 3.4 `shipment.invoice` 向导

`CODE_FACT` `wizard/shipment_invoice.py` 检查 `service_type=='customer'`（该枚举不存在）并创建 `sale.order`，不是发票；无菜单挂接，属死代码（TD-007）。

---

## 4. 现有开票入口清单

| 入口 | 位置 | 行为 | 状态 |
|---|---|---|---|
| 货单表单按钮 Create Invoice | `freight_shipment_view.xml:787` → `action_create_invoice` | 按 shipper/consignee + 币种分组直接建 out_invoice | 主入口，无对账单约束 |
| 货单表单按钮 Create Vendor Bill | `freight_shipment_view.xml:785` → `action_create_vendor_bill` | 按 vendor + 币种分组直接建 in_invoice，按 `sale` 计价 | 供应商链路入口 |
| 列表 Server Action | `ir_actions_server_freight_create_shipper/consignee_invoice` | 调遗留发货人/收货人开票方法 | 缩进错误，TD-006 |
| 货单 stat button | `button_customer_invoices / button_vendor_bills` | 仅打开发票列表/表单，create=False | 查看入口 |
| Invoicing 菜单 | `menus.xml action_freight_invoice_receivable/payable` | 展示 `freight_operation_id` 有值单据 | 未禁用创建 |
| Odoo 标准 Accounting 菜单 | account 模块 | 可直接创建 account.move | 潜在绕过入口（B-29 已确认不纳入收敛） |
| `shipment.invoice` 向导 | `wizard/shipment_invoice.py` | 检查不存在的 `service_type=='customer'`，创建 sale.order | 死代码，TD-007 |

---

## 5. CODE_FACT 证据等级

### FACT-A：直接代码证据

- `mymodules/tk_freight/models/freight_shipment.py`（`action_create_invoice` / `action_create_vendor_bill` / `_compute_total_amount` / 遗留开票方法）
- `mymodules/tk_freight/models/freight_configuration.py`（`freight.service` / `account.move` 扩展 / `freight.multiple.invoice` / 自动生成费用行）
- `mymodules/tk_freight/wizard/shipment_invoice.py`（遗留向导）
- `mymodules/tk_freight/views/freight_shipment_view.xml`（按钮与 server action）
- `mymodules/tk_freight/views/menus.xml`（Invoicing 菜单）
- `mymodules/tk_freight/security/ir.model.access.csv`（ACL）

### FACT-B：运行时验证

已通过 `odoo-bin shell -c odoo.conf -d odoo19_freight` 复核 `freight.shipment(1)`、`freight.service(1)`、`account.move(1)` 及关联记录（2026-08-12）。核验范围覆盖 id=1 单据，未逐一复核全部存量记录。

#### 运行时核验结果

| 对象 | 实测值 | 结论 |
|---|---|---|
| `freight.shipment(1)` | OCEAN/2026/03/00001；5 条 `freight.service`；`total_service_charge=5500.0`；`total_invoiced=32500.0`；`total_bills=-970.0` | `total_invoiced=32500` 是公司本位币 signed 口径：USD 4500 × 7 = 31500 + CNY 1000 = 32500，与 `amount_total_signed` 一致，**不是失真**；`total_bills=-970` 为供应商账单按原币（USD）登记的 signed 金额，符号口径正确；供应商账单由供应商开具原件、业务侧登记，不视为我方技术债 |
| `res.currency / res.currency.rate` | USD rate=0.142857（1 USD = 7 CNY），rate 日期 2026-08-10 | 汇率配置存在；out_invoice signed 金额已按本位币折算 |
| `freight.service(1)` | consignee；sale=2250；qty=2；USD；status=invoice；invoiced=True；`customer_invoice=False` | 已标记开票但无发票反向关联（TD-003 运行时确认） |
| `freight.service` 全部记录 | `customer_invoice` 有值 0 条、`vendor_invoice` 有值 0 条 | 费用行与发票双向追溯字段实际为空 |
| `account.move(1)` | INV/2026/00002；out_invoice；posted；`freight_operation_id=1`；partner=TAIDA Netherlands B.V.；USD；untaxed=4500；tax=0；1 条 invoice line（陆运费，qty=2，unit=2250，无税） | 发票行无费用行/对账单追溯字段 |
| `account.move` / `account.move.line` | 存在标准字段 `statement_id` / `statement_line_id`（Odoo 银行流水对账字段），当前 invoice(1) 均为 False；全局有值 0 条 | **不是**对账单字段；Sprint4 新增对账单字段必须避免命名冲突（建议 `freight_statement_id` / `freight_statement_line_id`） |
| 模型检查 | `freight.statement` / `freight.statement.line` / `shipment.fee` 均不存在 | 对账单模型缺失事实确认 |
| `freight.multiple.invoice` | 0 条记录 | 遗留表当前为空，无业务数据依赖 |
| 关联发票 | shipment(1) 下 out_invoice=2 张（4500 / 1000）、in_invoice=1 张（970） | 现有发票均通过 header 级 `freight_operation_id` 关联 |

### FACT-C：认知资产声明

- `docs/context/business/business_rules.yaml`
- `docs/context/business/finance_flow.md`
- `docs/context/constraints/forbidden_change.yaml`
- `mymodules/tk_freight/docs/technical_debt.md`
- `docs/context/architecture/module_map.md`

### 未验证内容

仅来自历史文档或技术债登记（TD 清单、knowledge_classification）的内容，尚未经运行时验证，统一标记 `UNKNOWN`，不得作为“代码真的有”的证据。

---

## 6. 认知资产规则

### 6.1 已确认业务规则（BUSINESS_FACT / DECISION）

- BR-01：收入 = shipper + consignee 服务行开票金额；成本 = vendor 服务行账单金额。
- BR-02：费用可分可合，费用行指定开票对象。
- BR-03：本位币人民币，允许外币报价/开票。
- BR-04：利润 = 已开票收入 − 已确认成本 − 税费（税费净额 = 销项税 − 进项税，B-25 已确认）。
- BR-05：开票时点由操作员决定。
- BR-06：收付款登记，不做复杂核销。
- BR-09 / BR-10：当前阶段不建设价目表/报价审批、不强制状态机。
- BR-12：不含税单价 + 税率录入；税额/含税可手工修改；费用类型可配置默认税率。
- BR-13 / BR-14：菜单与发票菜单范围（Sprint1）。

### 6.2 Sprint4 候选规则（历史事实，非本阶段约束）

`CODE_FACT`（历史事实）：`B-15 ~ B-22 / BR-15 ~ BR-22` 已写入 `INT-FREIGHT-SPRINT4-001`（暂存实施契约），但**尚未经业务负责人确认**，也未登记到 `business_rules.yaml` / `knowledge_classification.md`。

本报告不以其作为设计前提；涉及候选规则的推荐一律使用条件式表述：“若业务最终确认 X，则方案 A 能较好支持该要求。”

### 6.3 假设与未知（ASSUMPTION / UNKNOWN）

- A-1 ~ A-8：行级分批、汇率日期、税费净额、手工税码、草稿发票、缺伙伴禁止开票、发票回写、本位币展示等均为 ASSUMPTION；A-1 已由 B-24 确认、A-2 对账单折算已由 B-23 替代、A-3 已由 B-25 确认。
- Sprint3-002 开放项已全部确认（U-01 ~ U-32 → B-23 ~ B-38），详见第 13 节。

---

## 7. 代码与认知资产冲突

| 认知资产 | 声明 | 代码现状 | 冲突 |
|---|---|---|---|
| BR-01 | 成本 = vendor 服务行账单金额 | `action_create_vendor_bill` 为遗留创建路径，供应商账单实际由供应商开具原件 | 已确认不适用当前流程，TD-001 标记延期 |
| BR-02 | 费用行指定开票对象 | 自动生成行部分无对象 | 冲突（TD-015） |
| BR-03 | 本位币人民币，允许外币 | out_invoice 的 `amount_total_signed` 已折算本位币（运行时确认）；供应商账单按原币登记 | TD-002 表述需复核 |
| BR-12 | 税率/税额/含税可手改、费用类型默认税率 | 无税率字段、无 charge category | 缺失（TD-008） |
| B-15 ~ B-22 | 对账单/版本/分批开票/调整/币种口径（候选） | 无对账单模型 | 结构性缺失 |
| BR-15 ~ BR-22 | 候选规则 | 未登记、未确认 | 认知资产滞后 |
| U-01 | 费用行分批开票未知 | 已确认：费用行整行进一张发票（B-24）；B-17 仍为候选规则 | 已解决 |
| forbidden_change.yaml | 保护 `freight.service.sale/cost/currency_id` 等 | 未来只能新增字段，不能改写既有口径 | 约束 |
| audit_spec.yaml | 全链路审计 | 无对账单审计实体 | 缺失 |
| module_map.md | 计费层 → 结算层 | 无对账中间层 | 目标结构差异 |

---

## 8. Gap Matrix

| 业务要求 | 当前代码 | 差距 | 风险 | 建议 |
|---|---|---|---|---|
| 费用录入 | 手工 + 自动生成，可增删改 | 无税率/成本口径、无锁定 | 高 | 补充税字段与来源对象 |
| 对账单 | 无 | 缺失中间层 | 高 | 候选：新增 freight.statement |
| 客户异议 | 无 | 缺失 | 高 | 已确认：客户拒绝 → 结算单作废，费用释放回费用层（B-36/B-40） |
| 版本快照 | 无 | 缺失 | 高 | 候选：immutable version 链 |
| 客户确认 | 无 | 缺失 | 高 | 候选：confirmed 状态 + 模型级锁定 |
| 费用锁定 | 仅视图 readonly | 模型无强制 | 中 | 候选：模型 write 校验 |
| 发票生成 | 直接 account.move，多入口 | 需收敛到对账单 | 高 | 候选：statement 驱动开票 |
| 发票追溯 | 仅 header 级 freight_operation_id | 无对账单关联 | 高 | 已确认：header 级 statement ↔ invoice 关联（B-38），不做 line 级关联 |
| Credit Note | account 标准 out_refund 可用 | 无绑定流程 | 中 | 候选：基于已开票 statement line |
| 审计日志 | 无 statement 审计 | 缺失 | 中 | 版本快照与操作审计分开建设，不可互相替代 |
| PDF 对账单 | 无 statement 报表 | 缺失 | 中 | 已确认：以 docs/reports/应收对账单原始单据.md 为需求输入（B-27） |

---

## 9. 旧开票逻辑依赖

| 旧能力 | 依赖方 | 当前判断 | 候选方案 | 状态 |
|---|---|---|---|---|
| `action_create_invoice` | 货单表单按钮 | 高风险绕过入口，Sprint4 必须处理 | 隐藏，保留方法与兼容调用能力 | 已确认（B-30） |
| `action_create_vendor_bill` | 供应商账单链路 | 供应商账单入口 | 沿用旧链路，供应商成本不入客户对账单 | 已确认（B-35） |
| 列表 Server Action 两个 | 无有效依赖（TD-006） | 高风险遗留入口 | 随 Sprint4 收敛，按隐藏策略处理 | 已确认（B-30） |
| `button_customer_invoices / button_vendor_bills` | 查看发票 | 查看入口 | 保留 | 保留兼容 |
| Invoicing 菜单 | 查看/管理 | 查看入口 | 保留；标准财务凭证创建入口不收敛 | 已确认（B-29） |
| `shipment.invoice` 向导 | 无入口（TD-007） | 死代码 | 保留兼容不挂接 | 保留兼容 |
| `freight.multiple.invoice` | 遗留记录 | 遗留表 | 不删除，新流程不再写入 | 保留兼容 |
| `freight.service.customer_invoice / vendor_invoice` | 字段存在但未回填 | 遗留字段 | 新流程回填或废弃待定 | 保留兼容 |
| 标准 Accounting 创建入口 | account 模块 | 潜在绕过入口 | 当前不纳入收敛，Sprint4 只收敛 tk_freight 业务入口 | 已确认（B-29） |

---

## 10. 对账单设计候选方案

### 10.0 目标业务工作流（已确认）

```text
录入费用（freight.service）
   ↓
【向导】列表勾选费用行 → 生成结算单（Statement Draft，B-39）
   ↓
客户核对
   ├─ 拒绝 → 作废结算单 → 费用释放为可修改（B-36）
   │         ↓
   │        修改费用 → 【向导】重新勾选 → 生成新结算单
   │
   └─ 接受（B-33）
            ↓
       （开票申请：暂不设置开发任务）
            ↓
       生成草稿发票（account.move draft，A-5）
```

- **核心规则**：客户拒绝不是在原结算单上进入 dispute 后继续修改，而是作废当前结算单、回货运单修改费用、重新生成新结算单。
- 客户拒绝后原结算单作废，费用行释放为可修改（B-36 已确认）。
- 修改费用后重新通过向导生成新结算单并重新提交客户（B-37 版本化已确认）。
- 客户接受后生成 Odoo 草稿发票（A-5 假设，标准 draft move）。
- 开票申请环节当前不设置开发任务，Sprint4 不实现；如需审批再单独立项。

`PROPOSAL / NON-BINDING` 以下设计候选方案不构成已确认架构。

### 方案 A：新增 `freight.statement` + `freight.statement.line`

- statement：`freight_operation_id`、`customer_id`、`state`、`version_no`、`revision_of`、确认时间、本币/原币汇总。
- line：`freight_service_id`、`product_id`、`qty`、`untaxed/tax/total`、`billed_amount`、版本归属。
- 保留 `freight.service` 作为费用登记层，不对既有字段做破坏性改写。
- 生成入口：transient wizard，列表勾选 `freight.service` 行生成 statement（B-39 已确认）。

### 方案 B：直接给 `freight.service` 加状态字段

- 优点：改动小。
- 缺点：费用行可拆分/合并/版本化，单一登记模型难以表达不可变快照。

### 推荐（条件式）

`PROPOSAL` **若**业务最终确认客户唯一键（B-15 候选）、不可变版本链（B-16 候选）、行级分批开票（B-17 候选）、仅客户对账单（B-20 候选）等候选规则，**则**方案 A 能较好支持这些要求；若确认其他口径，需重新评估。本推荐不构成对候选规则的确认。

---

## 11. 版本快照/确认/调整/追溯设计候选方案

`PROPOSAL / NON-BINDING`

### 11.0 事实边界

- 已确认事实：当前系统不存在对账单中间层。
- 候选设计：draft 状态是否实时同步 `freight.service`。
- 已确认：confirmed 后强制版本化（B-37）；客户 reject 的对账单作废并释放费用（B-36）；不需要调整审批角色（B-34）。

### 11.1 版本快照

候选方案：

1. 业务主单：`freight.statement`（版本链根）；当前有效版本 = 同业务键 `version_no` 最大记录。
2. 不可变快照：每个版本一条 statement 记录，行数据存 `freight.statement.line`；旧版本通过模型层 `write()` 保护 + 视图只读双保险。
3. 触发时机：draft 为费用快照，费用修改回 freight.shipment / freight.service（B-40）；confirmed 后强制重新生成新版本（B-37 已确认）。
4. 历史查询：`revision_of / version_no` 版本链 + statement 搜索。
5. 打印指定版本：版本独立参数化报表（格式以 docs/reports/应收对账单原始单据.md 为输入，B-27 已确认）。

**重要边界：业务版本快照 ≠ 审计日志。**

- Statement Version：记录“当时客户看到/确认的业务内容是什么”。
- Audit Log：记录“谁、什么时候、做了什么操作”。
- 两者解决不同问题，不可互相替代；本报告不把版本快照当作审计日志。

### 11.2 确认后调整

已确认流程（B-34 / B-37）：

```text
Confirmed / Partially Invoiced / Invoiced
  ↓ 发现费用错误
生成新 Statement Version（旧版本不可变）
  ↓
重新确认
  ↓
如已开票：先 out_refund / Credit Note（候选规则 B-18），再关联新版本
```

- 不需要调整申请/审批角色流程（B-34 已确认）。
- confirmed 后任何变更强制生成新版本，原版本不可原地修改（B-37 已确认）。
- 已开票后调整通过 out_refund / Credit Note（B-18 候选），再关联新版本。

### 11.3 发票来源与追溯

已确认追溯（B-38：仅 header 级关联）：

```text
Shipment
   ↓
Statement（header）
   ↓
Invoice（header 关联 statement + freight_operation_id）
```

- 不建立 `Statement Line ↔ Invoice Line` 行级关联（B-38 已确认）。
- 费用行整行开票（B-24 已确认）：同一费用行整行进一张发票。
- 候选来源约束：仅客户确认后的对账单可开票（B-33 已确认）；partner、currency、单价、税率来自 statement line；“业务来源锁定”，金额/税务由 account 标准机制管理，不锁死 `account.move.line`。
- 币种：明细行允许本币/原币，按币种分别汇总（B-21 候选）；对账单折算默认取当前汇率，允许用户录入结算汇率覆盖（B-23 已确认）；每日汇率自动更新缺失已登记 TD-026（首选 Frankfurter/ECB，备选 ExchangeRate-API）；运行时证据显示现系统曾用 2026-08-10 汇率折算 2026-03-19 发票，Sprint4 需按 B-23 口径实现。
- 税费：服务/产品档案新增税目编码、税目名称字段（B-26 已确认）；税率/税额/含税/不含税可手工调整，`tax_amount` 为权威字段（B-19 候选）；运行时确认当前 `account.tax` / `product.product` / `product.template` 均无“税目编码/税目名称”字段，Sprint4 需新增字段。

---

## 12. 风险清单

| ID | 风险 | 等级 |
|---|---|---|
| R1 | 多入口绕过新流程（直接按钮、server action、标准 account 菜单） | 高 |
| R2 | 重复开票 / 无幂等（TD-009） | 高 |
| R3 | 多币种汇总失真（TD-002） | 高 |
| R4 | 成本口径失真（TD-001） | 高 |
| R5 | 税费链路缺失（TD-008） | 高 |
| R6 | 已开票费用行无追溯，作废/红冲不回滚（TD-003） | 高 |
| R7 | portal 写权限过宽（TD-019） | 中 |
| R8 | 历史数据不迁移（B-32 已确认），旧发票无 statement 关联为接受现状 | 中 |
| R9 | 并发开票超额，需事务级校验 | 高 |
| R10 | 角色/审批流程当前不建设（B-28/B-34 已确认），portal 现状保留 | 中 |
| R11 | 版本模型被错误实现为 audit log | 高 |
| R12 | PDF 对账单以 docs/reports/应收对账单原始单据.md 为输入（B-27 已确认）；其他报表不在当前范围 | 中 |
| R13 | 候选规则 B-15 ~ B-22 与设计建议被误当已确认基线 | 高 |
| R14 | 标准 Accounting 创建入口不纳入收敛（B-29 已确认），为接受范围 | 中 |
| R15 | 新增对账单字段若直接使用 `statement_id` / `statement_line_id` 会与 Odoo 标准银行流水字段冲突（运行时确认存在同名标准字段） | 高 |

---

## 13. 开放项确认结果（原 UNKNOWN 清单）

| 原 UNKNOWN | 确认决策 | 结论 |
|---|---|---|
| U-01 | B-24 | 费用行整行进一张发票，禁止行内分批/部分开票 |
| U-02 | B-23 | 对账单折算默认取当前汇率，允许用户录入结算汇率覆盖 |
| U-03 | B-25 | 利润公式中税费净额 = 销项税 − 进项税 |
| U-04 | B-26 | 服务/产品档案新增税目编码、税目名称；手工调整税额按 tax_amount 权威落账 |
| U-05 | B-27 | PDF 对账单以 docs/reports/应收对账单原始单据.md 为输入 |
| U-06 | B-28 | 当前不建设角色权限与 portal 收敛，保持现状 |
| U-23 | B-29 | 标准 Accounting 创建入口不纳入收敛，Sprint4 只收敛 tk_freight 业务入口 |
| U-24 | B-30 | 旧开票入口隐藏，保留方法与兼容调用能力 |
| U-25 | B-31 | Statement 编号：STM/年月/4位流水码 |
| U-26 | B-32 | 历史数据不迁移，对账单从新数据开始 |
| U-27 | B-33 | 自动生成费用行通过对账单状态管理，客户确认后生成发票 |
| U-28 | B-34 | 不需要调整申请/审批角色流程 |
| U-29 | B-35 | 供应商成本行排除在客户对账单外 |
| U-30 | B-36 | 客户 reject 的对账单作废，释放费用为可修改状态 |
| U-31 | B-37 | confirmed 后强制版本化，已确认版本不可原地修改 |
| U-32 | B-38 | 不建立 Statement Line ↔ Invoice Line 行级关联，仅 header 级关联 |

> Sprint3-002 全部开放项已由业务负责人确认（B-23 ~ B-38），并补充确认生成结算单向导（B-39）；Sprint4 实施契约按 B-23 ~ B-39 修订。

---

## 14. 推荐 Sprint 实施方案

`PROPOSAL / NON-BINDING`

> 该分 Sprint 方案仅作为实施规划候选，不构成 Sprint4 Intent 的 scope、acceptance criteria 或技术约束。

- **Sprint3（当前）**：现状分析完成（本报告）→ 开放项已全部确认（B-23 ~ B-39）→ 可进入 Sprint4 Intent 修订。
- **Sprint4（已暂存实施契约）**：候选实施阶段：
  1. P0 基础层候选：`freight.service` 增加税率/税额/含税/本币原币字段；服务/产品档案新增税目编码、税目名称（B-26）；自动生成费用行补开票对象（TD-015）。
  2. P1 对账单层候选：`freight.statement` + line + 版本链 + draft/voided/confirmed/draft_invoice + 模型级锁定；生成结算单 wizard（列表勾选费用行，B-39）；编号 STM/年月/4位流水码（B-31）。
  3. P2 开票层候选：客户接受后生成草稿应收发票；statement 驱动草稿发票 + 幂等校验；header 级关联（B-38），不做 line 级追溯；开票申请环节暂不设置开发任务。
  4. P3 调整层（后续 Sprint，不在本 Sprint）：out_refund / Credit Note + 新版本（B-37）+ adjusted 终态；无需审批角色（B-34）。
  5. P4 收敛与报表候选：旧 UI 入口隐藏（B-30）、ACL、PDF 对账单（B-27）；标准 Accounting 入口不收敛（B-29）、权限当前不建设（B-28）。
- 每步为 LEVEL3+ 风险，按 `human_loop.yaml` GATE3 人工卡点审批，禁止跳步。

---

## 附：本阶段变更说明

- 本报告不包含任何业务代码/模型/视图/权限/数据库修改。
- 已按用户指令完成“Sprint3 实施契约暂存为 Sprint4”的归档（`INT-FREIGHT-SPRINT4-001`、决策21、context_version）。
- 本报告中的设计建议均为候选方案（PROPOSAL / NON-BINDING），未写入 `business_rules.yaml` 或 `architecture/module_map.md`；候选规则 B-15 ~ B-22 不作为设计前提。
- 下一步：按第 13 节 B-23 ~ B-38 修订 Sprint4 Intent，进入 Business Rule Confirmation 与实施契约。
