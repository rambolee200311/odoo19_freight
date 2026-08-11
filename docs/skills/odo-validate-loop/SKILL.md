---
name: odo-validate-loop
description: >
  Use when changing or fixing the custom Odoo module tk_freight in this
  workspace. Enforces the module upgrade iron rule: resident Odoo server +
  XML-RPC upgrade + log inspection, then a closure report.
---

# Odoo 验证闭环

## When to use

Trigger automatically when the task involves modifying `mymodules/tk_freight` code, views, or data, or when the user asks "模块升级验证", "验证完了吗", "升级了吗", or "输出工作报告".

## Hard rules

- 模块升级一律用常驻方式启动 Odoo，并使用 XML-RPC 升级模块，复现人类工程师升级流程。
- 升级失败必须检查 log 文件：`debug_logs/odoo_190.log`（`odoo.conf` 指定 logfile）。
- 禁止仅用 `-u tk_freight --stop-after-init` 作为模块升级最终验证。
- 数据检查一律使用 `odoo shell`，非万不得已禁止直连数据库。
- 禁止修改官方 `odoo/` 与 `addons/` 代码。
- 不硬编码凭据；XML-RPC 登录信息从 `odoo.conf` 本地配置或环境变量读取。

## Workflow

1. 修改 tk_freight 代码，保持变更范围收敛；模型/视图/数据变更时递增 `__manifest__.py` version。
2. 静态校验：`python3 execution/scripts/verify.py`，并 `venv/bin/python -m py_compile <changed .py>`。
3. 常驻启动 Odoo：`venv/bin/python3 odoo-bin -c odoo.conf`（http_port 8090）；若已有常驻服务则复用，不重复启动。
4. XML-RPC 升级：调用 `/xmlrpc/2/object`，对 `ir.module.module` 搜索 `tk_freight` 并调用 `button_immediate_upgrade`；确认返回成功。
5. 检查 `debug_logs/odoo_190.log` 全文：出现 ERROR / CRITICAL / TRACEBACK / ParseError / AssertionError 即失败。
6. 通过 XML-RPC 重读 `ir.module.module.installed_version`，确认已升级到新版本。
7. 数据/行为校验用 `odoo shell` 完成；shell 写入必须 `env.cr.commit()` 并在新会话复核。
8. 若本会话启动了常驻服务，结束后释放端口并确认无残留监听；若复用已有服务，保持其运行状态。
9. 更新 `docs/context` 相关资产，使用 `execution/scripts/commit_guard.py --commit` 提交（不自动 add、不默认 push）。
10. 输出工作报告：变更、版本、验证结果、log 结论、git hash、端口状态、剩余事项。

## Common traps

- 沙箱内无法运行常驻服务与 `odoo shell`（psutil 进程权限被沙箱拦截），此时由用户在宿主机执行并回传输出。
- XML-RPC 升级返回 act_url 成功；必须重读模块版本确认升级生效。
- 数据回填被 NOT NULL 约束阻塞时，先升级模块应用 schema 变更，再回填。
- manifest 版本未递增时，XML-RPC 升级可能跳过 Python 变更。

## Learnings

- 常驻服务 + XML-RPC `button_immediate_upgrade` 是权威升级路径；`-u --stop-after-init` 不足以复现 UI 等效升级。
- 升级失败先看 log 再改代码，禁止只凭控制台错误猜原因。
- 本技能与 `task-completion-discipline` 配合使用。
