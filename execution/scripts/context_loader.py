#!/usr/bin/env python3
"""
Context Runtime v4 — AI Agent 开发前置认知加载 + 基线验证 + 风险注入

5.x 升级:
  - Profile 从硬编码 dict 升级为 profiles/*.yaml 文件驱动
  - 支持 include/exclude 黑白名单过滤 + load_strategy(summary/full_read/forbidden)
  - 新增 --profile CLI 参数自定义覆盖
  - 兼容旧版 context_load_profile 字段

职责:
  1. 加载上下文资产（按 Profile 过滤 + 按 load_strategy 分层摘要）
  2. 基线校验（intent binding vs context_version）
  3. 风险阻断（test_lessons LEVEL3 规则告警）
  4. 结构化输出（human / --json）

退出码:
  0 = READY         一切正常，可以开发
  1 = ASSET_MISSING 关键资产缺失
  2 = RISK_BLOCKED  存在未确认的 LEVEL3 风险
  3 = BASELINE_MISMATCH 上下文版本与契约要求的基线不匹配
"""
import os, sys, glob, json, re
from datetime import datetime

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CTX = os.path.join(BASE, 'docs/context')
PROFILES_DIR = os.path.join(CTX, 'profiles')
PATH_TEST_LESSONS = os.path.join(CTX, 'governance', 'test_lessons.yaml')
PATH_DECISION_NOTE = os.path.join(CTX, 'history', 'decision_note.md')

EXIT_READY = 0
EXIT_ASSET_MISSING = 1
EXIT_RISK_BLOCKED = 2
EXIT_BASELINE_MISMATCH = 3

# -----------------------------------------------------------
# 旧版 Profile 兜底（兼容旧格式 sprint 契约）
# -----------------------------------------------------------
LEGACY_PROFILES = {
    'development': {'deep': ['architecture', 'business', 'constraints/forbidden_change.yaml']},
    'testing':     {'deep': ['history/bug_record.md', 'governance/test_lessons.yaml', 'validation']},
    'bugfix':      {'deep': ['history/bug_record.md', 'constraints/forbidden_change.yaml',
                             'governance/test_lessons.yaml']},
    'infrastructure': {'deep': ['governance', 'architecture/dependency.yaml']},
    'full':        {'deep': None},
}

# -----------------------------------------------------------
# 通用工具
# -----------------------------------------------------------
def _read(path):
    """安全读取文件"""
    if not os.path.exists(path):
        return ''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except (UnicodeDecodeError, PermissionError, OSError) as err:
        return f'[READ_ERROR]: {repr(err)}'


def _yaml_val(text, key, default=''):
    """从 YAML 文本中提取指定 key 的值（纯文本解析）"""
    pat = re.compile(rf'^{re.escape(key)}\s*:\s*(["\']?)(.*?)\1?$', re.MULTILINE | re.DOTALL)
    m = pat.search(text)
    if m:
        return m.group(2).strip().strip('"').strip("'")
    return default


def _yaml_list(text, key, default=None):
    """从 YAML 文本中提取指定 key 下的 list 值"""
    if default is None:
        default = []
    pat = re.compile(rf'^{re.escape(key)}\s*:\s*\n((?:\s+- .*\n?)+)', re.MULTILINE)
    m = pat.search(text)
    if not m:
        return default
    items = re.findall(r'^\s+-\s+(.+)$', m.group(1), re.MULTILINE)
    return items


# -----------------------------------------------------------
# 版本与意图
# -----------------------------------------------------------
def read_version():
    raw = _read(os.path.join(CTX, 'context_version.yaml'))
    return _yaml_val(raw, 'context_version', 'UNKNOWN')


def read_intent():
    """返回 (filename, sprint_version, bind_context_version, profile_name)"""
    files = glob.glob(os.path.join(CTX, 'intent', '*[Ss]print*.yaml'))
    files = [f for f in files if 'template' not in f]
    if not files:
        return ('NONE', '', '', 'full')
    def sprint_num(fp):
        m = re.search(r'sprint(\d+)', os.path.basename(fp))
        return int(m.group(1)) if m else 0
    best = max(files, key=sprint_num)
    name = os.path.basename(best)
    raw = _read(best)
    sv = _yaml_val(raw, 'sprint_version', '')
    bv = _yaml_val(raw, 'bind_context_version', '')
    # 5.x 新字段: asset_snapshot_profile, 向后兼容: context_load_profile
    apf = _yaml_val(raw, 'asset_snapshot_profile', '')
    pf = apf or _yaml_val(raw, 'context_load_profile', 'full')
    return (name, sv, bv, pf)


# -----------------------------------------------------------
# 5.x Profile 加载（新增）
# -----------------------------------------------------------
def read_profile(profile_name):
    """读取 profiles/{profile_name}.yaml，返回 (include, exclude, load_strategy) 或 None"""
    fpath = os.path.join(PROFILES_DIR, f'{profile_name}.yaml')
    raw = _read(fpath)
    if not raw or raw.startswith('[READ_ERROR]'):
        return None

    include = _yaml_list(raw, 'include')
    exclude = _yaml_list(raw, 'exclude')
    ls_raw = _read(fpath)
    # 解析 load_strategy
    ls = {'mode': 'selective', 'summary': {'enabled': True},
          'full_read': {'allowed': []}, 'forbidden': []}
    allowed = _yaml_list(ls_raw, '  full_read:\n    allowed', default=None)
    if allowed is not None:
        ls['full_read']['allowed'] = allowed
    forbidden = _yaml_list(ls_raw, '  forbidden', default=None)
    if forbidden is not None:
        ls['forbidden'] = forbidden
    return {'name': profile_name, 'include': include, 'exclude': exclude, 'load_strategy': ls}


# -----------------------------------------------------------
# 资产扫描
# -----------------------------------------------------------
def scan_dir(subdir):
    path = os.path.join(CTX, subdir)
    if not os.path.isdir(path):
        return []
    items = []
    for f in sorted(os.listdir(path)):
        if f.startswith('.') or f == '__pycache__':
            continue
        items.append(f)
    return items


def check(name, subdir):
    items = scan_dir(subdir)
    ok = len(items)
    status = 'PASS' if ok > 0 else 'FAIL'
    return {'name': name, 'subdir': subdir, 'count': ok, 'status': status, 'items': items}


# -----------------------------------------------------------
# 内容摘要（支持 load_strategy）
# -----------------------------------------------------------
def summarize_file(fullpath, filename):
    raw = _read(fullpath)
    if raw.startswith('[READ_ERROR]'):
        return f'{filename}: FILE_READ_ERROR'
    if not raw:
        return f'{filename}: EMPTY'
    lines = raw.split('\n')
    if filename.endswith(('.yaml', '.yml')):
        entries = sum(1 for l in lines if ':' in l and not l.strip().startswith('#') and l[0] != ' ')
        return f'{filename}: {entries} entries'
    elif filename.endswith('.md'):
        headers = sum(1 for l in lines if l.startswith('#'))
        bullets = sum(1 for l in lines if l.strip().startswith('-'))
        return f'{filename}: {headers} headings, {bullets} items'
    else:
        return f'{filename}: {len(lines)} lines'


def _is_deep(subdir, fname, deep_list):
    if deep_list is None:
        return True
    rel = os.path.join(subdir, fname)
    for pattern in deep_list:
        if rel == pattern or rel.startswith(pattern):
            return True
    return False


def _match_profile_domain(domain_subdir, profile_include):
    """检查 domain 是否匹配 Profile include 列表"""
    if not profile_include:
        return True  # 空 include = 全部加载
    for pattern in profile_include:
        # pattern: 'architecture', 'business', 'history/decision_note'
        if domain_subdir == pattern or domain_subdir.startswith(pattern):
            return True
    return False


def _load_strategy_for_subdir(domain_subdir, load_strategy):
    """返回该 domain 的加载策略: 'forbidden' / 'summary' / 'full_read' """
    if not load_strategy:
        return 'full_read'
    # 检查 forbidden
    for f in load_strategy.get('forbidden', []):
        if domain_subdir == f or domain_subdir.startswith(f):
            return 'forbidden'
    # 检查 full_read.allowed
    for a in load_strategy.get('full_read', {}).get('allowed', []):
        if domain_subdir == a or domain_subdir.startswith(a):
            return 'full_read'
    return 'summary'


def summarize_domain(name, subdir, items, deep_list, load_strategy=None):
    ls_mode = _load_strategy_for_subdir(subdir, load_strategy)
    if ls_mode == 'forbidden':
        return {'name': name, 'subdir': subdir, 'count': 0, 'status': 'FORBIDDEN',
                'load_strategy': 'forbidden', 'files': []}

    summary = {'name': name, 'subdir': subdir, 'count': len(items),
               'load_strategy': ls_mode, 'files': []}
    for fname in items:
        fpath = os.path.join(CTX, subdir, fname)
        if ls_mode == 'full_read' and _is_deep(subdir, fname, deep_list):
            line = summarize_file(fpath, fname) + ' [Deep]'
        elif ls_mode == 'full_read':
            raw = _read(fpath)
            lc = raw.count('\n') + 1 if raw else 0
            line = f'{fname}: {lc} lines [Light]'
        else:
            # summary mode: 只统计行数
            raw = _read(fpath)
            lc = raw.count('\n') + 1 if raw else 0
            line = f'{fname}: {lc} lines [Summary]'
        summary['files'].append(line)
    return summary


# -----------------------------------------------------------
# 风险加载
# -----------------------------------------------------------
def load_risks():
    fp = PATH_TEST_LESSONS
    if not os.path.exists(fp):
        return []
    raw = _read(fp)
    blocks = raw.split('\n  - id:')
    rules = []
    for block in blocks[1:]:
        rid = block.split('"')[1] if block.count('"') >= 2 else '?'
        severity = ''
        problem = ''
        for line in block.split('\n'):
            if 'severity: "' in line:
                severity = line.split('"')[1]
            if 'problem: "' in line:
                problem = line.split('"')[1]
        rules.append({'id': rid, 'severity': severity, 'problem': problem})
    return rules


# -----------------------------------------------------------
# 报告构建
# -----------------------------------------------------------
def build_report(version, intent_info, domains, risks, summaries, all_pass,
                 gate_ok=False, profile_info=None):
    iv_name, iv_sprint, iv_bind, iv_profile = intent_info
    baseline_match = version == iv_bind if iv_bind else True
    high_risks = [r for r in risks if r['severity'] == 'LEVEL3']
    medium_risks = [r for r in risks if r['severity'] == 'LEVEL2']

    report = {
        'version': version,
        'profile': iv_profile,
        'gate_system_ok': gate_ok,
        'intent': {
            'file': iv_name,
            'sprint': iv_sprint,
            'bind_version': iv_bind,
        },
        'baseline_check': {
            'context_version': version,
            'intent_bind': iv_bind,
            'match': baseline_match,
        },
        'domains': domains,
        'all_pass': all_pass,
        'risks': {
            'total': len(risks),
            'level3': high_risks,
            'level2': medium_risks,
        },
        'summaries': summaries,
        'ready': all_pass and baseline_match and len(high_risks) == 0,
    }
    if profile_info:
        report['profile_info'] = {
            'name': profile_info['name'],
            'load_mode': profile_info.get('load_strategy', {}).get('mode', 'selective'),
            'domain_count': len(domains),
        }
    return report


# -----------------------------------------------------------
# 显示
# -----------------------------------------------------------
def _profile_label(profile_name):
    """旧 Profile 标签兜底显示"""
    labels = {
        'development': 'Development (5.x)',
        'maintenance': 'Maintenance (5.x)',
        'infrastructure': 'Infrastructure (5.x)',
        'governance': 'Governance (5.x)',
    }
    if profile_name in labels:
        return labels[profile_name]
    # 旧版 Profile 兜底
    return LEGACY_PROFILES.get(profile_name, {}).get('label', f'{profile_name} (legacy)')


def display_human(report):
    print()
    print('=' * 50)
    print('  Context Runtime v4 - Pre-Development Gate')
    print('=' * 50)
    print(f'  Run Timestamp:    {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'  Context Version:  {report["version"]}')

    iv = report['intent']
    if iv['file'] != 'NONE':
        pf = report.get('profile', 'full')
        label = _profile_label(pf)
        print(f'  Load Profile:     {label}')
        if iv['sprint']:
            print(f'  Sprint:           {iv["sprint"]}')
        gate_text = '✅ Complete' if report.get('gate_system_ok') else '❌ Missing'
        print(f'  Submit Gate Suite: {gate_text}')
        print(f'  Decision Note:    {PATH_DECISION_NOTE}')

        # Profile info (5.x)
        pi = report.get('profile_info')
        if pi:
            print(f'  Profile Mode:     {pi["load_mode"]} ({pi["domain_count"]} domains)')

    # Baseline
    bc = report['baseline_check']
    if bc['intent_bind']:
        ok = 'PASS' if bc['match'] else 'FAIL'
        icon = '✅' if bc['match'] else '❌'
        print(f'  Baseline Check:   [{ok}]  {icon}')
        if not bc['match']:
            print(f'    context_version={bc["context_version"]} vs intent bind={bc["intent_bind"]}')
    else:
        print(f'  Baseline Check:   [SKIP]  (intent has no baseline)')

    print()

    # Domains
    all_pass = True
    for d in report['domains']:
        ls_tag = ''
        if d.get('load_strategy') in ('summary', 'forbidden'):
            ls_tag = f' [{d["load_strategy"]}]'
        ok = 'PASS' if d['status'] == 'PASS' else d['status']
        print(f'  {d["name"]:15s} [{ok}]{ls_tag}  {d["count"]} file(s)')
        for fl in d.get('files', []):
            print(f'    {fl}')
        if d['status'] == 'FAIL':
            all_pass = False
        elif d['status'] == 'FORBIDDEN':
            pass  # Not an error, just filtered out

    print()

    # Risks
    risks = report['risks']
    if risks['level3']:
        print(f'  🔴 HIGH RISK: {len(risks["level3"])} unresolved LEVEL3 rule(s)')
        for r in risks['level3']:
            print(f'     [{r["severity"]}] {r.get("id","?")}: {r.get("problem","")[:80]}')
        print('  ⚠  Review required before development')
    elif risks['level2']:
        print(f'  🟡 MEDIUM RISK: {len(risks["level2"])} LEVEL2 rule(s) to review')
        for r in risks['level2'][:3]:
            print(f'     [{r["severity"]}] {r.get("id","?")}: {r.get("problem","")[:60]}')
        if len(risks['level2']) > 3:
            print(f'     ... and {len(risks["level2"]) - 3} more')
    else:
        print('  Risk Review:      No unresolved risks')

    print()

    # Status
    ready = report['ready']
    if ready:
        print('  Status: READY ✅  Development can proceed')
    else:
        blockers = []
        if not all_pass:
            blockers.append('asset missing')
        if not report['baseline_check'].get('match', True):
            blockers.append('baseline mismatch')
        if risks['level3']:
            blockers.append('LEVEL3 risks unresolved')
        print(f'  Status: BLOCKED ❌  ({", ".join(blockers)})')
    print('=' * 50)


def display_json(report):
    print(json.dumps(report, ensure_ascii=False, indent=2))


# -----------------------------------------------------------
# 主流程
# -----------------------------------------------------------
def main():
    json_mode = '--json' in sys.argv
    # 解析 --profile CLI 参数（覆盖自动检测）
    cli_profile = None
    for i, arg in enumerate(sys.argv):
        if arg == '--profile' and i + 1 < len(sys.argv):
            cli_profile = sys.argv[i + 1]

    version = read_version()
    intent_info = read_intent()
    iv_name, iv_sprint, iv_bind, iv_profile = intent_info

    # CLI 参数优先级高于 intent 自动检测
    if cli_profile:
        iv_profile = cli_profile
        intent_info = (iv_name, iv_sprint, iv_bind, iv_profile)

    # ── 1. 基线校验 ──
    skip_baseline = '--skip-baseline' in sys.argv
    if not skip_baseline and iv_bind and version != iv_bind:
        mismatch = {
            'version': version,
            'intent': {'file': iv_name, 'sprint': iv_sprint, 'bind_version': iv_bind},
            'baseline_check': {'context_version': version, 'intent_bind': iv_bind, 'match': False},
            'status': 'BLOCKED', 'reason': 'baseline_mismatch', 'ready': False,
        }
        if json_mode:
            print(json.dumps(mismatch, ensure_ascii=False, indent=2))
        else:
            extra_hint = '' if not cli_profile else ' (--skip-baseline to override)'
            print()
            print('=' * 50)
            print(f'  ❌ BASELINE MISMATCH{extra_hint} - Development BLOCKED')
            print('=' * 50)
            print(f'  context_version.yaml:  {version}')
            print(f'  intent requires:       {iv_bind}')
            print(f'  Intent file:           {iv_name}')
            if cli_profile:
                print(f'  Override profile:      {iv_profile}')
            print()
            print('  Run: context_loader.py --json for machine-readable output')
            print('=' * 50)
        sys.exit(EXIT_BASELINE_MISMATCH)

    # ── 2. 加载 Profile（5.x 文件模式 / 旧版兜底） ──
    profile_cfg = read_profile(iv_profile)
    if profile_cfg:
        # 5.x 文件模式
        use_include = profile_cfg.get('include', [])
        use_exclude = profile_cfg.get('exclude', [])
        load_strategy = profile_cfg.get('load_strategy', {})
        deep_targets = None  # 5.x 不用 deep 列表
    else:
        # 旧版 dict 模式
        legacy = LEGACY_PROFILES.get(iv_profile, LEGACY_PROFILES['full'])
        use_include = []     # 旧版无 include
        use_exclude = []
        load_strategy = {}
        deep_targets = legacy.get('deep')

    # ── 3. 资产扫描（按 Profile 过滤） ──
    all_domain_configs = [
        ('Architecture', 'architecture'),
        ('Business', 'business'),
        ('History', 'history'),
        ('Constraints', 'constraints'),
        ('Cognition', 'cognition'),
        ('Governance', 'governance'),
        ('Validation', 'validation'),
    ]

    # 过滤: 只保留匹配 include 且不在 exclude 中的 domain
    domain_configs = []
    for name, subdir in all_domain_configs:
        if use_include and not _match_profile_domain(subdir, use_include):
            continue  # include 模式下，不在白名单则跳过
        if subdir in use_exclude:
            continue  # exclude 黑名单跳过
        domain_configs.append((name, subdir))

    domains = []
    all_pass = True
    for name, subdir in domain_configs:
        result = check(name, subdir)
        domains.append(result)
        if result['status'] != 'PASS':
            all_pass = False

    # ── 4. 风险加载 ──
    risks = load_risks()

    # ── 5. 内容摘要 ──
    summaries = []
    for name, subdir in domain_configs:
        items = scan_dir(subdir)
        summary = summarize_domain(name, subdir, items, deep_targets, load_strategy)
        summaries.append(summary)

    # ── 6. 构建 + 显示 ──
    script_dir = os.path.join(BASE, 'execution', 'scripts')
    gate_ok = all(os.path.exists(os.path.join(script_dir, s)) for s in ['verify.py', 'odoo_check.py', 'test_runner.py'])
    report = build_report(version, intent_info, domains, risks, summaries, all_pass, gate_ok, profile_cfg)

    if json_mode:
        display_json(report)
    else:
        display_human(report)

    # ── 7. 退出码 ──
    final_code = EXIT_READY
    if not report['ready']:
        if not report['all_pass']:
            final_code = EXIT_ASSET_MISSING
        elif len(report['risks']['level3']) > 0:
            final_code = EXIT_RISK_BLOCKED
    sys.exit(final_code)


if __name__ == '__main__':
    main()
