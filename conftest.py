# ============================================================
# conftest.py
# ============================================================
"""
Assure que le dossier racine du projet est sur sys.path,
afin que les modules `core.*` soient importables depuis
les tests sans installation du package.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
