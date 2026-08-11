# tk_freight 技术债登记

- 模块：`mymodules/tk_freight`
- 版本：2.1.0（Odoo 19 Community Edition）
- 登记日期：2026-08-11
- 登记来源：tk_freight 现状梳理
- 状态定义：待处理 / 已确认 / 已修复 / 已延期
- 分类定义（严格区分，禁止混用）：
  - TECHNICAL_DEBT：当前实现不理想，不违反已确认业务规则
  - CONFIRMED_BUG：违反已确认业务规则，或明确代码缺陷（运行/拼写/逻辑错误）
  - MISSING_FEATURE：已确认需求但当前无实现
  - RISK：潜在风险，需业务确认
  - UNKNOWN：需求或语义未确认

## 1. 已确认业务口径

见 `docs/context/business/knowledge_classification.md`；本文档只登记技术债，不把债务写成业务规则。

## 2. P0 财务正确性

| ID | 分类 | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|---|
| TD-001 | Confirmed Bug | 成本字段未启用，应付按 sale 计算 | `action_create_vendor_bill` 使用 `data.sale`，成本与利润失真 | vendor 行按不含税成本生成账单 | 待处理 |
| TD-002 | Confirmed Bug | 多币种直接相加 | `_compute_total_amount` 累加 `amount_total_signed`，未折算人民币 | 逐票用 `res.currency._convert` 折算 | 待处理 |
| TD-003 | TECHNICAL_DEBT | 发票/账单与费用行无双向追溯 | 作废/红冲后 invoiced 不回滚 | 开票后回填发票行，account.move 状态联动 | 待处理 |
| TD-004 | Confirmed Bug | account.move 联动字段错误 | onchange 强制 partner；destination related 误指 source | 开票方法显式写 partner，修正 related | 待处理 |
| TD-005 | TECHNICAL_DEBT | 账务汇总不随发票状态刷新 | 计算依赖仅 freight_services，口径不一致 | 依赖发票行状态并显式刷新 | 待处理 |
| TD-006 | Confirmed Bug | 列表服务端动作缩进错误 | `ir_actions_server_freight_create_*` 必然 IndentationError | 修复缩进并复用统一开票方法 | 待处理 |
| TD-007 | TECHNICAL_DEBT | `shipment.invoice` 向导逻辑不可用 | 死代码，无入口 | 保留兼容，不挂接 | 已确认（延期） |
| TD-008 | MISSING_FEATURE | 税费链路缺失 | 已确认税率录入需求，但服务行无税率字段 | 新增税率/税额/含税字段，开票生成 account.tax | 待处理 |
| TD-009 | Confirmed Bug | 开票入口重复且部分缺关联 | 无幂等控制；部分入口不写 freight_operation_id | 统一按伙伴+币种分组生成发票 | 待处理 |

## 3. P1 业务流程

| ID | 分类 | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|---|
| TD-010 | Confirmed Bug | onchange 调用后不落库 | 地址字段不保存 | 改为计算字段或显式 write | 待处理 |
| TD-011 | Confirmed Bug | 计费重量比率类型错误 | 配置后计费重量计算报错 | float() 转换后使用 | 待处理 |
| TD-012 | Confirmed Bug | 合计与报关状态计算错误 | 删除箱货后合计残留；pass_state 最后一行决定 | 显式归零，pass_state 全行校验 | 待处理 |
| TD-013 | Confirmed Bug | 港口 code 唯一约束空值 bug | 空 code 触发重复校验 | 增加空值保护 | 待处理 |
| TD-014 | Risk | 路由生成拣货单类型疑似反向 | pickup/delivery 映射语义待确认 | 确认后修正类型映射 | 待处理 |
| TD-015 | TECHNICAL_DEBT | 自动生成的服务行无开票对象 | 包装/路由/保险费用无法开票 | 生成时要求归属伙伴 | 待处理 |
| TD-016 | Risk | 报价/订舱/货单转换校验不足 | 必填缺失、partner 副作用 | 按已确认口径补必填校验 | 待处理 |
| TD-017 | UNKNOWN | 货单序列按 transport 映射 operation | 语义未确认 | 保留现值，规则待业务确认 | 已确认（延期） |
| TD-018 | Confirmed Bug | 循环中误用 self | 多记录计数错误 | 改用 order.quotation_id/booking_id | 待处理 |

## 4. P2 安全、规范与残留

| ID | 分类 | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|---|
| TD-019 | Risk | 门户写权限过宽 | portal 可写业务模型 | 按后续权限方案收敛 | 已延期 |
| TD-020 | Unknown | 财务字段无权限收敛 | 角色权限未定 | 等角色方案确定 | 已延期 |
| TD-021 | Confirmed Bug | 视图拼写错误 | foce_Save、placeholer | 随视图改造修正 | 待处理 |
| TD-022 | Risk | 仪表盘统计口径不严谨 | 未过滤状态/公司/核销 | posted + 公司域过滤 | 待处理 |
| TD-023 | Unknown | 缺少财务报表 | 报表需求未定 | 需求确认后建设 | 已延期 |
| TD-024 | TECHNICAL_DEBT | 遗留死代码 | freight.js 未加载、compute_actual 无效 | 保留兼容，暂不清理 | 已确认（延期） |
| TD-025 | Risk | 仪表盘/搜索缺少公司过滤 | 多公司串数据 | 增加 company_id 过滤 | 待处理 |

## 5. 未决事项

1. 汇率折算日期（U-02）
2. 利润税费净税口径（U-03）
3. 手工税额开票方式（U-04）
4. 报表需求（U-05）
5. 角色权限（U-06）
6. 外部财务系统 U8C（U-07）

## 6. 建议修复顺序

1. P0：TD-001、TD-002、TD-003、TD-004、TD-005、TD-008、TD-009 与费用模型改造一起处理。
2. P1：TD-010、TD-011、TD-012、TD-013、TD-015、TD-018 随相关流程修复。
3. P2：TD-021、TD-022、TD-025 在视图/仪表盘改造时顺手修复。
4. TD-006 属立即修复项，可随任何一次模块升级处理。
5. 已延期项等待业务决策，不在当前范围。
