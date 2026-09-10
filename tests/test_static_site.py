import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parents[1];DATA=ROOT/'public'/'data'
def load(n):return json.loads((DATA/n).read_text(encoding='utf-8'))
def test_exported_json_valid():
 for p in DATA.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
def test_counts():
 s=load('summary.json');assert {k:s[k] for k in ['records','level_A','level_B','level_C','text_units','persons','families','places','sources','themes','leads']}=={'records':36,'level_A':4,'level_B':27,'level_C':5,'text_units':46,'persons':29,'families':21,'places':41,'sources':33,'themes':22,'leads':9}
def test_ids_unique_and_relations():
 rs=load('records.json');ds=load('record_details.json');assert len({x['record_id'] for x in rs})==36
 ps={x['person_id'] for x in load('persons.json')};pls={x['place_id'] for x in load('places.json')};ss={x['source_id'] for x in load('sources.json')};ts={x['theme_id'] for x in load('themes.json')}
 for d in ds.values():
  assert all(x['person_id'] in ps for x in d['persons']);assert all(x['place_id'] in pls for x in d['places']);assert all(x['source_id'] in ss for x in d['sources']);assert all(x['theme_id'] in ts for x in d['themes'])
def test_c_and_d_rules():
 ds=load('record_details.json');assert all(not d['text_units'] for d in ds.values() if d['verification_level']=='C');assert all(r['verification_level']!='D' for r in load('records.json'))
 assert len(load('leads.json'))==9 and all(x['verification_level']=='D' for x in load('leads.json'))
 assert ds['JX-SB-004']['original_text_status']=='待复核' and not ds['JX-SB-004']['text_units']
 assert ds['JX-SZ-003']['original_text_status']=='待补' and not ds['JX-SZ-003']['text_units']
def test_jx_sz_006_title_and_access():
 ds=load('record_details.json');assert ds['JX-SZ-006']['standard_title']=='焦氏宗谱 祖训十条 训读书'
def test_reading_search():
 ix=load('search_index.json');assert any('读书' in x['normalized'] for x in ix)
def test_regions_and_levels():
 rs=load('records.json');assert {x['region'] for x in rs}=={'苏北','苏中','苏南'};assert {x['verification_level'] for x in rs}=={'A','B','C'}
def test_no_private_paths_or_duplicate_keys():
 for p in DATA.glob('*.json'):
  raw=p.read_text(encoding='utf-8');assert '/Users/' not in raw and not re.search(r'[A-Za-z]:\\',raw)
def test_pages_and_relative_assets():
 pages=list((ROOT/'src').glob('*.html'));assert len(pages)>=9
 for p in pages:
  raw=p.read_text(encoding='utf-8');assert 'href="/css/' not in raw and 'src="/js/' not in raw and 'href="/record' not in raw
def test_detail_accessible_from_list():assert 'record.html?id=' in (ROOT/'src'/'js'/'app.js').read_text(encoding='utf-8')
def test_safe_dom_construction():
 raw=''.join(p.read_text(encoding='utf-8') for p in (ROOT/'src'/'js').glob('*.js'));assert 'innerHTML' not in raw;assert 'textContent' in raw
def test_missing_text_messages_present():
 raw=(ROOT/'src'/'js'/'record-detail.js').read_text(encoding='utf-8');assert '原文待复核' in raw and '原文待补' in raw and '!r.text_units.length' in raw
def test_home_statistics_section_removed():
 raw=(ROOT/'src'/'index.html').read_text(encoding='utf-8')
 assert '数据范围' not in raw
 assert 'id="stats"' not in raw and 'class="stats"' not in raw
 assert not re.search(r'>\s*\d+\s*</(?:strong|span)>\s*<(?:span|strong)>\s*(?:正式记录|原文单元|待查线索)',raw)
 assert all(label in raw for label in ['江苏家训数据库','分类入口','主题入口','浏览家训','global-search'])
def test_home_no_longer_loads_summary_or_stats_css():
 js=(ROOT/'src'/'js'/'app.js').read_text(encoding='utf-8')
 css=(ROOT/'src'/'css'/'styles.css').read_text(encoding='utf-8')
 assert "load('summary.json')" not in js and "$('#stats')" not in js
 assert '.stats' not in css
 assert (DATA/'summary.json').exists()
def test_build_has_no_database(tmp_path):
 subprocess.run([sys.executable,str(ROOT/'scripts'/'build.py')],check=True);assert not list((ROOT/'dist').rglob('*.sqlite'));assert (ROOT/'dist'/'.nojekyll').exists()

def test_all_places_have_coordinate_status_and_provenance():
 places=load('places.json');geo=load('place_coordinates.json')['places']
 assert len(places)==len(geo)==41
 assert {p['place_id'] for p in places}=={p['place_id'] for p in geo}
 for point in geo:
  assert point['status'] in {'located','pending'}
  assert point['coordinate_system']=='WGS84'
  assert all(point.get(k) for k in ['precision','basis','source_name','verified_at'])
  if point['status']=='located': assert point.get('source_url')
  if point['status']=='located':
   assert isinstance(point['longitude'],(int,float)) and isinstance(point['latitude'],(int,float))
   assert 116<=point['longitude']<=122.5 and 30.5<=point['latitude']<=35.5
  else:
   assert point['longitude'] is None and point['latitude'] is None and point.get('missing_evidence')

def test_map_relations_and_shared_places_are_complete():
 places=load('places.json');details=load('record_details.json');record_ids=set(details)
 assert all(r['record_id'] in record_ids for p in places for r in p['records'])
 heyuan=next(p for p in places if p['place_id']=='PL-005')
 assert len(heyuan['records'])==2 and len({r['record_id'] for r in heyuan['records']})==1
 map_js=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8')
 assert 'new Map' in map_js and 'uniqueRelations' in map_js and 'dataset.placeId' in map_js and 'dataset.recordId' in map_js

def test_map_excerpt_uses_verified_text_without_generation():
 raw=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8')
 assert 'sequence_no' in raw and 'original_text' in raw and 'slice(0, 90)' in raw
 assert '原文待复核' in raw and '原文待补' in raw
 assert 'innerHTML' not in raw and 'textContent' in raw

def test_map_page_relative_assets_and_accessibility_fallback():
 html=(ROOT/'src'/'map.html').read_text(encoding='utf-8');js=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8')
 assert all(value in html for value in ['js/map.js','id="place-detail"','id="jiaxun-map"','aria-labelledby','aria-live="polite"'])
 assert 'map-count' not in html and 'map-popover' not in html
 assert 'map-count' not in js and 'map-popover' not in js
 assert 'fetch(`data/${name}`)' in js and 'record.html?id=' in js
 assert "event.key === 'Enter'" in js and "event.key === ' '" in js
 assert 'mouseenter' in js and "addEventListener('focus'" in js and "addEventListener('click'" in js
 assert 'updateSidePanel' in js and 'renderDefaultList' in js and 'mouseleave' not in js
 for page in (ROOT/'src').glob('*.html'):
  assert 'href="map.html"' in page.read_text(encoding='utf-8')

def test_thirteen_prefectures_regions_labels_and_legend():
 boundary=json.loads((DATA/'jiangsu_boundary.geojson').read_text(encoding='utf-8'))
 expected={'南京市','无锡市','徐州市','常州市','苏州市','南通市','连云港市','淮安市','盐城市','扬州市','镇江市','泰州市','宿迁市'}
 assert len(boundary['features'])==13 and {f['properties']['city_name'] for f in boundary['features']}==expected
 groups={f['properties']['city_name']:f['properties']['region'] for f in boundary['features']}
 assert {c for c,r in groups.items() if r=='苏南'}=={'南京市','无锡市','常州市','苏州市','镇江市'}
 assert {c for c,r in groups.items() if r=='苏中'}=={'南通市','扬州市','泰州市'}
 assert {c for c,r in groups.items() if r=='苏北'}=={'徐州市','连云港市','淮安市','盐城市','宿迁市'}
 assert 'OpenStreetMap / Nominatim' in boundary['source']['platform'] and 'Natural Earth' in boundary['source']['platform'] and 'ODbL' in boundary['source']['license'] and 'public domain' in boundary['source']['license'] and boundary['source']['coordinate_system']=='WGS84'
 html=(ROOT/'src'/'map.html').read_text(encoding='utf-8');js=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8');css=(ROOT/'src'/'css'/'styles.css').read_text(encoding='utf-8')
 assert 'id="city-label-layer"' in html and all(label in html for label in ['苏南','苏中','苏北'])
 assert all(token in js for token in ['city_name','region-${','city-label'])
 assert all(token in css for token in ['.region-south','.region-central','.region-north','.legend-south','.legend-central','.legend-north'])

def test_map_source_text_matches_data():
 html=(ROOT/'src'/'map.html').read_text(encoding='utf-8')
 assert '地图依据' in html and 'OpenStreetMap' in html and 'Natural Earth' in html and '地点坐标参考' in html and '高德地图' in html and 'WGS84' in html
 assert 'Natural Earth 1:50m Admin 1' not in html

def test_projected_nearby_grouping_does_not_mutate_coordinates():
 js=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8')
 assert 'GROUP_DISTANCE = 26' in js and 'Math.hypot' in js and 'projectedGroups' in js
 assert 'longitude +=' not in js and 'latitude +=' not in js

def test_pending_places_use_disclosed_city_representative_markers():
 js=(ROOT/'src'/'js'/'map.js').read_text(encoding='utf-8');html=(ROOT/'src'/'map.html').read_text(encoding='utf-8');css=(ROOT/'src'/'css'/'styles.css').read_text(encoding='utf-8')
 assert 'cityForPlace' in js and 'state.cityCenters' in js and "coord.status === 'located'" in js
 assert 'marker-pending-symbol' in js and '市域代表点（非历史遗址坐标）' in js
 assert '位置待核（市域代表点）' in html and '不是遗址、门牌或家族居地坐标' in html
 assert '.marker-pending-symbol' in css and '.legend-pending' in css
 coordinates=load('place_coordinates.json')['places']
 assert all(item['longitude'] is None and item['latitude'] is None for item in coordinates if item['status']=='pending')

def test_all_public_page_footers_are_consistent():
 expected='江苏家训文献数据库·古训新问'
 pages=list((ROOT/'src').glob('*.html'));assert pages
 for page in pages:
  raw=page.read_text(encoding='utf-8');assert raw.count(expected)==1;assert 'GitHub Pages 公开只读版' not in raw

def test_map_artifacts_in_build_and_no_secrets():
 subprocess.run([sys.executable,str(ROOT/'scripts'/'build.py')],check=True)
 for name in ['map.html','js/map.js','data/place_coordinates.json','data/jiangsu_boundary.geojson']:
  assert (ROOT/'dist'/name).exists()
 for page in (ROOT/'dist').glob('*.html'):
  assert '江苏家训文献数据库·古训新问' in page.read_text(encoding='utf-8')
 raw='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in (ROOT/'dist').rglob('*') if p.is_file())
 assert '/Users/' not in raw and not re.search(r'(?i)(api[_-]?key|secret|password)\s*[:=]\s*["\'][^"\']+',raw)
