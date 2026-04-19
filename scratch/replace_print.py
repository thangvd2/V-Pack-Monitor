import os
import re

TARGET_FILES = [
    "api.py",
    "auth.py",
    "database.py",
    "recorder.py",
    "video_worker.py",
    "cloud_sync.py",
    "telegram_bot.py",
    "network.py",
    "routes_auth.py",
    "routes_records.py",
    "routes_stations.py",
    "routes_system.py",
]


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if "print(" not in content:
        return

    print(f"Processing {filepath}")

    # Prepend imports if not exists
    if "from logger import get_logger" not in content:
        # Find where to insert (after standard imports, or just at the top)
        # Safest is right after the first block of imports or simply at the top of the file after docstrings.
        # But wait, we can just insert it at the beginning of the file, after the copyright block.
        header_end = content.find("===============\n")
        if header_end != -1:
            insert_pos = content.find("\n", header_end + 16) + 1
            content = (
                content[:insert_pos]
                + "from logger import get_logger\nlogger = get_logger(__name__)\n\n"
                + content[insert_pos:]
            )
        else:
            content = "from logger import get_logger\nlogger = get_logger(__name__)\n\n" + content

    # Replace print( -> logger.info(, logger.error(, logger.warning(
    def replacer(match):
        arg = match.group(1)
        lower_arg = arg.lower()
        if "error" in lower_arg or "fail" in lower_arg:
            return f"logger.error({arg})"
        elif "warn" in lower_arg:
            return f"logger.warning({arg})"
        else:
            return f"logger.info({arg})"

    new_content = re.sub(r"print\((.*)\)", replacer, content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)


for filename in TARGET_FILES:
    if os.path.exists(filename):
        process_file(filename)

print("Replacement complete.")
