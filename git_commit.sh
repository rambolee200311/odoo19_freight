#!/bin/bash
# Release Gate — 参考 odoo18_tms/git_commit.sh，按 odoo19_freight/tk_freight 适配
# 步骤：verify.py → odoo_check.py（常驻+XML-RPC）→ test_runner.py → git commit
# 差异：
#   - 只提交 docs/ execution/ mymodules/tk_freight/docs/technical_debt.md，避免误带本地改动
#   - push 需要显式 --push 或 PUSH=1
#   - 仅文档/上下文变更时可 --skip-runtime 跳过 odoo_check/test_runner
set -e
cd "$(dirname "$0")"

SKIP_RUNTIME=0
if [ "$1" = "--skip-runtime" ]; then
    SKIP_RUNTIME=1
fi

echo ""
echo "========== [Gate] Step 1: Quality Gate (verify.py) =========="
python3 execution/scripts/verify.py
if [ $? -ne 0 ]; then
    echo "FAIL: Quality gate not passed. Fix errors and retry."
    exit 1
fi

if [ "$SKIP_RUNTIME" -eq 0 ]; then
    echo ""
    echo "========== [Gate] Step 2: Runtime Validation (odoo_check.py) =========="
    echo "模块升级铁律：常驻 Odoo + XML-RPC button_immediate_upgrade + log 检查"
    python3 execution/scripts/odoo_check.py
    if [ $? -ne 0 ]; then
        echo "FAIL: Runtime validation not passed. Fix errors and retry."
        exit 1
    fi

    echo ""
    echo "========== [Gate] Step 2.5: Integration Tests (test_runner.py) =========="
    python3 execution/scripts/test_runner.py
    if [ $? -ne 0 ]; then
        echo "FAIL: Integration tests not passed. Fix errors and retry."
        exit 1
    fi
else
    echo "SKIP: --skip-runtime，跳过 odoo_check.py / test_runner.py（仅文档/上下文变更）"
fi

echo ""
echo "========== [Gate] Step 3: Commit =========="
echo "Enter commit message:"
read commit_msg
if [ -z "$commit_msg" ]; then
    echo "Empty description rejected"
    exit 1
fi

git add docs/ execution/ mymodules/tk_freight/docs/technical_debt.md
git commit -m "$commit_msg"

if [ "$1" = "--push" ] || [ "$PUSH" = "1" ]; then
    git push
    echo "Commit and push done."
else
    echo "Commit done. 未推送；如需推送运行: git_commit.sh --push"
fi
