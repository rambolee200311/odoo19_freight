# 决策记录

- 决策21：Sprint3 实施契约暂存为 Sprint4（INT-FREIGHT-SPRINT4-001）。
- 决策22：Sprint3-002 分析阶段意图契约登记。
- 决策23：Sprint3-002 分析契约按评审修订（6 点）。
- 决策24：Sprint3-002 分析执行完成，报告交付，UNKNOWN 待业务负责人确认后进入 Sprint4。
- 决策25：Sprint3-002 分析报告按评审修订，候选规则与设计建议明确为非约束输入，报告扩展为 14 章，U-23 提升为 LEVEL4 / BLOCKING UNKNOWN。
- 决策26：Sprint3-002 分析报告补充 odoo shell 运行时核验结果（FACT-B），确认费用行-发票无双向追溯、total_invoiced=32500 为本位币 signed 口径、供应商账单为供应商原件按原币登记（不视为技术债）、statement 字段为标准银行流水字段、freight.multiple.invoice 为空表。
- 决策27：移除 U8C 历史残留，知识资产与分析报告同步清理。
- 决策28：U-02 汇率口径确认（B-23）：对账单默认取当前汇率，允许用户录入结算汇率覆盖。
- 决策29：U-04 税目字段范围澄清（当前无税目编码/名称字段）。
- 决策30：U-01 费用行整行开票确认（B-24）。
- 决策31：U-03 税费净额 = 销项税 − 进项税确认（B-25）。
- 决策32：Sprint3-002 剩余开放项确认（U-04 ~ U-32 → B-26 ~ B-38），开放项全部关闭。
- 决策33：目标工作流确认（录入费用→结算单→客户拒绝/作废→修改→新结算单→客户接受→草稿发票）；生成结算单向导 B-39；开票申请暂不设置开发任务。
- 决策34：Sprint4 契约按评审重写（状态机 draft → voided / confirmed → draft_invoice）。
- 决策35：Sprint4 契约按第二轮评审修订（draft metadata_only、confirmed 动作分离、唯一性/幂等、wizard 边界、费用资格、header 追溯、旧入口直调拦截、税目字段落模型、non_inference_rules）。
