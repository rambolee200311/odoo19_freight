---
name: task-completion-discipline
description: Use before ending any multi-step coding or verification turn. Enforces that every promised action is actually executed, the full closure checklist passes, and a work report is delivered. Trigger when the user asks "完成了吗", "改了吗", "报告", or whenever a task spans several steps.
---

# 任务完成纪律

## Core rule

"说做" 与 "做" 之间不能只隔一句话：一旦说“我现在执行”，下一条消息必须是工具调用。

## Closure checklist (before ending a turn)

- [ ] Code changes are actually written (verify with git diff / file content)
- [ ] Verification ran (syntax, XML, module upgrade, log check as applicable)
- [ ] Docs / issues / fix records updated
- [ ] Git committed and pushed (if repo work)
- [ ] Ports / services state verified (e.g. 8089 released or intentionally running)
- [ ] Work report delivered in final message

## Rules

1. Do not output "完成" unless the checklist passes.
2. Do not stop at an intermediate "准备更新文档/准备提交" state; finish the full loop in the same turn.
3. If blocked, state the exact blocker and what you need from the user; do not fake progress.
4. Change one independent issue at a time; verify before moving on.
5. Give the work report proactively: what changed, verification results, docs updated, git hash, port status, remaining items.

## Failure patterns to avoid

- "我现在就改" followed by no tool call, then the user has to repeat the request.
- Stopping after a code edit without upgrade / commit / report.

## When to invoke

Automatically at the end of any task turn, especially after long multi-step work, or when the user has to repeat "完成了吗 / 改了吗 / 报告".
