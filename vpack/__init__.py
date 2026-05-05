"""V-Pack Monitor — Camera station recording management."""

import os


def _get_version():
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip().lstrip("v")
    return "0.0.0"


__version__ = _get_version()
