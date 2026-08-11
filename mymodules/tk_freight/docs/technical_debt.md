# tk_freight 技术债登记

- 模块：`mymodules/tk_freight`
- 版本：2.1.0（Odoo 19 Community Edition）
- 登记日期：2026-08-11
- 登记来源：tk_freight 现状梳理
- 状态定义：待处理 / 已确认 / 已修复 / 已延期

## 1. 已确认业务口径

以下口径于 2026-08-11 与业务方确认，后续修复和开发均以此为准：

1. 收入 = shipper + consignee 服务行的开票金额；成本 = vendor 服务行的账单金额。
2. 费用可分可合：按费用行指定开票对象，可多客户/多供应商、可分多张发票/账单；一个费用行对应一张客户发票或一张供应商账单，不做行级分批开票。
3. 本位币为人民币；允许美元/欧元等外币报价和开票；货单汇总按 Odoo 汇率表折算，收入/成本按发票/账单日期汇率，收付款按登记日期汇率。
4. 费用行录入不含税单价 + 税率，自动计算税额和含税单价；税额和含税金额可手工修改；费用类型可配置默认税率。
5. 开票时点由操作员决定，手工触发创建发票/供应商账单，生成 Odoo 草稿单据。
6. 无网上银行；财务在 Odoo 内登记收付款，不建设复杂核销界面。
7. 利润 = 已开票收入（含税） − 已确认成本（含税） − 税费净额（销项税 − 进项税），等价于不含税收入 − 不含税成本。
8. 货单阶段不强制状态机；不建设价目表、报价审批等精细报价管理。
9. 报表需求、角色权限后续再定；遗留字段、向导、方法保留兼容，不删除。

## 2. P0 财务正确性

| ID | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|
| TD-001 | 成本字段未启用，应付按 sale 计算 | `freight.service.cost` 在视图中隐藏，`action_create_vendor_bill` 使用 `data.sale`，`total_vendor_service_charge` 也按 sale 汇总，成本与利润失真 | 启用 cost/price 系列字段，vendor 行按不含税成本生成账单 | 待处理 |
| TD-002 | 多币种直接相加 | `_compute_total_amount` 直接累加 `amount_total_signed/amount_residual_signed`，未按人民币折算，外币发票越多误差越大 | 逐票用 `res.currency._convert` 按单据日期折算公司本位币 | 待处理 |
| TD-003 | 发票/账单与费用行无双向追溯 | `customer_invoice_id/vendor_invoice_id` 从未回填，发票作废/红冲后 `invoiced/vendor_invoiced` 不回滚，`account.move.line` 无法反查服务行 | 开票后回填发票行，继承 `account.move` 在状态变化时同步服务行 | 待处理 |
| TD-004 | account.move 联动字段错误 | `_onchange_freight_operation_id` 强制 `out_invoice` 带 consignee、`in_invoice` 带 agent，不符合分客户/分供应商开票；`destination_location_id` related 误指 source | 开票方法显式写 partner，修正 related 字段 | 待处理 |
| TD-005 | 账务汇总不随发票状态刷新 | 货单计算字段只依赖 `freight_services`，`account.move` 创建/过账/核销不触发刷新；计数含草稿、金额只统计 posted，口径不一致 | 计算字段依赖服务行关联的发票行状态，`account.move` 状态变化时显式刷新货单 | 待处理 |
| TD-006 | 列表服务端动作缩进错误 | `ir_actions_server_freight_create_*` 的 code 中 `if records:` 后未缩进，触发必然 `IndentationError` | 修复缩进并复用统一开票方法 | 待处理 |
| TD-007 | `shipment.invoice` 向导逻辑不可用 | 判断不存在的 `service_type == 'customer'`，写入非法状态 `quotation`，实际创建 `sale.order` 而非发票；当前无任何按钮/菜单入口 | 按“保留兼容”不删除；不挂接、不修复，后续决策 | 已确认（延期） |
| TD-008 | 税费链路缺失 | `freight.service` 无税率/税额字段，开票不携带税；报价/订舱行税额用百分比手算，不能处理含税价、复合税、固定税额 | 新增税率/税额/含税字段，开票生成 `account.tax`，行合计改用 `tax.compute_all` | 待处理 |
| TD-009 | 开票入口重复且部分缺关联 | 货单页按钮与列表服务端动作都可开票，无幂等控制；`action_create_shipper_invoice/consignee` 不写 `freight_operation_id`，仪表盘统计不到 | 统一到按伙伴+币种分组生成发票，补写 `freight_operation_id` | 待处理 |

## 3. P1 业务流程

| ID | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|
| TD-010 | onchange 调用后不落库 | 报价、订舱转货单、货单创建主路由均在 `create()` 后调用 `_onchange_address()` 但不 `write()`，起运/目的地址字段不保存 | 将地址填充改为正式计算字段或显式 `write()` | 待处理 |
| TD-011 | 计费重量比率类型错误 | `ir.config_parameter` 返回字符串，`weight_ratio` 参与比较和除法，配置比率后计费重量计算必然报错 | 统一 `float()` 转换后使用 | 待处理 |
| TD-012 | 合计与报关状态计算错误 | 删除全部箱货后 `package_total_*` 保留旧值；`pass_state` 由最后一行决定而非“全部通过” | 计算字段显式归零，`pass_state` 改为全行校验 | 待处理 |
| TD-013 | 港口 code 唯一约束空值 bug | 两个未填 code 的港口会触发重复校验 | 增加空值保护，与船/航司等其他模型一致 | 待处理 |
| TD-014 | 路由生成拣货单类型疑似反向 | `pickup` 使用 `in_type_id`、`delivery` 使用 `out_type_id`，与仓库提货/送货入库语义相反 | 确认业务语义后修正类型映射 | 待处理 |
| TD-015 | 自动生成的服务行无开票对象 | 包装费、路由费、保险转服务费只写价格，未写 `shipper_id/consignee_id/vendor_id`，后续无法开票 | 生成时要求归属伙伴，或显式提示补全 | 待处理 |
| TD-016 | 报价/订舱/货单转换校验不足 | 转货单不强制 transport/direction/operation；报价转订舱直接修改 partner 的 consignee 标记；无行数据校验 | 按已确认口径“不强制状态机”仅补必要必填校验，去掉 partner 副作用 | 待处理 |
| TD-017 | 货单序列按 transport 映射 operation 序列 | air→master、ocean→house、land→direct，运输方式与单证类型混淆 | 保留现有序列值，编码规则待业务确认后统一 | 已确认（延期） |
| TD-018 | 循环中误用 self | `_compute_invoice` 中 `service_quote_count/service_booking_count` 使用 `self.quotation_id/self.booking_id`，多记录计算错误 | 改为 `order.quotation_id/order.booking_id` | 待处理 |

## 4. P2 安全、规范与残留

| ID | 问题 | 现状/影响 | 修复方向 | 状态 |
|---|---|---|---|---|
| TD-019 | 门户写权限过宽 | `base.group_portal` 对 `freight.service`、箱货、跟踪、报关单据等开放写权限；`security.xml` 门户规则开启 `perm_unlink` | 按后续角色权限方案收敛，门户改为只读/询价 | 已延期 |
| TD-020 | 财务字段无权限收敛 | 内部任意用户可见应收应付与利润汇总 | 等角色权限确定后增加会计权限组 | 已延期 |
| TD-021 | 视图拼写错误 | `foce_Save`、`placeholer` 等未知属性残留 | 随相关视图改造一并修正 | 待处理 |
| TD-022 | 仪表盘统计口径不严谨 | 月度收付、TOP consignee 未过滤状态/公司/已核销，草稿发票进入统计 | 按 posted + 公司域过滤 | 待处理 |
| TD-023 | 缺少财务报表 | 无单票利润、客户对账、供应商对账、账龄报表；现有“Shipment Label”只是条码标签 | 报表需求后续确定后建设 | 已延期 |
| TD-024 | 遗留死代码 | `freight.js` 未加载、`BookingLine.compute_actual` 无效、deprecated 字段/方法、`shipment.invoice` 向导无入口 | 按业务确认“保留兼容”，暂不清理 | 已确认（延期） |
| TD-025 | 仪表盘/搜索缺少公司过滤 | 多公司环境下统计可能串公司 | 增加 `company_id` 过滤 | 待处理 |

## 5. 未决事项

以下事项待业务后续确认，确认前不实施：

1. 汇率折算细节：默认“收入/成本按发票日汇率、收付款按登记日汇率”，是否统一日期待确认。
2. 利润税费口径：默认“含税收入 − 含税成本 − 税费净额”，是否按净税口径待确认。
3. 手工税额开票方式：默认在“手工税额与税率计算不一致”时生成定额税码，是否允许待确认。
4. 报表需求：单票利润、对账、账龄等报表的具体格式待定。
5. 角色权限：内部角色划分、门户可见范围、财务权限组待定。
6. 外部财务系统：git 历史中存在已删除的 U8C/到账/开票 API 配置（原为保险经纪业务），是否需要在货代项目中恢复/重新设计待定。

## 6. 建议修复顺序

1. P0：TD-001、TD-002、TD-003、TD-004、TD-005、TD-008、TD-009 与费用模型改造一起处理。
2. P1：TD-010、TD-011、TD-012、TD-013、TD-015、TD-018 随相关流程修复。
3. P2：TD-021、TD-022、TD-025 在视图/仪表盘改造时顺手修复。
4. TD-006 属立即修复项，可随任何一次模块升级处理。
5. 已延期项等待业务决策，不在当前范围。
