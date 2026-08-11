#!/usr/bin/env python3
"""提交守卫：先跑 verify 门禁，通过后再提交已暂存内容（不自动 add、不默认 push）。"""
import os
import subprocess
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VERIFY = os.path.join(BASE, "execution", "scripts", "verify.py")


def run_verify():
    return subprocess.run([sys.executable, VERIFY], cwd=BASE).returncode == 0


def main():
    do_commit = "--commit" in sys.argv
    do_push = "--push" in sys.argv
    if not run_verify():
        print("\nGate not passed. Fix errors and retry.")
        sys.exit(1)
    print("\nGate passed.")
    if not do_commit:
        print("Use --commit to commit staged changes; use --commit --push to also push.")
        return
    print("Enter commit message:")
    msg = sys.stdin.readline().strip()
    if not msg:
        print("Empty message rejected.")
        sys.exit(1)
    r = subprocess.run(["git", "commit", "-m", msg], cwd=BASE)
    if r.returncode != 0:
        print("Git commit failed. Stage intended files first with git add.")
        sys.exit(1)
    print("Commit done.")
    if do_push:
        r = subprocess.run(["git", "push"], cwd=BASE)
        if r.returncode != 0:
            print("Git push failed.")
            sys.exit(1)
        print("Push done.")


if __name__ == "__main__":
    main()
