"""
Версия Starvell Cardinal
"""

import os

VERSION = "0.3.18"
REPOSITORY_URL = "https://github.com/etheriumflipper/Starvell-Cardinal.git"
VERSION_URL = os.getenv(
    "STARVELL_VERSION_URL",
    "https://raw.githubusercontent.com/etheriumflipper/Starvell-Cardinal/main/version.py"
)
