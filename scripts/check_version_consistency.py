import json
import re
import sys
from pathlib import Path


def main():
    root_dir = Path(__file__).parent.parent

    version_file = root_dir / "VERSION"
    if not version_file.exists():
        print("Error: VERSION file not found.")
        sys.exit(1)

    expected_version = version_file.read_text(encoding="utf-8").strip().lstrip("v")
    print(f"Expected version: {expected_version}")

    errors = []

    # Check Python files
    py_files = list(root_dir.glob("*.py"))
    header_pattern = re.compile(r"^# V-Pack Monitor(?: - CamDongHang)?\s+v(\d+\.\d+\.\d+)", flags=re.MULTILINE)
    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        match = header_pattern.search(content)
        if match and match.group(1) != expected_version:
            errors.append(f"{py_file.name}: expected {expected_version}, found {match.group(1)}")

    # Check README.md
    readme_file = root_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding="utf-8")
        match1 = re.search(r"# 📦 V-Pack Monitor \(CamDongHang\) - v(\d+\.\d+\.\d+)", content)
        if match1 and match1.group(1) != expected_version:
            errors.append(f"README.md title: expected {expected_version}, found {match1.group(1)}")

        match2 = re.search(r"## 🌟 Chức năng nổi bật \(v(\d+\.\d+\.\d+)\)", content)
        if match2 and match2.group(1) != expected_version:
            errors.append(f"README.md features: expected {expected_version}, found {match2.group(1)}")

    # Check package.json
    package_json = root_dir / "web-ui" / "package.json"
    if package_json.exists():
        with open(package_json, encoding="utf-8") as f:
            data = json.load(f)
            if data.get("version") != expected_version:
                errors.append(f"web-ui/package.json: expected {expected_version}, found {data.get('version')}")

    if errors:
        print("Version consistency checks failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("All version checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
