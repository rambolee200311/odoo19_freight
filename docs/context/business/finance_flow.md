# 财务单据流与核算口径

## 单据流（CODE_FACT）

```text
freight.service (收入行: shipper/consignee，成本行: vendor)
        ↓ action_create_invoice / action_create_vendor_bill
account.move (out_invoice / in_invoice, draft → posted)
        ↓ account.payment.register（财务登记收付款）
account.payment → 核销 → 货单 accountancy 汇总
```

## 目标核算字段口径（DESIGN_PROPOSAL，当前代码未实现）

以下为方案设计，不是现状：

| 字段 | 目标口径 |
|---|---|
| revenue_total | 已过账 out_invoice 归属服务的含税金额，折算人民币 |
| cost_total | 已过账 in_invoice 归属服务的含税金额，折算人民币 |
| tax_net | 销项税 − 进项税（ASSUMPTION A-3） |
| profit | 含税收入 − 含税成本 − 税费净额 |
| invoice_residual / bills_residual | 已过账发票/账单未结余额，折算人民币 |
| invoice_paid_amount / bills_paid_amount | 含税合计 − 未结余额 |

## 已确认税费录入规则（BUSINESS_FACT）

- 费用行录入不含税单价、税率；自动计算税额与含税单价。
- 税额/含税金额可手工修改。
- 费用类型（`freight.charge.category`）可配置默认税率。
- 手工税额开票机制（定额税码）为 ASSUMPTION A-4，未确认。

## 关联技术债

- TD-001 成本未启用
- TD-002 多币种未折算
- TD-003 发票/费用行无双向追溯
- TD-004 account.move 联动字段错误
- TD-005 账务汇总不随发票状态刷新
- TD-008 税费链路缺失
- TD-009 开票入口重复/缺关联

详细清单与分类见 `mymodules/tk_freight/docs/technical_debt.md`。
