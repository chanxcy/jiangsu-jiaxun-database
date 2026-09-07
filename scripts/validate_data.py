#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];data=root/'public'/'data'
load=lambda n:json.loads((data/n).read_text(encoding='utf-8'))
s=load('summary.json');expected={'records':9,'level_A':4,'level_B':3,'level_C':2,'text_units':27,'persons':17,'families':5,'places':14,'sources':11,'themes':22,'leads':5}
assert all(s[k]==v for k,v in expected.items()),(s,expected)
records=load('records.json');details=load('record_details.json');assert len({r['record_id'] for r in records})==len(records)==9
for r in records:
 assert r['record_id'] in details
 if r['verification_level']=='C':assert details[r['record_id']]['text_units']==[]
for p in data.glob('*.json'):
 raw=p.read_text(encoding='utf-8');assert not re.search(r'/Users/|[A-Za-z]:\\',raw),f'发现本地路径：{p}'
 json.loads(raw)
print('静态数据验证通过：',expected)
