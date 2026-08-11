#!/usr/bin/env python3
"""模块升级检查（XML-RPC 铁律版）

要求：
  1. Odoo 以常驻方式启动（http_port 来自 odoo.conf）
  2. 通过 XML-RPC 调用 button_immediate_upgrade 升级 tk_freight
  3. 升级后检查 odoo.conf 指定 logfile 是否出现 ERROR/CRITICAL/TRACEBACK

禁止仅用 `-u --stop-after-init` 作为最终验证。
"""
import configparser
import os
import sys
import xmlrpc.client

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONF = os.path.join(BASE, "odoo.conf")
MODULE = "tk_freight"


def _read_conf():
    cfg = configparser.ConfigParser()
    if not os.path.exists(CONF):
        print("  odoo.conf not found")
        sys.exit(1)
    cfg.read(CONF)
    section = "options"
    host = cfg.get(section, "http_interface", fallback="0.0.0.0")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    port = int(cfg.get(section, "http_port", fallback="8090"))
    db = cfg.get(section, "db_name", fallback="odoo19_freight")
    login = cfg.get(section, "xmlrpc_user", fallback=os.environ.get("ODOO_LOGIN", ""))
    password = cfg.get(
        section, "xmlrpc_password", fallback=os.environ.get("ODOO_PASSWORD", "")
    )
    logfile = cfg.get(section, "logfile", fallback="debug_logs/odoo_190.log")
    return host, port, db, login, password, logfile


def _check_log(logfile):
    if not os.path.exists(logfile):
        print(f"  WARN: logfile not found: {logfile}")
        return True
    bad = ("ERROR", "CRITICAL", "TRACEBACK", "ParseError", "AssertionError")
    errors = []
    with open(logfile, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if any(tag in line for tag in bad):
                errors.append(line.strip()[:200])
    if errors:
        print(f"  FAIL: {len(errors)} log error line(s)")
        for e in errors[:20]:
            print(f"    {e}")
        return False
    print(f"  PASS: logfile {logfile} clean")
    return True


def main():
    host, port, db, login, password, logfile = _read_conf()
    url = f"http://{host}:{port}"
    if not login or not password:
        print(
            "  FAIL: XML-RPC 登录信息缺失。请在 odoo.conf [options] 配置 "
            "xmlrpc_user/xmlrpc_password，或设置 ODOO_LOGIN/ODOO_PASSWORD。"
        )
        sys.exit(1)
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, login, password, {})
    except Exception as exc:
        print(
            f"  FAIL: 无法连接常驻 Odoo 服务 {url}。请先启动："
            "venv/bin/python3 odoo-bin -c odoo.conf（常驻方式）"
        )
        print(f"    detail: {exc!r}")
        sys.exit(1)
    if not uid:
        print("  FAIL: XML-RPC 认证失败")
        sys.exit(1)

    obj = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    ids = obj.execute_kw(
        db, uid, password, "ir.module.module", "search", [[["name", "=", MODULE]]]
    )
    if not ids:
        print(f"  FAIL: module {MODULE} not found")
        sys.exit(1)
    try:
        obj.execute_kw(
            db, uid, password, "ir.module.module", "button_immediate_upgrade", [ids]
        )
    except Exception as exc:
        print(f"  FAIL: XML-RPC upgrade raised: {exc!r}")
        sys.exit(1)
    version = obj.execute_kw(
        db, uid, password, "ir.module.module", "read", [ids, ["installed_version"]]
    )
    print(f"  PASS: {MODULE} upgraded, installed_version={version[0].get('installed_version')}")
    sys.exit(0 if _check_log(logfile) else 1)


if __name__ == "__main__":
    main()
