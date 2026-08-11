# tk_freight 上下文基线

## 加载顺序（AI 开发前置）

1. 执行 `python3 execution/scripts/context_loader.py`
2. 读取 `context_version.yaml` 锁定基线
3. 读取 `constraints/forbidden_change.yaml` 刚性约束
4. 按 Intent 契约的 `asset_snapshot_profile` 加载对应 Profile

## 目录

```text
docs/context/
├── context_version.yaml         # 版本基线
├── architecture/                # 架构认知
├── business/                    # 业务铁律与财务口径
├── history/                     # 决策、Bug、迭代记录
├── constraints/                 # 禁止变更清单
├── cognition/                   # 认知控制规则
├── governance/                  # 治理、风险、审计
├── intent/                      # 意图契约模板与历史契约
├── intent_records/              # 执行记录
├── profiles/                    # Work Type 加载画像
└── validation/                  # 测试执行台账
```

## 提交门禁

```bash
python3 execution/scripts/verify.py
python3 execution/scripts/commit_guard.py --commit
```

注意：`commit_guard.py` 只提交已 `git add` 的内容，不自动 add，不默认 push。
