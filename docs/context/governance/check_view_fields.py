#!/usr/bin/env python3
"""
View-Model 字段存在性交叉校验 (v3)
防止 BUG-007/009/010 类型错误：视图引用了模型中不存在的字段

v3 改进：
  1. 行级扫描，不依赖缩进宽度（兼容 3/4 空格混合项目）
  2. 识别 _inherit 链，累积父模型字段
  3. 识别 _inherit-only 模型（给已有模型加字段）
  4. 跳过 Odoo 标准基字段 + 常见关联字段
  5. 按 class 边界正确归属字段

用法: python3 check_view_fields.py
返回码: 0=通过, 1=有错误
"""
import os, re, sys, glob
import xml.etree.ElementTree as ET

BASE = '/Users/lijianqiang/Documents/odoo19_freight/mymodules/tk_freight'
MODELS_DIR = os.path.join(BASE, 'models')
VIEWS_DIR = os.path.join(BASE, 'views')

# Odoo 每个模型都有的标准基字段
BASE_MODEL_FIELDS = {
    'id', 'display_name', 'create_uid', 'create_date',
    'write_uid', 'write_date', '__last_update',
    'noupdate', 'message_main_attachment_id',
    'message_ids', 'message_follower_ids', 'message_partner_ids',
    'message_channel_ids', 'message_is_follower',
    'message_has_error', 'message_has_error_counter',
    'message_needaction', 'message_needaction_counter',
    'message_attachment_count', 'message_unread',
    'message_unread_counter', 'message_last_post_date',
    'website_message_ids',
    'activity_ids', 'activity_state', 'activity_user_id',
    'activity_type_id', 'activity_date_deadline',
    'activity_summary', 'activity_exception_decoration',
    'activity_exception_icon', 'activity_calendar_event_id',
    'name',  # 几乎所有模型都有 name/_rec_name
}


def extract_model_fields():
    """
    行级扫描全部模型文件，构建 {model_name: {field_name, ...}} 映射。
    按 class 边界追踪 _name / _inherit，将 field 归属到最近的 class。
    """
    model_defs = {}    # _name → {inherit: str|None, fields: set()}
    inherit_only = {}  # _inherit → fields set (no _name in same class)

    for f in sorted(glob.glob(os.path.join(MODELS_DIR, '*.py'))):
        with open(f) as fh:
            lines = fh.readlines()

        current_name = None
        current_inherit = None
        in_class = False

        for line in lines:
            sline = line.strip()

            # --- 检测 class 边界 ---
            m = re.match(r'^class\s+(\w+)', line)
            if m:
                # 保存上一个 class 的数据
                if current_name:
                    pass  # 已在 model_defs 中累积
                elif current_inherit:
                    pass  # 已在 inherit_only 中累积
                current_name = None
                current_inherit = None
                in_class = True
                continue

            if not in_class:
                continue

            # 跳过空行、注释、以及非缩进行（模块级代码）
            if not sline or sline.startswith('#'):
                continue
            if sline.startswith('"""') or sline.startswith("'''"):
                continue
            # 如果行不以空格/tab开头，可能是非 class 体的顶层代码
            if not line.startswith((' ', '\t')):
                continue

            # --- 检测 _name ---
            m = re.search(r"""\b_name\s*=\s*['\"]([^'\"]+)['\"]""", line)
            if m:
                current_name = m.group(1)
                if current_name not in model_defs:
                    model_defs[current_name] = {'inherit': None, 'fields': set()}
                # 如果同一行也有 _inherit
                im = re.search(r"""\b_inherit\s*=\s*['\"]([^'\"]+)['\"]""", line)
                if im:
                    model_defs[current_name]['inherit'] = im.group(1)
                continue

            # --- 检测 _inherit （单独一行）---
            im = re.search(r"""\b_inherit\s*=\s*['\"]([^'\"]+)['\"]""", line)
            if im:
                current_inherit = im.group(1)
                if current_name:
                    model_defs[current_name]['inherit'] = current_inherit
                continue

            # --- 检测 field 定义 ---
            fm = re.match(r'^\s*(\w+)\s*=\s*fields\.(\w+)\(', line)
            if fm:
                fname = fm.group(1)
                if current_name:
                    model_defs[current_name]['fields'].add(fname)
                elif current_inherit:
                    if current_inherit not in inherit_only:
                        inherit_only[current_inherit] = set()
                    inherit_only[current_inherit].add(fname)

    # --- 构建最终 field_map ---
    field_map = {}

    # 初始化所有 _name 模型
    for model_name, info in model_defs.items():
        field_map[model_name] = set(info['fields'])
        field_map[model_name].update(BASE_MODEL_FIELDS)

    # 继承父模型字段（递归极简版，仅一层）
    for model_name, info in model_defs.items():
        parent = info['inherit']
        if parent and parent in field_map:
            field_map[model_name].update(field_map[parent])

    # _inherit-only 模型的字段归属到被继承模型
    for iname, fields in inherit_only.items():
        if iname not in field_map:
            field_map[iname] = set(BASE_MODEL_FIELDS)
        field_map[iname].update(fields)

    return field_map, set(model_defs)


def extract_view_fields(filepath, owned_models):
    """从视图 XML 中提取 {model_name: {field_name, ...}}
    跳过 inline list 内嵌字段（它们属于 line model，不属于 parent model）"""
    views = {}
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except ET.ParseError:
        return views

    for record in root.findall(".//record"):
        model_elem = record.find("./field[@name='model']")
        if model_elem is None or not model_elem.text:
            continue
        model_name = model_elem.text.strip()
        # 只校验 tk_freight 自有模型；继承视图（account.move/sale.order 等）无法
        # 在不阅读官方源码的前提下验证标准字段，跳过并保持 DOCUMENT_ONLY。
        if model_name not in owned_models:
            continue
        arch = record.find("./field[@name='arch']")
        if arch is not None:
            fields_found = set()
            # Build parent map to skip inline list nested fields
            parent_map = {c: p for p in arch.iter() for c in p}
            for field_tag in arch.iter('field'):
                fn = field_tag.get('name')
                if not fn:
                    continue
                if fn == 'arch' or fn.startswith(('parent.', 'context_', '.')):
                    continue
                # Skip inline list nested fields (fields inside another <field> ancestor)
                found_field_ancestor = False
                cur = field_tag
                while cur in parent_map:
                    cur = parent_map[cur]
                    if cur.tag == 'field':
                        found_field_ancestor = True
                        break
                    if cur.tag in ('list', 'tree', 'form', 'group', 'sheet', 'header', 'search',
                                   'xpath', 'page', 'notebook', 'button'):
                        continue
                    else:
                        break
                if found_field_ancestor:
                    continue
                fields_found.add(fn)
            views[model_name] = fields_found
    return views


def main():
    field_map, owned_models = extract_model_fields()
    errors = []

    for f in sorted(glob.glob(os.path.join(VIEWS_DIR, '*.xml'))):
        view_fields = extract_view_fields(f, owned_models)
        for model_name, fnames in view_fields.items():
            model_fields = field_map.get(model_name, set())
            for fn in sorted(fnames):
                if fn in BASE_MODEL_FIELDS:
                    continue
                if fn not in model_fields:
                    errors.append((os.path.basename(f), model_name, fn))

    if errors:
        from collections import defaultdict
        by_file = defaultdict(list)
        for fname, model, field in errors:
            by_file[fname].append((model, field))

        print("=== View-Model 字段存在性校验 ===")
        for fname in sorted(by_file):
            items = by_file[fname]
            for model, field in sorted(items, key=lambda x: x[1]):
                print(f"  {fname}: field '{field}' NOT in model '{model}'")
        print(f"\n❌ {len(errors)} real error(s) found")
        return 1
    else:
        print("  View-Model 字段校验: 全部通过 ✅")
        return 0


if __name__ == '__main__':
    sys.exit(main())
