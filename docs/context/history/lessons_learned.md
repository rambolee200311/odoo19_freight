# Sprint4-4-4 Wizard 复盘教训（2026-08-14）

## 1. 背景

Sprint4-4-3 及后续 wizard 修复连续多轮被业务负责人打回：用户在真实页面上点击 Create Statement 反复遇到“列表为空 / 勾选失效 / 报错”等问题，而每次服务端断言都显示“通过”。本轮复盘以实际代码执行路径和真实数据库状态为准，定位根因并沉淀教训。

## 2. 根因

网页端会把 wizard 的 One2many 瞬态行按客户端本地数据重建，重建时丢失 `service_id`（例如 wizard 72：`selected_service_ids=[1,2,3,35]` 残留 CAT320D2，而行记录全部 `service_id=False`）。修复方向长期停在“生成逻辑/选择控件”上打补丁，而不是先钉死：

1. wizard 行与 `freight.service` 的绑定关系（`service_id` 创建即绑定、视图层保留关联）。
2. 选择态（`select`）的生命周期与重置语义。
3. 费用被 Statement 占用的唯一事实来源（`fee_state` 权威，statement 引用仅作迁移触发/防御）。

## 3. 主要错误

- **谎报验证**：反复以 odoo shell 服务端断言冒充“测试通过”，没有真实浏览器点击验证；对用户来说等于没有测试。
- **改错层**：把“网页端丢关联”当成“生成方法问题”修，多次改 `action_generate_statement`，未动真正病灶（wizard 生命周期）。
- **引入反模式**：用 `name+qty+price` 猜测 `service_id`，属于数据关联上的错误设计。
- **方案反复横跳**：checkbox → 行内按钮 → Many2many tags → checkbox + m2m 同步 → 猜测恢复，未停下来先确认设计。
- **把“门禁通过”当“问题解决”**：`verify.py` 与 shell 断言不覆盖网页端表单行为，通过它们给不了用户信心。

## 4. 教训

- 先复现再动手：用户报错时，第一件事是查看真实 UI 留下的数据库状态与页面现象，而不是继续猜。
- 只宣称验证过的东西：服务端断言写“服务端已验证”；浏览器点击验证完成前禁止说“测试通过”。
- 数据契约先于代码：One2many 行关联、默认勾选态、占用事实来源必须在契约层定死再编码。
- 同一症状反复出现三次，必须停止编码、重新定位根因并重审契约，而不是继续打补丁。

## 5. 修正动作

- Sprint4-4-4 契约登记 B-61~B-69：`service_id` 创建即绑定、禁止猜测恢复、select 生命周期明确、selectable 强制校验、锁后全量 eligible 重校验、eligibility 单一引擎、默认全选（U-45 → B-69）。
- 验收要求加入“真实浏览器点击”作为硬性条件，禁止 shell 断言冒充端到端测试。
- 将本复盘注入 `governance/test_lessons.yaml`（TL-FREIGHT-006~008），后续每次 `context_loader.py` 加载都会提示。

## 6. 关联资产

- Intent: `docs/context/intent/intent_sprint4_4_4_wizard_refactor.yaml`
- 决策: `docs/context/history/decision_note.md`（决策61/62）
- 教训规则: `docs/context/governance/test_lessons.yaml`

## 7. 过渡方案（2026-08-14 二次复盘，后被第 8 节替代）

同日下午曾把向导改为**彻底放弃 One2many 行勾选**：

- `freight.statement.wizard` 仅保留 `selected_service_ids`（`freight.service` Many2many）与 `eligible_service_domain` 计算域；视图使用原生 `many2many_checkboxes`，勾选列表直接写 Many2many，不经过 One2many。
- 生成结算单直接读 `selected_service_ids`，用户选几条就生成几条。
- 删除 `line_ids` 勾选、`write()` 命令守卫、`selectable` / `_rebuild_lines`。
- 服务端实测：选客户 7 后只勾 `场站费 800`，生成 `STM/202608/0041` 仅 1 行；作废后费用回 `confirmed`。

最终教训：wizard 多选状态必须直接挂在真实业务对象上（Many2many），不要在瞬态行 checkbox 上模拟选择状态，更不要写命令解析守卫去猜网页端行为。

## 8. 最终轮次复盘（2026-08-14 三次复盘）

从 Sprint4-4-3 到最终验收，“用户勾选哪几行就生成哪几行”这一需求共经历 4 种方案、至少 11 次用户可见失败/打回：

| # | 方案/现象 | 失败原因 |
|---|-----------|----------|
| 1 | One2many checkbox 列表为空 | eligible 口径/数据客户不对，且依赖网页端行重建 |
| 2 | checkbox 一点就打开行表单 | 非编辑列表的 checkbox 行为 |
| 3 | 行内按钮取消勾选无效 | 又回到同步猜测 |
| 4 | editable 列表产生无 service_id 空行 | 网页端重建行丢 service_id |
| 5 | “no freight service” 报错 | 生成读取行快照而非真实费用 |
| 6 | “CAT320D2 no longer eligible” | 选择状态与占用校验脱节 |
| 7 | 只选 1 条生成 3 条 | write 守卫把网页端重建当结构变更并重置全选 |
| 8 | 修完还是 3 条 | 只改磁盘没升级模块/重启 |
| 9 | 修完还是 3 条 | `_rebuild_lines` 的 `(5,0,0)` 递归触发守卫 |
| 10 | Many2many tags 无表格 | 牺牲数量/单价/税率列，业务不接受 |
| 11 | many2many_checkboxes 仍无表格 | 仍是极简多选，不是表格 |

最终方案：保留 One2many 表格 + 默认不勾选 + `select_map` 保留选择 + `wizard_rebuild` 上下文防递归。服务端实测通过：默认 4 行不选，勾选 `场站费 800` 后重建仍保留，生成 `STM/202608/0042` 仅 1 行，作废后费用回 `confirmed`。

核心教训：
1. 先问“用户在界面上要看到什么”（表格列），再选技术机制；稳定但不可用的方案等于没做。
2. 不要在网页端 One2many 行重建上写命令守卫去猜；把“重建时保留用户选择”作为显式生命周期，用 `select_map` + 明确 rebuild 上下文。
3. shell 断言只是服务端验证；必须升级、重启、浏览器点击后才能宣称通过。
4. 方案反复横跳本身就是问题：每次换机制前应先固化 UI 需求与验收标准。

## 9. 参考纪律（2026-08-14 四次复盘）

8 小时耗时最根本的教训不是代码复杂，而是“没有先查参考就动手”：

- 项目内已有 `DeliveryOrderNewWizard` 简单 wizard 参考，未先查阅。
- Odoo 19 框架自带 `many2many_checkboxes` / `many2many_tags` 控件，源码就在本地 `addons/web/static/src/views/fields/`，未先搜索。
- 卡住后继续打补丁，而不是停下来查官方文档、社区示例或框架源码。

规则（TL-FREIGHT-011）：实现不熟悉的 UI 交互前，必须先搜索框架源码与项目内已有实现作为参考，再定机制；禁止直接凭假设写代码并在失败后继续打补丁。
