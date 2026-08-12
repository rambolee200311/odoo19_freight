# 模块架构地图（tk_freight）

## 1. 模块组织

业务模块位于 `mymodules/tk_freight/`，遵循标准 Odoo 模块结构。

```text
mymodules/tk_freight/
├── __init__.py
├── __manifest__.py
├── controllers/main.py              # 门户/官网订舱与查询
├── models/                          # 全部业务模型
├── wizard/shipment_invoice.py       # 遗留向导（保留兼容，不挂接）
├── data/                            # 序列、阶段、基础数据、邮件模板
├── views/                           # 表单/列表/看板/菜单/设置
├── report/                          # BL/AWB/CMR/Waybill/报价/订舱等 QWeb 报表
├── security/                        # ACL + ir.rule
├── static/                          # 前端资源与仪表盘
├── i18n/                            # 多语言，含 zh_CN
└── docs/technical_debt.md           # 技术债登记
```

## 2. 单据层次

| 层 | 模型 | 说明 |
|---|---|---|
| 上游 | `crm.lead`、`shipment.quotation` | 线索、报价 |
| 中游 | `shipment.freight.booking` | 订舱 |
| 下游 | `freight.shipment`、`freight.route`、`shipment.package.line`、`shipment.item` | 货单及承运明细 |
| 计费 | `freight.service` | 收入/成本费用行 |
| 结算 | `freight.statement`、`freight.statement.line` | 客户结算单（draft → voided / confirmed → draft_invoice，版本链） |
| 开票 | `account.move`（out/in）、`account.payment`、`freight.multiple.invoice` | 发票/账单/收付款登记（发票 header 关联 `freight_statement_id`，B-38） |
| 基础资料 | `freight.port`、`freight.vessel`、`freight.airline`、`freight.package`、`freight.incoterms`、`freight.move.type`、`certificate.type`、`shipment.location`、`tracking.template` 等 | 主数据 |

## 3. 主流程

```text
CRM/门户 → 报价 → 订舱 → 货单 → 服务费 → 结算单（wizard 勾选费用行）→ 客户确认/作废 → 草稿应收发票/供应商账单 → 收付款登记 → 货单账务汇总与利润
```

## 4. 分层约束

- 业务字段只加在 tk_freight 模型；官方模型只做最小继承（`account.move`、`sale.order`、`stock.picking`、`res.partner`）。
- 财务联动必须走 `account` 标准模型与 API，禁止绕过 ORM。
- 结算单为不可变快照：draft 仅允许税额/结算汇率元数据调整；voided/confirmed/draft_invoice 不可原地修改，变更走版本链重新生成。
- 门户只承担查询/询价能力；写权限收敛待角色权限方案确定后实施。
