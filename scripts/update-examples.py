"""Upgrade only unedited copies from known shipped versions."""
import hashlib
import json
from pathlib import Path
import shutil

root = Path('/home/student/lab/examples')
originals = Path('/opt/examples')
baseline = json.loads(Path('/opt/scripts/example-baseline.json').read_text())
for name, digest in baseline.items():
    dest = root / name
    if dest.resolve() != dest or not dest.is_file():
        continue
    content = dest.read_bytes().replace(b'\r\n', b'\n')
    if hashlib.sha256(content).hexdigest() in ([digest] if isinstance(digest, str) else digest):
        shutil.copyfile(originals / name, dest)
