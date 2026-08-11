#!/usr/bin/env python3
"""产出语法门禁 — 可执行版本。取代 verify.sh（避免 bash heredoc 问题）"""
import os, re, sys, glob, xml.etree.ElementTree as ET

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODELS = os.path.join(BASE, 'mymodules/tk_freight/models')
VIEWS = os.path.join(BASE, 'mymodules/tk_freight/views')
passed, failed = 0, 0

def check(name, fn):
    global passed, failed
    print(f'  {name:20s} ... ', end='', flush=True)
    ok = fn()
    print('PASS' if ok else 'FAIL')
    if ok: passed += 1
    else: failed += 1
    return ok

print('\n========== 产出语法门禁 ==========')

# c1: Python 编译
def c1():
    for root, dirs, files in os.walk(MODELS):
        for fn in files:
            if not fn.endswith('.py'): continue
            fp = os.path.join(root, fn)
            try: compile(open(fp).read(), fn, 'exec')
            except SyntaxError as ex: print(f'\n  FAIL: {fn}: {ex}'); return False
    return True
check('Python 编译', c1)

# c2: XML 结构
def c2():
    for fn in sorted(os.listdir(VIEWS)):
        if not fn.endswith('.xml'): continue
        try: ET.parse(os.path.join(VIEWS, fn))
        except ET.ParseError: print(f'\n  FAIL: {fn}'); return False
    return True
check('XML 结构', c2)

# c3: 首行前导空格
def c3():
    for root, dirs, files in os.walk(os.path.join(BASE, 'mymodules/tk_freight')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if not fn.endswith(('.py', '.xml')): continue
            l = open(os.path.join(root, fn)).readline()
            if len(l) - len(l.strip()) > 1:
                print(f'\n  LEADING SPACE: {fn}'); return False
    return True
check('首行空格', c3)

# c4: 模块名一致性
def c4():
    matches = []
    old_names = ['wd_tlms', 'transport_logistics_management', 'odoo18_tms',
                 'odoo18e_tms', 'tlmp.']
    for root, dirs, files in os.walk(os.path.join(BASE, 'mymodules/tk_freight')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if not fn.endswith(('.py', '.xml', '.js', '.csv')): continue
            for i, line in enumerate(open(os.path.join(root, fn)), 1):
                if any(old in line for old in old_names):
                    matches.append(f'{fn}:{i}')
    if matches:
        for m in matches: print(f'\n  {m}')
        return False
    return True
check('模块名称', c4)

# c5: Odoo19 兼容
def c5():
    patterns = ['<tree', 'decoration-bf', 'decoration-it', 'state_selection', 'colors=', 'fonts=', 'attrs=', 'states=']
    for pat in patterns:
        for root, dirs, files in os.walk(VIEWS):
            for fn in files:
                if not fn.endswith('.xml'): continue
                for i, line in enumerate(open(os.path.join(root, fn)), 1):
                    if pat in line:
                        print(f'\n  {fn}:{i}: {pat}'); return False
    # view_mode 中包含 tree（Odoo 19 需改为 list）
    import re
    for root, dirs, files in os.walk(VIEWS):
        for fn in files:
            if not fn.endswith('.xml'): continue
            for i, line in enumerate(open(os.path.join(root, fn)), 1):
                if re.search(r'view_mode\s*=\s*"[^"]*\btree\b[^"]*"', line):
                    print(f'\n  {fn}:{i}: view_mode contains "tree" (use "list" in Odoo 19)'); return False
    return True
check('Odoo19 兼容', c5)

# c6: Tab 字符
def c6():
    for root, dirs, files in os.walk(os.path.join(BASE, 'mymodules/tk_freight')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if not fn.endswith(('.py', '.xml')): continue
            for i, line in enumerate(open(os.path.join(root, fn)), 1):
                if '\t' in line: print(f'\n  TAB: {fn}:{i}'); return False
    return True
check('Tab 字符', c6)

# c7: View-Model 字段存在性校验（v3）
def c7():
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(BASE, 'docs/context/governance/check_view_fields.py')],
                      capture_output=True, text=True)
    if r.returncode != 0:
        print()
        for l in r.stdout.strip().split('\n'): print(f'  {l}')
        return False
    print('  ... OK')
    return True
check('View-Model', c7)


# c8: Menuitem 父菜单顺序校验（防 BUG-011）
def c8():
    import glob, re
    errs = []
    for f in sorted(glob.glob(os.path.join(BASE, 'mymodules/tk_freight/views', '*.xml'))):
        with open(f) as fh:
            lines = fh.readlines()
        defined = {}  # id -> line_number
        referenced = []  # [(parent_id, child_id, line_number)]
        for i, line in enumerate(lines, 1):
            mid = re.search(r'\bid="(\w+)"', line)
            parent = re.search(r'\bparent="(\w+)"', line)
            if mid:
                defined[mid.group(1)] = i
            if parent:
                referenced.append((parent.group(1), mid.group(1) if mid else '?', i))
        for parent_id, child_id, ln in referenced:
            if parent_id not in defined:
                errs.append(f'{os.path.basename(f)}:{ln} parent="{parent_id}" never defined in file')
            elif defined[parent_id] > ln:
                errs.append(f'{os.path.basename(f)}:{ln} parent="{parent_id}" defined at line {defined[parent_id]} AFTER child')
    if errs:
        for e in errs: print(f'\n  {e}')
        return False
    return True
check('Menuitem顺序', c8)


# c9: 禁止 SQL 直写（cr.execute INSERT/UPDATE/DELETE 等）
def c9():
    import re
    pattern = re.compile(
        r"cr\.execute\s*\(\s*['\"](INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|TRUNCATE)",
        re.IGNORECASE,
    )
    hits = []
    for root, dirs, files in os.walk(os.path.join(BASE, 'mymodules/tk_freight')):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(root, fn)
            for i, line in enumerate(open(fp), 1):
                if pattern.search(line):
                    hits.append(f'{fn}:{i}')
    if hits:
        for h in hits:
            print(f'\n  SQL WRITE: {h}')
        return False
    return True
check('SQL直写', c9)


# c10: Context 资产完整性（关键文件必须存在）
REQUIRED_CONTEXT = [
    'docs/context/context_version.yaml',
    'docs/context/cognition/cognition_asset_map.md',
    'docs/context/constraints/forbidden_change.yaml',
    'docs/context/business/freight_rule.md',
    'docs/context/business/export_freight_coverage.md',
    'docs/context/business/reference/china_export_freight_forwarding_domain_model.md',
    'docs/context/business/knowledge_classification.md',
    'docs/context/business/business_rules.yaml',
    'docs/context/history/decision_note.md',
    'docs/context/history/bug_record.md',
    'docs/context/governance/check_view_fields.py',
    'mymodules/tk_freight/docs/technical_debt.md',
]


def c10():
    missing = [p for p in REQUIRED_CONTEXT if not os.path.exists(os.path.join(BASE, p))]
    if missing:
        for m in missing:
            print(f'\n  MISSING CONTEXT: {m}')
        return False
    return True
check('Context完整性', c10)


# c11: 业务铁律锚点（防止把 Context 改空）
def c11():
    rule_path = os.path.join(BASE, 'docs/context/business/freight_rule.md')
    if not os.path.exists(rule_path):
        return False
    content = open(rule_path, encoding='utf-8').read()
    anchors = ['收入 =', '成本 =', '本位币', '利润 =', 'odoo shell']
    missing = [a for a in anchors if a not in content]
    if missing:
        print(f'\n  MISSING BUSINESS ANCHOR: {missing}')
        return False
    return True
check('业务锚点', c11)


# c12: Context 版本刷新（docs/context 有变更时必须同步 context_version.yaml）
def c12():
    import subprocess
    r = subprocess.run(
        ['git', 'status', '--porcelain', 'docs/context'],
        cwd=BASE, capture_output=True, text=True,
    )
    changed = [line[3:] for line in r.stdout.splitlines() if line.strip()]
    if not changed:
        return True
    if 'docs/context/context_version.yaml' not in changed:
        print('\n  docs/context 有变更但未同步 context_version.yaml')
        return False
    return True
check('版本刷新', c12)


# c13: 业务规则冲突（利润口径一致性）
def c13():
    import re
    canonical = "已开票收入−已确认成本−税费"
    rules_path = os.path.join(BASE, 'docs/context/business/business_rules.yaml')
    if os.path.exists(rules_path):
        rules_content = open(rules_path, encoding='utf-8').read()
        block = rules_content.split('id: BR-04', 1)
        if len(block) == 2:
            m = re.search(r'statement:\s*"([^"]+)"', block[1])
            if m:
                raw = re.sub(r'\s+', '', m.group(1).split('（')[0])
                if raw.startswith('利润='):
                    raw = raw[len('利润='):]
                canonical = raw
    bad = []
    for f in sorted(glob.glob(os.path.join(BASE, 'docs/context/business', '*.md'))):
        with open(f, encoding='utf-8') as fh:
            for i, line in enumerate(fh, 1):
                m = re.search(r'利润\s*=\s*(.+)', line)
                if not m:
                    continue
                expr = m.group(1).strip()
                expr = re.split(r'[|（(]', expr)[0]
                expr = expr.rstrip('。！？；., ')
                norm = re.sub(r'\s+', '', expr)
                if norm != canonical:
                    bad.append(f'{os.path.basename(f)}:{i}: {expr}')
    if bad:
        for b in bad:
            print(f'\n  RULE CONFLICT: {b}')
        return False
    return True
check('规则冲突', c13)


# c14: Forbidden Change 机器可读结构检查
FORBIDDEN_SECTIONS = [
    'protected_models:', 'protected_fields:', 'protected_state_values:',
    'interface_contracts:', 'require_user_confirmation:', 'document_only:',
]
OWNED_PROTECTED_MODELS = [
    'freight.shipment', 'freight.service', 'shipment.quotation',
    'shipment.freight.booking',
]


def c14():
    import re
    fp = os.path.join(BASE, 'docs/context/constraints/forbidden_change.yaml')
    if not os.path.exists(fp):
        print('\n  forbidden_change.yaml not found')
        return False
    content = open(fp, encoding='utf-8').read()
    missing = [s for s in FORBIDDEN_SECTIONS if s not in content]
    if missing:
        print(f'\n  FORBIDDEN MISSING SECTION: {missing}')
        return False
    model_src = ''
    for f in sorted(glob.glob(os.path.join(BASE, 'mymodules/tk_freight/models', '*.py'))):
        model_src += open(f, encoding='utf-8').read()
    absent = [
        m for m in OWNED_PROTECTED_MODELS
        if not re.search(r"_name\s*=\s*['\"]" + re.escape(m) + r"['\"]", model_src)
    ]
    if absent:
        print(f'\n  PROTECTED MODEL NOT IN MODULE: {absent}')
        return False
    return True
check('Forbidden结构', c14)


USER_LOCAL_PATHS = (
    '.gitignore',
    '.vscode/',
    'mymodules/tk_freight/docs/config.xml',
    'debug_logs/',
)


def _current_intent_yaml():
    files = sorted(glob.glob(os.path.join(BASE, 'docs/context/intent', '*[Ss]print*.yaml')))
    files = [f for f in files if 'template' not in os.path.basename(f)]
    if not files:
        return None
    def num(fp):
        m = re.search(r'sprint(\d+)', os.path.basename(fp))
        return int(m.group(1)) if m else 0
    return max(files, key=num)


def _yaml_list_any(content, key):
    """Parse a YAML list under `key` at any indentation (inline [] or block)."""
    out = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        m = re.match(r'^(\s*)' + re.escape(key) + r':\s*(.*)$', lines[i])
        if not m:
            i += 1
            continue
        indent = m.group(1)
        tail = m.group(2).strip()
        if tail.startswith('['):
            inner = tail[1:-1].strip()
            if inner:
                out.extend(x.strip().strip('"\'')
                           for x in inner.split(',')
                           if x.strip().strip('"\''))
            i += 1
        else:
            prefix = indent + '  '
            j = i + 1
            while j < len(lines) and lines[j].startswith(prefix + '- '):
                item = lines[j].strip()[2:].strip().strip('"\'')
                if item:
                    out.append(item)
                j += 1
            i = j
    return out


# c15: Intent scope 越界检查
def c15():
    import subprocess
    intent = _current_intent_yaml()
    if not intent:
        print('\n  no intent file found')
        return False
    content = open(intent, encoding='utf-8').read()
    scopes = _yaml_list_any(content, 'allowed_files') or _yaml_list_any(content, 'scope_paths')
    if not scopes:
        print('\n  intent 缺少 scope.allowed_files / scope_paths')
        return False
    r = subprocess.run(['git', 'status', '--porcelain'], cwd=BASE,
                       capture_output=True, text=True)
    r2 = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=BASE,
                        capture_output=True, text=True)
    changed = set()
    for line in (r.stdout + '\n' + r2.stdout).splitlines():
        if not line.strip():
            continue
        p = line[3:] if len(line) > 3 and line[2] == ' ' else line
        if ' -> ' in p:
            p = p.split(' -> ')[-1]
        changed.add(p)
    bad = []
    for p in sorted(changed):
        if p.startswith(USER_LOCAL_PATHS):
            continue
        if any(p == s or p.startswith(s.rstrip('/') + '/') for s in scopes):
            continue
        bad.append(p)
    if bad:
        for b in bad:
            print(f'\n  OUT OF INTENT SCOPE: {b}')
        return False
    return True
check('Intent范围', c15)


# c16: 业务规则表结构检查
def c16():
    fp = os.path.join(BASE, 'docs/context/business/business_rules.yaml')
    if not os.path.exists(fp):
        print('\n  business_rules.yaml not found')
        return False
    content = open(fp, encoding='utf-8').read()
    required = ['BR-01', 'BR-04', 'BR-08', 'BR-09', 'BR-12',
                'status: CONFIRMED', 'status: ASSUMPTION',
                'status: UNKNOWN', 'status: DECISION_CONFIRMED']
    missing = [r for r in required if r not in content]
    if missing:
        print(f'\n  RULES REGISTRY MISSING: {missing}')
        return False
    return True
check('规则表结构', c16)


# c17: business/* 变更必须同步 decision_note
def c17():
    import subprocess
    r = subprocess.run(['git', 'status', '--porcelain', 'docs/context/business'],
                       cwd=BASE, capture_output=True, text=True)
    if not r.stdout.strip():
        return True
    r2 = subprocess.run(
        ['git', 'status', '--porcelain', 'docs/context/history/decision_note.md'],
        cwd=BASE, capture_output=True, text=True)
    if not r2.stdout.strip():
        print('\n  business/* 变更必须同步 history/decision_note.md')
        return False
    return True
check('业务决策同步', c17)


# c18: UNKNOWN 未确认不得进入代码开发
def c18():
    intent = _current_intent_yaml()
    if not intent:
        return False
    content = open(intent, encoding='utf-8').read()
    if not re.search(r'^(\s*)unresolved_unknowns\s*:', content, re.MULTILINE):
        print('\n  intent 缺少 unresolved_unknowns')
        return False
    unresolved = _yaml_list_any(content, 'unresolved_unknowns')
    if 'mymodules/' in content and unresolved:
        print(f'\n  UNRESOLVED UNKNOWNS: {unresolved}')
        return False
    return True
check('UNKNOWN拦截', c18)

print(f'\n========== 结果: {passed} pass, {failed} fail ==========')
if failed == 0: print('  ALL CHECKS PASSED \U0001f7e2')
else: print(f'  {failed} checks failed \u274c')
sys.exit(failed)
