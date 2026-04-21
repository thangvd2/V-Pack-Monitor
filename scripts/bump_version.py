import re
import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1].lstrip("v")
    print(f"Bumping version to {new_version}...")

    root_dir = Path(__file__).parent.parent

    # 1. Update VERSION file
    version_file = root_dir / "VERSION"
    if version_file.exists():
        version_file.write_text(f"v{new_version}\n", encoding="utf-8")
        print("Updated VERSION")

    # 2. Update Python and Frontend headers
    src_files = list(root_dir.glob("*.py")) + list((root_dir / "web-ui" / "src").rglob("*.[jt]s*"))
    header_pattern = re.compile(r"^((?:#| \*) V-Pack Monitor(?: - CamDongHang)?\s+v)\d+\.\d+\.\d+", flags=re.MULTILINE)
    count = 0
    for src_file in src_files:
        content = src_file.read_text(encoding="utf-8")
        new_content, num = header_pattern.subn(rf"\g<1>{new_version}", content)
        if num > 0:
            src_file.write_text(new_content, encoding="utf-8")
            count += 1
    print(f"Updated {count} Python/Frontend files")

    # 3. Update README.md
    readme_file = root_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding="utf-8")
        content = re.sub(r"(# 📦 V-Pack Monitor \(CamDongHang\) - v)\d+\.\d+\.\d+", rf"\g<1>{new_version}", content)
        content = re.sub(r"(## 🌟 Chức năng nổi bật \(v)\d+\.\d+\.\d+(\))", rf"\g<1>{new_version}\g<2>", content)
        readme_file.write_text(content, encoding="utf-8")
        print("Updated README.md")

    # 4. Update frontend package.json
    web_ui_dir = root_dir / "web-ui"
    package_json = web_ui_dir / "package.json"
    if package_json.exists():
        import json

        with open(package_json, encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != new_version:
            import os

            subprocess.run(
                ["npm", "version", new_version, "--no-git-tag-version"],
                cwd=str(web_ui_dir),
                check=True,
                shell=(os.name == "nt"),
            )
            print("Updated web-ui/package.json")
        else:
            print("web-ui/package.json already at version " + new_version)

    print("Version bump complete.")


if __name__ == "__main__":
    main()
