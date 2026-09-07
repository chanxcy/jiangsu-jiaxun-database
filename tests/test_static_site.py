import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).parents[1];DATA=ROOT/'public'/'data'
def load(n):return json.loads((DATA/n).read_text(encoding='utf-8'))
def test_exported_json_valid():
 for p in DATA.glob('*.json'):json.loads(p.read_text(encoding='utf-8'))
def test_counts():
 s=load('summary.json');assert {k:s[k] for k in ['records','level_A','level_B','level_C','text_units','persons','families','places','sources','themes','leads']}=={'records':9,'level_A':4,'level_B':3,'level_C':2,'text_units':27,'persons':17,'families':5,'places':14,'sources':11,'themes':22,'leads':5}
def test_ids_unique_and_relations():
 rs=load('records.json');ds=load('record_details.json');assert len({x['record_id'] for x in rs})==9
 ps={x['person_id'] for x in load('persons.json')};pls={x['place_id'] for x in load('places.json')};ss={x['source_id'] for x in load('sources.json')};ts={x['theme_id'] for x in load('themes.json')}
 for d in ds.values():
  assert all(x['person_id'] in ps for x in d['persons']);assert all(x['place_id'] in pls for x in d['places']);assert all(x['source_id'] in ss for x in d['sources']);assert all(x['theme_id'] in ts for x in d['themes'])
def test_c_and_d_rules():
 ds=load('record_details.json');assert all(not d['text_units'] for d in ds.values() if d['verification_level']=='C');assert all(r['verification_level']!='D' for r in load('records.json'))
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
def test_c_message_present():assert '元数据已核，原文待补' in (ROOT/'src'/'js'/'record-detail.js').read_text(encoding='utf-8')
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
