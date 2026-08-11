# AI Agent 启动提示词模板

## 标准模板

```text
## 任务基准
启动 {Sprint名称}。

## 前置加载
首先执行 `python3 execution/scripts/context_loader.py` 加载上下文认知快照。

## 契约绑定
绑定意图契约：docs/context/intent/{intent_yaml}
基线上下文版本：context_version = {版本号}

## 迭代类型
本次迭代类型为「{profile_label}」，按 profiles/{work_type}.yaml 加载资产。
```

## 配套规则

1. loader 只出快照，资产原文按需 `cat` 读取。
2. 迭代结束更新 decision_note.md / sprint_log.md / context_version.yaml。
3. 有测试更新 validation/test_exec_records.yaml，有 Bug 更新 bug_record.md。
