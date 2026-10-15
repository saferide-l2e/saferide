#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python - <<'PY'
import json
import os
import re
from pathlib import Path

# Public build identity; contains only the Render-provided Git SHA, no credentials.
commit = os.getenv("RENDER_GIT_COMMIT", "")
if re.fullmatch(r"[0-9a-f]{40}", commit):
    Path("staticfiles/release.json").write_text(json.dumps({"commit": commit}) + "\n")
PY
