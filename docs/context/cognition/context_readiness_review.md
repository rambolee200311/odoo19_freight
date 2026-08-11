# tk_freight Context Readiness Review

## 1. Executive Summary

本次为独立最终验收，审查对象是 `odoo19_freight / tk_freight` Context Reconstruction 的“可被 AI 安全理解、验证和约束”能力。

结论：**NOT READY**。

- 项目身份主体已切换到 `odoo19_freight / tk_freight`，但 `docs/skills` 与部分引擎文件仍残留 `odoo18_tms / wd_tlms` 旧项目内容。
- 业务 Context 存在“把方案/推测写成已确认规则”的污染，且没有事实来源分类，AI 会被误导。
- 门禁引擎能执行并拦截一部分问题（旧模块名 `wd_tlms`、缺失版本基线、`<tree>` 等旧视图标签），但存在重大空转：View-Model 门禁实际不检查 tk_freight 模型；SQL 直写、`odoo18_tms` 残留、规则冲突、业务口径违规均无法自动发现。
- 沙箱内无法运行 `odoo shell` / `odoo_check.py`（psutil 进程枚举被沙箱拦截）；按铁律在宿主机执行 `odoo shell` 已验证：`tk_freight` installed `19.0.2.1.0`、`freight.shipment` 存在、记录数 1。
- 本次验收期间未修改业务功能、未修复技术债、未改变现有业务行为。

## 2. Project Identity Verification

全量搜索 `odoo18_tms / wd_tlms / worlddepot / transport_logistics / tlmp. / pickup.plan / odoo18e_tms`：

| 位置 | 内容 | 分类 |
|---|---|---|
| `docs/context/context_version.yaml` | “替换 odoo18_tms 残留资产” | 合法历史引用（变更记录） |
| `docs/context/history/decision_note.md` | 决策1 沿用 odoo18_tms 框架 | 合法历史引用（决策溯源） |
| `docs/context/intent_records/.../decision.md` | 采用 odoo18_tms 同款框架 | 合法历史引用（决策溯源） |
| `docs/skills/odoo_shell_query.md` | odoo18_tms 路径、`tlmp.*` 模型、wd_tlms 外部 ID | 错误残留（会误导 AI） |
| `docs/skills/odo-validate-loop/SKILL.md` | `-u wd_tlms`、XML-RPC 升级 | 错误残留 |
| `execution/scripts/test_runner.py` | docstring “运行 wd_tlms” | 错误残留（代码已改 tk_freight） |
| `execution/scripts/verify.py` | 检查标签 “Odoo18 兼容” | 轻度残留（检查内容为 Odoo19 标签） |
| `docs/context/governance/check_view_fields.py` | 模型名按 `tlmp./transport./pickup./schedule./container.` 前缀过滤 | 功能残留（tk_freight 模型被跳过） |

结论：核心 Context 身份正确，但存在 3 类残留，不能判 GREEN。

## 3. Context Asset Audit

```text
Declared Assets   39（含 execution/scripts 5 个引擎）
Existing Assets   44（docs/context 38 + execution/scripts 5 + technical_debt.md 1）
Missing Assets    0
Incorrect Assets  2（governance/check_view_fields.py 旧模型过滤；finance_flow 把未实现字段写成口径）
Orphan Assets     3（prompt_template.md 未入 Map；check_view_fields.py 未入 Map；intent_records defect.yaml 为空壳）
```

核对方式：逐项对照 `cognition_asset_map.md` 与实际 `find` 结果，并抽查内容。

重要缺口：

- Map 未声明 `context_version.yaml`、`prompt_template.md`、`governance/check_view_fields.py`。
- Map 声明的资产全部存在，但 `check_view_fields.py` 内容与 tk_freight 架构不一致（旧前缀过滤）。
- `intent_records/.../defect.yaml` 为 `defects: []` 空壳，未标注 N/A。

## 4. Business Context Audit

已覆盖：业务边界、核心对象（报价/订舱/货单/服务费/发票账单）、主流程、9 条已确认口径、财务核算方向、技术债关联。

已确认业务事实（用户 2026-08-11 确认）：

1. 收入 = shipper + consignee 服务开票金额；成本 = vendor 服务账单金额。
2. 本位币人民币；允许外币报价/开票。
3. 费用行录入不含税单价 + 税率，税额/含税金额可手工修改；费用类型可配默认税率。
4. 开票时点由操作员决定。
5. 无网上银行；财务登记收付款，不做复杂核销。
6. 利润 = 已开票收入 − 已确认成本 − 税费。
7. 货单阶段不强制状态机；不做精细报价管理。
8. 报表需求、角色权限后续确定；遗留字段/向导/方法保留兼容。
9. 数据检查一律使用 `odoo shell`，非万不得已禁止直连数据库（2026-08-11 新铁律，已登记为 constraint）。

未覆盖/需确认：费用行是否允许分批开票、汇率折算日期、税费净额解释、手工税额开票机制、报表字段口径。

## 5. Fact / Assumption / Unknown Audit

发现 Context Pollution，逐项列出：

| # | Source | Current Statement | Why It Is Unsafe | Recommended Classification |
|---|---|---|---|---|
| P1 | `business/freight_rule.md` 口径2 | “一个费用行对应一张客户发票或一张供应商账单” | 用户只说“可分可合”，未确认禁止行级分批开票 | ASSUMPTION / NEEDS_CONFIRMATION |
| P2 | `business/freight_rule.md` 口径3 | “收入/成本按单据日期，收付款按登记日期” | 汇率日期未获业务确认 | ASSUMPTION / NEEDS_CONFIRMATION |
| P3 | `business/freight_rule.md` 口径5 | “生成 Odoo 草稿单据” | 用户只确认操作员决定开票时点，草稿机制是方案 | DECISION_PROPOSAL |
| P4 | `business/freight_rule.md` 口径7 | “税费净额（销项税 − 进项税）” | 是对“税费”的解释，用户未确认净税口径 | ASSUMPTION / NEEDS_CONFIRMATION |
| P5 | `business/freight_rule.md` 流程铁律 | “开票对象必须明确，缺少 partner 不得开票” | 是修复建议，不是用户确认的业务规定 | TECHNICAL_DEBT / PROPOSAL |
| P6 | `business/freight_rule.md` 流程铁律 | “发票/账单状态变化必须回写服务行与货单账务” | 当前代码未实现，是目标设计而非现状 | DECISION_PROPOSAL |
| P7 | `business/finance_flow.md` | `revenue_total/cost_total/tax_net/profit` 字段口径表 | 这些字段当前不存在，方案被写成现状 | DESIGN_PROPOSAL / CODE_FACT=False |
| P8 | `business/finance_flow.md` 税费规则 | “开票时使用定额税码保证单据一致” | 定额税码是方案默认，未获确认 | ASSUMPTION |
| P9 | `history/decision_note.md` 决策6 | 汇率/利润默认口径 | 已标注“若调整先更新”，但未标 NEEDS_CONFIRMATION | DECISION + ASSUMPTION |
| P10 | `business/freight_rule.md` 数据铁律 | “不在发票上随意改口径” | 属于操作约束建议，未确认 | CONSTRAINT_PROPOSAL |

结论：Context 没有机器可读的事实来源/状态字段（CODE_FACT / BUSINESS_FACT / DECISION / CONSTRAINT / TECHNICAL_DEBT / UNKNOWN / ASSUMPTION），无法自动区分“代码现在这样”和“业务规定必须这样”。

## 6. Forbidden Change Audit

`constraints/forbidden_change.yaml` 覆盖了：官方源码、官方源码阅读、视图/JS/Controller 直写 DB、模块边界、ORM 绕过、批量数据修改、业务口径变更、遗留兼容删除、未定需求实施、安全组删除、portal 权限、数据检查方式（新铁律）。

针对验收问题逐项回答：

1. 哪些文件禁止修改：`./odoo`、`./addons`，以及 tk_freight 之外的自定义模块。可自动验证程度：低（verify.py 未检查 git diff 路径）。
2. 哪些模型禁止修改：未列出具体模型清单。`account.move`、`freight.shipment` 等关键模型无 allow/deny 表。
3. 哪些字段禁止改变语义：未列出。账务字段、状态字段无保护清单。
4. 哪些状态值禁止改变：未列出。`draft/converted/cancel`、`q/qs/c`、服务状态等无清单。
5. 哪些业务行为禁止改变：口径 9 条在 business 资产中，但不是机器可验证格式。
6. 哪些接口契约禁止改变：未定义 `freight_operation_id`、`freight_id` 等契约。
7. 哪些变更必须先获得用户确认：仅“未定需求”笼统表述，无正式确认清单。
8. 哪些只是技术债而非禁止修改：TD-001 等应允许修复，约束文件未做区分。

无法程序化验证的条目（DOCUMENT_ONLY）：

- 禁止阅读官方源码（AI 行为，无法由 verify 验证）
- 禁止删除 security group / 调整 portal 权限（无 ACL 差异检查）
- 禁止改变业务口径（无规则对比器）
- 禁止修改未列出模型/字段/状态（无清单）
- 数据检查必须用 odoo shell（无 shell 调用审计）

可验证但当前未接入 verify.py：官方路径修改（git diff）、`cr.execute` 写库扫描、`odoo18_tms` 残留扫描、规则冲突检测。

## 7. Technical Debt Audit

`mymodules/tk_freight/docs/technical_debt.md` 与代码抽查一致：

- TD-001：`action_create_vendor_bill` 使用 `data.sale`（代码实证 `freight_shipment.py:830`）。
- TD-002：`_compute_total_amount` 直接累加 `amount_total_signed`（`freight_shipment.py:304/310`）。
- TD-006：`ir_actions_server_freight_create_*` 缩进错误（`freight_shipment_view.xml`）。
- TD-008：`freight.service` 无税率字段；向导写入非法状态 `quotation`（`shipment_invoice.py:47/78`）。
- TD-011：`ir.config_parameter` 返回字符串直接参与运算。
- TD-021：`foce_Save`、`placeholer`（`freight_quotation_view.xml:32`、`shipment_invoice_view.xml:11`）。

问题：

- 缺少“Known Debt / Risk / Confirmed Bug / Unknown”四类明确分类，部分条目状态为“已确认（延期）”实际是决策而非债务。
- 个别条目（TD-024/025）描述的是遗留/待定事项，不是可复现缺陷。
- 未把技术债转换成“待修复任务”，符合 Review 要求；本次也未修复任何技术债。

## 8. Executable Engine Audit

实际运行结果（`python3`，本项目 3.11）：

| Engine | Result | Evidence |
|---|---|---|
| `context_loader.py` | PASS exit 0 | 0.1.1，full profile 7 domain 全 PASS，Baseline PASS，READY |
| `verify.py` | PASS exit 0 | 8/8 PASS（Python/XML/首行空格/模块名/兼容/Tab/View-Model/Menuitem） |
| `commit_guard.py` | PASS exit 0 | Gate passed；提示 --commit/--push |
| `odoo_check.py` | FAIL exit 1 | 沙箱内无法完成 DB 连接验证 |
| `odoo shell`（宿主机） | PASS | TK_STATE=installed / TK_VERSION=19.0.2.1.0 / HAS_SHIPMENT=True / SHIPMENT_COUNT=1 |
| `odoo shell`（沙箱重试） | FAIL exit 1 | psutil `sysctl(KERN_PROC_ALL)` PermissionError，代码未执行 |

能力边界：

- `context_loader.py`：只检查资产目录存在性/文件数、版本与 Intent 绑定，不做语义校验；按 Profile 过滤（默认 infrastructure 只扫 3 个域）。
- `verify.py`：能做语法、旧标签、旧模块名（仅 `wd_tlms/transport_logistics_management`）、menuitem 顺序检查；但 View-Model 门禁调用 `check_view_fields.py` 因旧前缀过滤对 tk_freight 空转。
- `commit_guard.py`：仅包装 verify，无额外语义检查；设计上不自动 add/push（安全）。
- `odoo_check.py`：沙箱内无法完成（网络/进程权限），需宿主机执行。
- `odoo shell`：沙箱内被 psutil 权限拦截；宿主机已验证通过（DB 可用、tk_freight installed）。

## 9. Git Audit

```text
git status:
  M .gitignore
  D mymodules/tk_freight/docs/config.xml
  ?? .vscode/
  ?? docs/
  ?? execution/
  ?? mymodules/tk_freight/docs/technical_debt.md
```

- `docs/context`、`execution/scripts`、`technical_debt.md` 均未被 `.gitignore` 忽略（`git check-ignore` 无匹配），可纳入 Git。
- 敏感项已忽略：`odoo.conf`、`venv/`、`debug_logs/`、`.env`、`__pycache__`、`.DS_Store`。
- 当前尚未 `git add/commit`：用户要求“纳入 git”，但本次为 Review，未提交。
- `mymodules/tk_freight/docs/config.xml` 删除与 `.gitignore` 修改为用户既有变更，未触碰。
- `docs/skills` 残留旧项目内容，纳入 Git 前应清理。

## 10. Adversarial Tests

全部为临时探针，测试后已删除，业务代码未受影响。

| Test | Method | Result | Interpretation |
|---|---|---|---|
| 1a 旧项目污染 | 在 models 加 `odoo18_tms` 探针 | verify PASS | 未检测到旧项目名（Guard 盲区） |
| 1b 旧项目污染 | 探针改为 `wd_tlms` | verify FAIL (c4) | 能检测 `wd_tlms`，但不能检测 `odoo18_tms` |
| 2 业务规则污染 | 静态审查 | 发现 P1~P10 | 引擎无法识别 CODE_FACT vs BUSINESS_FACT，靠人工分类 |
| 3 禁止修改 | models 加 `cr.execute(UPDATE account_move ...)` 探针 | verify PASS | 无 SQL 直写门禁（DOCUMENT_ONLY） |
| 4 Context 缺失 | 临时移走 `context_version.yaml` | loader exit 3 BLOCKED；verify PASS | loader 能拦缺失，verify 无 Context 完整性检查 |
| 5 Context 冲突 | business 加“利润=收入+成本”冲突文件 | loader/verify PASS | 无规则冲突检测 |
| 6 未知事项 | 检查 provenance 元数据 | 不存在 | 系统无法区分“已确认/推测/未知” |

## 11. Findings

F1（严重）业务 Context 污染：方案与推测被写成已确认口径（P1~P10），无事实来源分类。
F2（严重）`check_view_fields.py` 按旧项目模型前缀过滤，View-Model 门禁对 tk_freight 空转。
F3（严重）引擎无法发现 `odoo18_tms` 残留、SQL 直写、规则冲突、业务口径违规；这些约束只能 DOCUMENT_ONLY。
F4（严重）沙箱内 `odoo shell` / `odoo_check.py` 被进程/网络权限拦截；宿主机 `odoo shell` 已验证模块已安装（19.0.2.1.0），但完整 `-u` 加载检查未在沙箱内完成。
F5（中）`docs/skills` 与引擎 docstring 残留旧项目内容。
F6（中）Asset Map 未声明 `context_version.yaml`、`prompt_template.md`、`check_view_fields.py`；存在空壳 intent defect.yaml。
F7（中）Forbidden Change 无模型/字段/状态/接口清单，无法形成可验证 Guard。
F8（中）Git 未纳入（docs/execution/technical_debt 未 add/commit），与“纳入 git”要求不符。

## 12. Required Fixes

进入 READY 前必须完成：

1. 业务 Context 重分类：为关键规则增加 provenance 标记（CODE_FACT / BUSINESS_FACT / DECISION / CONSTRAINT / TECHNICAL_DEBT / UNKNOWN / ASSUMPTION），新增 UNKNOWN / NEEDS_CONFIRMATION 登记；把 P1~P10 标注或移出“已确认口径”。
2. 修复项目身份残留：`docs/skills/odoo_shell_query.md`、`docs/skills/odo-validate-loop/SKILL.md`、`test_runner.py` docstring、`verify.py` 标签、`check_view_fields.py` 模型前缀过滤。
3. 强化 verify.py：增加 `odoo18_tms` 残留、`cr.execute` 写库、Context 完整性、规则冲突、官方路径 git diff 检查；无法机器验证的约束显式标注 DOCUMENT_ONLY。
4. Forbidden Change 增加机器可读清单：受保护模型、字段语义、状态值、接口契约、用户确认清单。
5. 修正 Asset Map：声明 `context_version.yaml`、`prompt_template.md`、`check_view_fields.py`；补 intent defect 记录或标 N/A。
6. Technical Debt 增加 Known Debt / Risk / Confirmed Bug / Unknown 分类，方案项与缺陷项分离。
7. Git：清理残留后 `git add docs/ execution/ mymodules/tk_freight/docs/technical_debt.md` 并提交（用户已确认纳入）。
8. 运行验证：宿主机 `odoo shell` 已通过（tk_freight installed 19.0.2.1.0，freight.shipment 存在，记录数 1）；完整 `-u` 模块加载检查为可选项，可在宿主机执行 `venv/bin/python3 execution/scripts/odoo_check.py`。
9. 更新 `validation/test_exec_records.yaml` 与本次验收结果。

## 13. Context Readiness Matrix

| Area | Status | Evidence |
|---|---|---|
| Project Identity | YELLOW | 主体已切换；skills/引擎残留旧项目 |
| Architecture Context | GREEN | module_map/dependency/odoo_version 与项目一致 |
| Business Context | RED | 方案/推测被写成已确认口径，无 UNKNOWN 分类 |
| Constraint Context | YELLOW | 约束存在，但多为 DOCUMENT_ONLY，无模型/字段/状态清单 |
| Historical Context | GREEN | 历史记录为本项目，旧项目仅为决策溯源 |
| Decision Context | YELLOW | 决策已记录，部分默认口径未标 NEEDS_CONFIRMATION |
| Technical Debt | YELLOW | 与代码一致，缺四类分类，方案项混入 |
| Unknowns | RED | 无 UNKNOWN / NEEDS_CONFIRMATION 登记 |
| Asset Map | YELLOW | 声明资产全存在；3 个 orphan/未声明项 |
| Context Version | GREEN | 0.1.1，loader 基线 PASS |
| Context Loader | YELLOW | 可用；只做存在性/数量/基线，不做语义 |
| Verify | YELLOW | 可拦截 wd_tlms/旧标签；View-Model 空转，缺多项 Guard |
| Commit Guard | YELLOW | 安全包装 verify；无附加语义检查 |
| Odoo Check | YELLOW | 沙箱内被 psutil 拦截；宿主机 odoo shell 已验证 DB 与模块安装；-u 检查未跑 |
| Git Integration | YELLOW | 内容未被忽略，但尚未 add/commit |

## 14. Final READY / NOT READY Decision

### Q1

> 完全没参与过项目的 Codex 仅依赖 docs/context 能否正确理解项目？

`PARTIAL`

证据：目录结构和已确认 9 条口径可读，但 P1~P10 会把“方案/推测”当“业务事实”，且 skills 残留会给出错误路径与模型；财务字段口径表引用了不存在的字段。

### Q2

> Codex 误解业务规则或试图修改禁止项时，Harness 能否阻止？

`PARTIAL`

证据：`context_loader` 可拦截版本基线缺失；`verify` 可拦截 `wd_tlms` 残留与旧视图标签（Test 1b/4）；但 Test 1a/3/5 证明 `odoo18_tms`、SQL 直写、规则冲突均无法拦截，Forbidden Change 语义无法自动验证。

### Q3

> 是否可以进入正常 Feature / Sprint 开发？

`NOT READY`

进入 READY 前必须完成第 12 节 Required Fixes 第 1~7、9 项；第 8 项运行时证据已通过宿主机 `odoo shell` 取得（`-u` 全量检查为可选项）。

---

审计日期：2026-08-11
审计方式：独立复核 + 实际引擎运行 + 六项对抗测试
审计范围：不修改业务功能、不修复技术债、不改业务行为

## 15. Post-Review Update (2026-08-11)

- 新增模块升级铁律并登记（context_version 0.1.3）：常驻启动 Odoo + XML-RPC `button_immediate_upgrade` 升级；升级失败必须检查 `debug_logs/odoo_190.log`；禁止仅用 `-u --stop-after-init` 作为最终验证。
- 同步改造 `execution/scripts/odoo_check.py`（XML-RPC 版）与 `docs/skills/odo-validate-loop/SKILL.md`，并清理 `docs/skills/odoo_shell_query.md` 旧项目残留。
- 补齐 TMS 执行侧参考（context_version 0.1.4）：新增根目录 `git_commit.sh` 发布门禁，结构对齐 odoo18_tms；本工作区沙箱 `.git` 只读且 `require_escalated` 策略为 never，发布门禁需宿主机执行或由用户调整权限后由 agent 执行。
- 上述登记不改变本报告第 1~14 节结论；进入 READY 的 Required Fixes 仍有效。
