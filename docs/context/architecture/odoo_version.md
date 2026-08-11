# Odoo 版本与项目基线

## 当前版本

- Odoo 19 Community Edition，项目源码位于 `./odoo`
- 项目根目录：`/Users/lijianqiang/Documents/odoo19_freight`
- 自定义模块：`mymodules/tk_freight`（manifest version 2.1.0）
- 本地运行配置：`odoo.conf`（含敏感信息，不入库）
- 开发环境：`venv/`，Python 3.11

## 模块依赖

`base`、`contacts`、`account`、`product`、`sale_management`、`stock`、`fleet`、`crm`、`website`、`portal`、`hr`、`mail`、`board`、`calendar`、`base_setup`、`web`

## 项目内约定（现状核查）

- 列表视图使用 `<list>`，不新增 `<tree>`。
- 状态字段使用 `widget="badge"` 与 `decoration-*`。
- 不新增 `attrs=` / `states=` 等已弃用属性。
- 金额字段优先 `Monetary` + `currency_id`，本位币人民币。
- 遗留问题（`foce_Save`、`placeholer`、Odoo19 兼容风险）登记在 `mymodules/tk_freight/docs/technical_debt.md`。

## 开发规则

- 不阅读、不解析、不跟进 Odoo 官方源码，只围绕 `tk_freight` 自定义代码与业务文档工作。
- 禁止修改 `./odoo` 与 `./addons`。
- 所有改动聚焦 tk_freight 业务：出口货代报价、订舱、货运单全生命周期、收入/成本/应收/应付核算与对账。
