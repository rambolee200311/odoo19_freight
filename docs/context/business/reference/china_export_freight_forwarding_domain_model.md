# 中国出口货代行业通用业务模型（Domain Reference）

```yaml
knowledge_type: DOMAIN_REFERENCE
authority: REFERENCE_ONLY
project_requirement: false
business_rule: false
development_instruction: false
forbidden_change_source: false
```

> 本文件描述中国出口货代行业的一般业务结构，仅作为领域知识参考，不代表 `odoo19_freight / tk_freight` 的已确认业务需求。
> 任何行业通用能力不得因为出现在本文件中而自动进入开发任务、业务规则、Forbidden Change 或 Technical Debt。

## 1. 用途与边界

- 用途：帮助 AI 理解中国出口货代行业的一般业务组织方式，避免把“代码现在怎么实现”误认为“行业业务本来就应该这样”。
- 边界：本文件不回答“tk_freight 应该做什么”，只回答“行业中通常有哪些业务能力、如何组织”。
- 判定：本文件与当前项目不一致时，只记录为 `DOMAIN_REFERENCE_DIFFERENCE`，不修改代码、不创建 Feature、不创建 Technical Debt、不自动创建业务规则。

## 2. 业务主体

行业常见参与方（名称因企业而异，不要求 tk_freight 使用相同模型名）：

- 出口货代企业（核心主体）
- 委托方/客户（直客或同行）
- 发货人（Shipper）
- 收货人（Consignee）
- 通知方（Notify Party）
- 船公司/航空公司
- 承运人/供应商（车队、仓库、报关行、港区）
- 港口/码头
- 报关行
- 仓库
- 保险机构
- 海外代理
- 结算对手方（客户、供应商、代理）

## 3. 核心业务链

行业典型流程（参考，不代表当前项目必须全部实现）：

```text
客户询价/委托
→ 报价
→ 客户确认
→ 订舱
→ 委托/操作
→ 货物准备
→ 提货/进仓
→ 报关
→ 装船/起运
→ 提单/运输单证
→ 在途跟踪
→ 到港/目的地操作
→ 费用结算
→ 应收应付
→ 单票利润/对账
```

不同企业可能裁剪或调整顺序，例如无询价直接委托、先订舱后补报价等。

## 4. 核心业务对象

行业通常涉及以下对象（名称仅供参考）：

- Inquiry / 询价
- Quotation / 报价
- Booking / 订舱
- Shipment / 货运单
- Cargo / 货物
- Container / 集装箱
- Route / 路由
- Customs Declaration / 报关
- Transport / 运输
- Document / 单证
- Tracking / 跟踪
- Charge / 费用
- Customer Invoice / 应收
- Supplier Bill / 应付
- Settlement / 结算

## 5. 典型状态生命周期（行业参考）

示例（不得直接覆盖当前项目状态机）：

```text
Inquiry:
Draft → Sent → Quoted → Accepted / Rejected / Closed

Booking:
Draft → Submitted → Confirmed → Cancelled

Shipment:
Draft → Processing → Departed → In Transit → Arrived → Closed
```

行业不存在唯一标准状态集；当前项目状态以 `tk_freight` 代码与已确认口径为准。

## 6. 财务业务

行业通常存在以下财务概念：

- 收入
- 成本
- 应收
- 应付
- 多币种
- 汇率
- 税费
- 供应商费用
- 客户收费
- 对账
- 单票利润
- 毛利
- 结算

以上仅为行业参考，不得据此推导当前项目需求。

## 7. 单证

行业常见单证（不同运输模式和企业流程存在差异）：

- Booking Confirmation
- Bill of Lading
- Air Waybill
- Commercial Invoice
- Packing List
- Customs Declaration
- CMR
- Shipping Instruction
- Delivery Order

## 8. 运输模式

- 海运整箱 FCL
- 海运拼箱 LCL
- 空运
- 公路运输
- 多式联运

## 9. 行业常见业务变体

中国出口货代不存在唯一标准业务流程，常见变体包括：

- 直接订舱 vs 二代订舱
- 自营运输 vs 外包运输
- 客户指定船公司 vs 货代自主选择
- 直客 vs 同行
- 海运 vs 空运
- 自有报关团队 vs 外部报关行
- 单票结算 vs 月度结算

## 10. Domain Reference Boundary

```text
Industry Reference ≠ Project Requirement
Industry Reference ≠ Business Decision
Industry Reference ≠ Current Code Fact
Industry Reference ≠ Forbidden Change
```

## 11. 映射规则

```text
Industry Reference
        ↓
Project Confirmed Requirement
        ↓
Current Code Fact
        ↓
Coverage Assessment
```

- 行业能力只有在“当前项目业务需求被明确确认”后，才允许进入 `business/` 的项目权威业务上下文。
- 本文件永远保持 `REFERENCE_ONLY`。
- 行业能力与当前项目不一致时，只记录 `DOMAIN_REFERENCE_DIFFERENCE`，不产生任何开发动作。
