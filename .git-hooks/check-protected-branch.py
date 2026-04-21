#!/usr/bin/env python3
"""Block direct pushes to protected branches (master, dev)."""

import subprocess
import sys

PROTECTED = {"master", "dev"}


def main():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()

    if branch in PROTECTED:
        print(f"BLOCKED: Direct push to '{branch}' is not allowed.")
        print("Create a feature branch from dev and use PR:")
        print("  git checkout -b {type}/{description} dev")
        print("  git push origin {type}/{description}")
        print("  gh pr create --base dev")
        sys.exit(1)


if __name__ == "__main__":
    main()
