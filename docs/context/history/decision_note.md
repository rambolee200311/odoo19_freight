# Decision Note — 决策笔记

## Sprint0: 上下文基线建设

**契约**: INT-FREIGHT-SPRINT0-001
**时间**: 2026-08-11

### 决策1：项目认知资产体系沿用 odoo18_tms 框架

**背景**: `docs/context` 原为 odoo18_tms 残留资产，与本项目不符。

**决策**: 整体替换为 `odoo19_freight / tk_freight` 版本，保留参考项目的目录结构与引擎命名（`execution/scripts`），内容全部按本项目重写。

### 决策2：业务口径固化

**决策**: 收入/成本/币种/税费/开票/收付款/利润/状态/兼容 9 条口径登记为业务铁律，写入 `business/freight_rule.md`，后续改动必须先更新决策笔记。

### 决策3：财务联动采用 Odoo account 标准模型

**决策**: 发票/账单使用 `account.move`，收付款使用 `account.payment` 登记，不做复杂核销；利润公式为“含税收入 − 含税成本 − 税费净额”。

### 决策4：技术债集中登记

**决策**: 所有已知问题统一登记到 `mymodules/tk_freight/docs/technical_debt.md`（TD-001 ~ TD-025），`docs/context/business/business_debt_register.md` 只保留与业务口径强相关的摘要。

### 决策5：兼容保留策略

**决策**: 遗留字段、`shipment.invoice` 向导、deprecated 方法保留兼容不删除；`commit_guard.py` 不自动 `git add .`、不默认 push。

### 决策6：汇率与利润微调口径

**决策**: 默认“收入/成本按单据日汇率、收付款按登记日汇率”折算；利润按“含税收入 − 含税成本 − 税费净额”。若业务后续调整，先更新本决策再改代码。

### 决策7：模块升级铁律

**决策**: 模块升级一律用常驻方式启动 Odoo，通过 XML-RPC 调用 `button_immediate_upgrade` 升级；升级失败必须检查 `debug_logs/odoo_190.log`；禁止仅用 `-u --stop-after-init` 作为最终验证。同步改造 `odoo_check.py` 与 `odo-validate-loop` 技能。

### 决策8：事实与推测分类基线

**决策**: 建立 `business/knowledge_classification.md`，对业务知识统一标注 CODE_FACT / BUSINESS_FACT / DECISION / CONSTRAINT / TECHNICAL_DEBT / UNKNOWN / ASSUMPTION；决策6 中的汇率与利润默认口径标记为 ASSUMPTION / NEEDS_CONFIRMATION，不再作为已确认事实表述。
