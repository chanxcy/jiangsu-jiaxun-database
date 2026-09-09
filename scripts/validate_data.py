#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];data=root/'public'/'data'
load=lambda n:json.loads((data/n).read_text(encoding='utf-8'))
s=load('summary.json');expected={'records':36,'level_A':4,'level_B':27,'level_C':5,'text_units':46,'persons':29,'families':21,'places':41,'sources':33,'themes':22,'leads':9}
assert all(s[k]==v for k,v in expected.items()),(s,expected)
records=load('records.json');details=load('record_details.json');assert len({r['record_id'] for r in records})==len(records)==36
places=load('places.json');coordinates=load('place_coordinates.json');place_ids={p['place_id'] for p in places};record_ids={r['record_id'] for r in records}
boundary=json.loads((data/'jiangsu_boundary.geojson').read_text(encoding='utf-8'))
city_names={'南京市','无锡市','徐州市','常州市','苏州市','南通市','连云港市','淮安市','盐城市','扬州市','镇江市','泰州市','宿迁市'}
assert len(boundary['features'])==13 and {f['properties']['city_name'] for f in boundary['features']}==city_names
assert boundary['source']['coordinate_system']=='WGS84' and 'ODbL' in boundary['source']['license']
assert len(coordinates['places'])==41
assert {p['place_id'] for p in coordinates['places']}==place_ids
for point in coordinates['places']:
 assert point['status'] in {'located','pending'}
 assert point['coordinate_system']=='WGS84' and point['precision'] and point['basis'] and point['source_name'] and point['verified_at']
 if point['status']=='located':
  assert point['source_url']
  assert isinstance(point['longitude'],(int,float)) and isinstance(point['latitude'],(int,float))
  assert 116.0<=point['longitude']<=122.5 and 30.5<=point['latitude']<=35.5
 else: assert point['longitude'] is None and point['latitude'] is None and point.get('missing_evidence')
for r in records:
 assert r['record_id'] in details
 if r['verification_level']=='C':assert details[r['record_id']]['text_units']==[]
for p in data.glob('*.json'):
 raw=p.read_text(encoding='utf-8');assert not re.search(r'/Users/|[A-Za-z]:\\',raw),f'发现本地路径：{p}'
 json.loads(raw)
for p in places:
 assert all(r['record_id'] in record_ids for r in p['records'])
print('静态数据验证通过：',expected)
