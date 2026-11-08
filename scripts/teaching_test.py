"""Verify teaching links against the shipped sources, without touching student files."""
from pathlib import Path
import sys
sys.path.insert(0, '/opt/app')
from curriculum import LESSONS

total = 0
for lesson in LESSONS:
    r = lesson['reading']
    assert r['flow']
    assert lesson['intro'] and len(lesson['sections']) >= 3
    assert all(len(s['paragraphs']) >= 2 for s in lesson['sections'])
    excerpts = [r['code']] if 'code' in r else []
    excerpts.extend(s['code'] for s in lesson.get('sections', []) if 'code' in s)
    for api in lesson.get('apis', []):
        assert all(api.get(k) for k in ('purpose','usage','args','ownership','returns','failure','lab'))
        assert api.get('practice_links')
        for link in api['practice_links']:
            target = next(l for l in LESSONS if l['id'] == link['lesson'])
            assert target['steps'][link['step']]['title'] == link['label']
            assert link['href'] == '/#' + target['id'] + '/step/' + str(link['step']+1)
        excerpts.extend(api.get('examples', []))
    for code in excerpts:
        path=Path('/opt/examples')/code['file'].removeprefix('examples/')
        lines=path.read_text(encoding='utf8').splitlines()
        actual='\n'.join(lines[code['line']-1:code['line']-1+len(code['text'].split('\n'))])
        assert actual == code['text'], (lesson['id'], code['file'])
        assert code['anchor'] in actual
        total += 1
assert len(LESSONS)==33
print(f'PASS: 33 reading routes; {total} exact source excerpts; API contracts and exercise anchors')
