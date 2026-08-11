# 财务单据流与核算口径

## 单据流

```text
freight.service (收入行: shipper/consignee，成本行: vendor)
        ↓ action_create_invoice / action_create_vendor_bill
account.move (out_invoice / in_invoice, draft → posted)
        ↓ account.payment.register（财务登记收付款）
account.payment → 核销 → 货单 accountancy 汇总
```

## 货单核算字段口径

| 字段 | 口径 |
|---|---|
| revenue_total | 已过账 out_invoice 归属服务的含税金额，折算人民币 |
| cost_total | 已过账 in_invoice 归属服务的含税金额，折算人民币 |
| tax_net | 销项税 − 进项税 |
| profit | 含税收入 − 含税成本 − 税费净额 |
| invoice_residual / bills_residual | 已过账发票/账单未结余额，折算人民币 |
| invoice_paid_amount / bills_paid_amount | 含税合计 − 未结余额 |

## 税费规则

- 费用行录入不含税单价、税率；自动计算税额与含税单价。
- 用户可手工修改税额/含税金额；开票时若与按税率计算不一致，使用定额税码保证单据一致。
- 费用类型（`freight.charge.category`）可配置默认税率。

## 关联技术债

- TD-001 成本未启用
- TD-002 多币种未折算
- TD-003 发票/费用行无双向追溯
- TD-004 account.move 联动字段错误
- TD-005 账务汇总不随发票状态刷新
- TD-008 税费链路缺失
- TD-009 开票入口重复/缺关联

详细清单见 `mymodules/tk_freight/docs/technical_debt.md`。
