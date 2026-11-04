"""Run every lesson in an isolated temporary workspace; preserve student files."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0, '/opt/app')
from curriculum import LESSONS
from checks import COMMANDS

with tempfile.TemporaryDirectory(prefix='curriculum-test-') as folder:
    lab = Path(folder)
    shutil.copytree('/home/student/lab/tls', lab/'tls')
    shutil.copytree('/opt/examples', lab/'examples')
    (lab/'pki').mkdir()
    for lesson in LESSONS:
        for step in lesson['steps']:
            command = step['command'].replace('~/lab', shlex.quote(str(lab)))
            result = subprocess.run(['/bin/bash', '-c', command], cwd=lab, capture_output=True, text=True, timeout=20)
            # Several demonstrations intentionally return nonzero. Checkpoints assert their outcomes.
            if 'command not found' in result.stderr or ('No such file or directory' in result.stderr and '/missing.pem' not in command):
                raise AssertionError(f"{lesson['id']}: {result.stderr}")
        result = subprocess.run(['/bin/bash','-e','-o','pipefail','-c',COMMANDS[lesson['id']]], cwd=lab, capture_output=True, text=True, timeout=20)
        assert result.returncode == 0, f"{lesson['id']}: {result.stdout}\n{result.stderr}"
        print(f"PASS {lesson['id']}: lesson commands + checkpoint")
print(f'PASS all {len(LESSONS)} lessons in temporary workspace; student files unchanged.')
