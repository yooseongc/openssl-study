"""Seed IDE defaults once; preserve user settings on subsequent starts."""
from pathlib import Path
import json
import shutil
import hashlib
format_file=Path('/home/student/lab/.clang-format')
if not format_file.exists() or hashlib.sha256(format_file.read_bytes().replace(b'\r\n',b'\n')).hexdigest() == '2b1731f2c8b9fa24b5f5878253ba3d75bd38594361d6d43153b987024cd549bd':
    shutil.copyfile('/opt/study.clang-format',format_file)
settings=Path('/home/student/ide-data/User/settings.json')
settings.parent.mkdir(parents=True,exist_ok=True)
if not settings.exists():
    settings.write_text(json.dumps({
        'workbench.colorTheme':'Default Dark Modern', 'workbench.startupEditor':'none',
        'workbench.tips.enabled':False, 'workbench.activityBar.location':'hidden',
        'workbench.sideBar.location':'left', 'window.menuBarVisibility':'compact',
        'editor.minimap.enabled':False, 'editor.inlayHints.enabled':'off', 'editor.fontSize':14, 'editor.tabSize':4,
        'editor.detectIndentation':False, 'editor.stickyScroll.enabled':False,
        'extensions.ignoreRecommendations':True, 'extensions.autoUpdate':False,
        'clangd.path':'/usr/bin/clangd', 'clangd.checkUpdates':False,
        'clangd.arguments':['--background-index','--clang-tidy','--header-insertion=never'],
        'clangd.fallbackFlags':['-I/home/student/lab/examples/cpp'],
        'terminal.integrated.cwd':'/home/student/lab',
        'security.workspace.trust.enabled':False,
        'telemetry.telemetryLevel':'off', 'update.mode':'none',
    },indent=2))

# Migrate only the previously shipped fallback; retain unrelated user settings.
current_settings=json.loads(settings.read_text())
if current_settings.get('clangd.fallbackFlags') == ['-std=c++20','-I/home/student/lab/examples/cpp']:
    current_settings['clangd.fallbackFlags']=['-I/home/student/lab/examples/cpp']
    settings.write_text(json.dumps(current_settings,ensure_ascii=False,indent=2)+'\n')
clangd_config=Path('/home/student/lab/.clangd')
if not clangd_config.exists():
    shutil.copyfile('/opt/scripts/study.clangd',clangd_config)

workspace=Path('/home/student/lab/.vscode')
workspace.mkdir(exist_ok=True)
defaults={
    'tasks.json': {'version':'2.0.0','tasks':[{
        'label':'Study: build active file','type':'process',
        'command':'/opt/scripts/ide-compile.sh','args':['${file}'],
        'options':{'cwd':'/home/student/lab'},'problemMatcher':['$gcc'],
        'group':{'kind':'build','isDefault':True}}]},
    'launch.json': {'version':'0.2.0','configurations':[{
        'name':'Study: debug active file','type':'lldb','request':'launch',
        'program':'${fileDirname}/${fileBasenameNoExtension}',
        'args':[],'cwd':'/home/student/lab','preLaunchTask':'Study: build active file',
        'initCommands':['settings set target.disable-aslr false']}]}
}
for name,data in defaults.items():
    target=workspace/name
    if not target.exists():target.write_text(json.dumps(data,indent=2))
