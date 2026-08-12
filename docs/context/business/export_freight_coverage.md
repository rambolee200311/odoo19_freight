# 出口货代业务能力覆盖审计

## 1. 文档定位

```text
Document Type: Capability Coverage Audit
Knowledge Type: Mixed Reference
Primary Evidence: CODE_FACT
Business Requirement Source: business/knowledge_classification.md（B-*）
Not authoritative for business requirements
```

本文件回答：当前 tk_freight 代码能力，与已确认的出口货代业务能力相比，覆盖到什么程度。不承担业务需求定义职责。

## 2. 业务范围（BUSINESS_FACT）

来源：项目初始约束（用户 2026-08-11，见 B-12）。

- 客户主体：中国天津出口代理货代企业。
- 核心业务：出口货代报价管理、订舱流程、货运单全生命周期管理。
- 财务核心：货运单绑定收入、成本、应收账款、应付账款核算与对账。

## 3. 当前代码覆盖（CODE_FACT）

状态语义：

- `CODE_PRESENT`：代码存在，不证明业务完整。
- `FUNCTIONALLY_COVERED`：可完整支撑已确认业务能力（附证据）。
- `PARTIALLY_COVERED`：有实现但有缺口（附 TD/U）。
- `NOT_IMPLEMENTED`：无实现。

### 3.1 报价管理

| 能力 | Code Evidence | Code Status | Business Coverage | Source |
|---|---|---|---|---|
| 报价单 | `shipment.quotation` | PRESENT | CODE_PRESENT | CODE_FACT |
| 报价状态流转 | status: q/qs/c | PRESENT | PARTIALLY_COVERED（转换校验不足） | TD-016 |
| 报价行：服务/税/计费重量 | `quot.order.line` | PRESENT | PARTIALLY_COVERED（税额手算） | TD-008 |
| CRM 线索转报价 | `freight_crm.py` | PRESENT | PARTIALLY_COVERED（地址不落库） | TD-010 |
| 门户在线询价 | controllers + portal 模板 | PRESENT | CODE_PRESENT | CODE_FACT |
| 报价 PDF / 邮件 | report + mail templates | PRESENT | FUNCTIONALLY_COVERED | CODE_FACT |
| 价目表/标准费率/报价审批 | 无 | ABSENT | NOT_IMPLEMENTED（当前阶段决策不建设） | B-08 |
| 报价转订舱价格锁定 | 未发现实现 | ABSENT | UNKNOWN | U-05 |

### 3.2 订舱流程

| 能力 | Code Evidence | Code Status | Business Coverage | Source |
|---|---|---|---|---|
| 订舱单与状态 | `shipment.freight.booking`（draft/converted/cancel） | PRESENT | PARTIALLY_COVERED（取消校验不足） | TD-016 |
| 订舱行 | `booking.order.line` | PRESENT | PARTIALLY_COVERED（税额手算） | TD-008 |
| 订舱转货单 | `convert_to_operation` | PRESENT | PARTIALLY_COVERED（校验不足/地址不落库） | TD-016/TD-010 |
| 订舱单 PDF / 邮件 | `freight_booking_form.xml` | PRESENT | FUNCTIONALLY_COVERED | CODE_FACT |
| 门户在线订舱 | controllers + portal 模板 | PRESENT | CODE_PRESENT（写权限风险） | TD-019 |

### 3.3 货运单全生命周期

| 能力 | Code Evidence | Code Status | Business Coverage | Source |
|---|---|---|---|---|
| 货单主档/看板 | `freight.shipment` + stages | PRESENT | FUNCTIONALLY_COVERED（不强制状态机） | B-08 |
| 起运/目的地址 | freight.shipment 地址字段 | PRESENT | PARTIALLY_COVERED | TD-010 |
| 箱货/容器明细 | `shipment.package.line` / `shipment.item` | PRESENT | PARTIALLY_COVERED | TD-012 |
| 路由与仓库收发货 | `freight.route` + `stock.picking` | PRESENT | PARTIALLY_COVERED | TD-014 |
| 报关登记 | `custom.department` | PRESENT | PARTIALLY_COVERED | TD-012 |
| 保险 | freight.shipment 保险字段 + `policy.risk` | PRESENT | PARTIALLY_COVERED | TD-015 |
| 运输跟踪 | `tracking.template` / `shipment.tracking` | PRESENT | FUNCTIONALLY_COVERED | CODE_FACT |
| 单证报表（BL/AWB/CMR/Waybill 等） | report/*.xml | PRESENT | FUNCTIONALLY_COVERED | CODE_FACT |

### 3.4 财务核算与对账（核心重点）

| 能力 | Code Evidence | Code Status | Business Coverage | Source |
|---|---|---|---|---|
| 服务费行 sale/cost/币种/状态 | `freight.service` | PRESENT | PARTIALLY_COVERED | TD-001/TD-008 |
| 按客户/供应商/币种生成发票/账单 | `action_create_invoice` / `action_create_vendor_bill` | PRESENT | PARTIALLY_COVERED | TD-009 |
| 发票/账单关联货单 | `account.move.freight_operation_id` | PRESENT | PARTIALLY_COVERED | TD-003/TD-004 |
| 货单账务汇总页 | `_compute_total_amount` | PRESENT | PARTIALLY_COVERED | TD-002/TD-005 |
| 收付款登记接入货单 | 标准 `account.payment`，货单无入口 | ABSENT | NOT_IMPLEMENTED | MISSING_FEATURE |
| 对账/账龄/单票利润报表 | 无 | ABSENT | NOT_IMPLEMENTED（需求未确认） | UNKNOWN |

### 3.5 基础资料与门户

| 能力 | Code Evidence | Code Status | Business Coverage | Source |
|---|---|---|---|---|
| 港口/船/航司/车辆/包装/贸易术语/路由 | 基础资料模型 | PRESENT | FUNCTIONALLY_COVERED（港口 code 约束） | TD-013 |
| 伙伴角色 | `res.partner` 扩展 | PRESENT | FUNCTIONALLY_COVERED | CODE_FACT |
| 门户查询与公开跟踪 | controllers + portal 模板 | PRESENT | CODE_PRESENT（写权限风险） | TD-019 |
| 报表/权限角色 | 未定 | ABSENT | UNKNOWN | U-06 |

## 4. 已确认需求（BUSINESS_REQUIREMENT）

仅列已确认项，来源 `knowledge_classification.md`：

- B-01 收入/成本口径
- B-03 本位币人民币，允许外币
- B-04 不含税+税率录入、税额/含税可手改、费用类型默认税率
- B-05 开票时点操作员决定
- B-06 收付款登记、不做复杂核销
- B-07 利润公式
- B-08 不强制状态机；当前阶段不建设价目表/审批（范围=当前项目/当前阶段，未来可重新讨论）
- B-09 报表/权限后定，遗留兼容保留
- B-12 业务范围

## 5. 未确认需求（UNKNOWN）

- U-01 费用行分批开票
- U-02 汇率折算日期
- U-03 利润公式“税费”净税解释
- U-04 手工税额开票机制
- U-05 收付款登记货单入口、报价转订舱价格锁定
- U-06 报表需求、角色权限、门户写权限

## 6. 缺口总表（严格分类）

| 缺口 | 分类 | 关联 |
|---|---|---|
| 成本字段未启用，应付按 sale | CONFIRMED_BUG（违反 B-01） | TD-001 |
| 多币种未折算 | CONFIRMED_BUG（违反 B-03） | TD-002 |
| 发票/费用行无双向追溯 | TECHNICAL_DEBT | TD-003 |
| 税费链路缺失 | MISSING_FEATURE（违反 B-04） | TD-008 |
| 收付款登记未接入货单 | MISSING_FEATURE | U-05 |
| 对账/账龄/利润报表 | UNKNOWN（需求未确认） | U-06/TD-023 |
| 门户写权限过宽 | RISK | TD-019 |
| 报价转订舱价格锁定 | UNKNOWN | U-05 |

注意：未实现 ≠ Technical Debt。分类按上表严格区分。

## 7. 引用语义规范

```text
B-*  = Business Decision / 已确认业务事实（knowledge_classification.md）
TD-* = Technical Debt（technical_debt.md，含严格分类）
U-*  = Unknown / Unconfirmed（knowledge_classification.md）
CODE_FACT = 代码现状
```

## 8. 数据来源

```yaml
code_source:
  - current_repository
  - tk_freight models/controllers/views
business_source:
  - docs/context/business/knowledge_classification.md
decision_source:
  - B-08
technical_debt_source:
  - mymodules/tk_freight/docs/technical_debt.md
unknown_source:
  - knowledge_classification.md U-*
```

## 9. 与已确认口径的对应

- 已体现：操作员决定开票时点、多币种允许、费用行 sale/cost 字段、分客户/供应商开票。
- 未体现：成本启用、税率/税额字段、发票双向追溯、按本位币折算、利润字段。
- 未体现项按第 6 节分类（CONFIRMED_BUG / TECHNICAL_DEBT / MISSING_FEATURE / UNKNOWN），不一律视为技术债。
