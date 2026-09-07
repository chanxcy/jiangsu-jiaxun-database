#!/usr/bin/env python3
"""从本地 SQLite 导出可公开发布的稳定 JSON；不会修改数据库。"""
import argparse, json, re, sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public'/'data'

def clean(v):
    if v is None:return None
    if isinstance(v,str):
        v=v.replace('\x00','').strip()
        if re.fullmatch(r'\d{4}-\d{1,2}-\d{1,2}.*',v):
            try:return datetime.fromisoformat(v.replace('Z','+00:00')).date().isoformat()
            except ValueError:pass
    return v

def safe_url(v):
    if not v:return None
    u=urlparse(v.strip())
    return v.strip() if u.scheme in {'https','http'} and u.netloc else None

def fetch(c,sql,params=()): return [{k:clean(v) for k,v in dict(x).items()} for x in c.execute(sql,params)]
def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')

def main():
    global OUT
    p=argparse.ArgumentParser();p.add_argument('--database',required=True,type=Path);p.add_argument('--output',type=Path,default=OUT);a=p.parse_args()
    OUT=a.output;OUT.mkdir(parents=True,exist_ok=True)
    uri=f"file:{a.database.resolve()}?mode=ro"
    with sqlite3.connect(uri,uri=True) as c:
        c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
        records=fetch(c,"SELECT r.*,p.standard_name primary_person_name,f.standard_name family_name FROM records r LEFT JOIN persons p ON p.person_id=r.primary_person_id LEFT JOIN families f ON f.family_id=r.family_id WHERE r.verification_level IN (?,?,?) ORDER BY r.record_id",('A','B','C'))
        persons=fetch(c,"SELECT * FROM persons ORDER BY person_id");families=fetch(c,"SELECT * FROM families ORDER BY family_id")
        places=fetch(c,"SELECT * FROM places ORDER BY place_id");sources=fetch(c,"SELECT * FROM sources ORDER BY source_id")
        for s in sources:s['url']=safe_url(s.get('url'))
        themes=fetch(c,"SELECT * FROM themes ORDER BY theme_id");leads=fetch(c,"SELECT * FROM leads WHERE verification_level=? ORDER BY lead_id",('D',))
        details={}
        for r in records:
            rid=r['record_id'];d=dict(r)
            d['text_units']=[] if r['verification_level']=='C' else fetch(c,"SELECT * FROM text_units WHERE record_id=? ORDER BY sequence_no",(rid,))
            d['persons']=fetch(c,"SELECT p.*,rp.role,rp.note relation_note FROM record_persons rp JOIN persons p ON p.person_id=rp.person_id WHERE rp.record_id=? ORDER BY rp.role,p.person_id",(rid,))
            d['places']=fetch(c,"SELECT p.*,rp.relation_type,rp.time_note,rp.evidence_note FROM record_places rp JOIN places p ON p.place_id=rp.place_id WHERE rp.record_id=? ORDER BY rp.relation_type,p.place_id",(rid,))
            d['themes']=fetch(c,"SELECT t.*,pt.theme_name parent_name,rt.classification_basis FROM record_themes rt JOIN themes t ON t.theme_id=rt.theme_id LEFT JOIN themes pt ON pt.theme_id=t.parent_theme_id WHERE rt.record_id=? ORDER BY t.theme_id",(rid,))
            d['sources']=fetch(c,"SELECT s.*,rs.source_purpose,rs.verification_level source_verification_level,rs.locator,rs.verified_at FROM record_sources rs JOIN sources s ON s.source_id=rs.source_id WHERE rs.record_id=? ORDER BY s.source_id",(rid,))
            for s in d['sources']:
                s['url']=safe_url(s.get('url'));s['versions']=fetch(c,"SELECT * FROM source_versions WHERE source_id=? ORDER BY source_version_id",(s['source_id'],))
            details[rid]=d
        def related(table,pk,join,fk):
            base={x[pk]:x for x in table}
            for x in table:x['records']=[]
            for x in fetch(c,f"SELECT j.{fk} item_id,r.record_id,r.standard_title,r.era{',j.role relation_type,j.note relation_note' if join=='record_persons' else ',j.relation_type,j.evidence_note relation_note' if join=='record_places' else ',j.source_purpose relation_type,j.locator relation_note' if join=='record_sources' else ''} FROM {join} j JOIN records r ON r.record_id=j.record_id WHERE r.verification_level IN (?,?,?) ORDER BY r.record_id",('A','B','C')):
                if x['item_id'] in base:base[x['item_id']]['records'].append({k:v for k,v in x.items() if k!='item_id'})
        related(persons,'person_id','record_persons','person_id');related(places,'place_id','record_places','place_id');related(sources,'source_id','record_sources','source_id')
        for f in families:f['records']=[{'record_id':r['record_id'],'standard_title':r['standard_title'],'era':r['era']} for r in records if r['family_id']==f['family_id']]
        for t in themes:t['records']=[{'record_id':r['record_id'],'standard_title':r['standard_title']} for r in fetch(c,"SELECT rt.theme_id,r.record_id,r.standard_title FROM record_themes rt JOIN records r ON r.record_id=rt.record_id WHERE r.verification_level IN (?,?,?) ORDER BY r.record_id",('A','B','C')) if r['theme_id']==t['theme_id']]
        search=[]
        for rid,d in details.items():
            fields={'记录ID':rid,'题名':' '.join(filter(None,[d['standard_title'],d['short_title']])),'人物':' '.join(' '.join(filter(None,[x['standard_name'],x['alternative_name']])) for x in d['persons']),'家族':d['family_name'] or '', '地点':' '.join(' '.join(filter(None,[x['historical_name'],x['modern_name']])) for x in d['places']),'分节与原文':' '.join(' '.join(filter(None,[x['section_title'],x['original_text']])) for x in d['text_units']),'主题':' '.join(x['theme_name'] for x in d['themes']),'来源':' '.join(x['source_title'] for x in d['sources'])}
            search.append({'record_id':rid,'standard_title':d['standard_title'],'fields':fields,'normalized':' '.join(fields.values())})
        counts={k:len(v) for k,v in {'records':records,'persons':persons,'families':families,'places':places,'sources':sources,'themes':themes,'leads':leads}.items()};counts['text_units']=sum(len(x['text_units']) for x in details.values());counts.update({f'level_{lv}':sum(r['verification_level']==lv for r in records) for lv in 'ABC'})
        for n,v in [('summary.json',counts),('records.json',records),('record_details.json',details),('persons.json',persons),('families.json',families),('places.json',places),('themes.json',themes),('sources.json',sources),('leads.json',leads),('search_index.json',search)]:dump(n,v)
        dump('manifest.json',{'dataset':'江苏家训数据库公开静态版','files':['summary.json','records.json','record_details.json','persons.json','families.json','places.json','themes.json','sources.json','leads.json','search_index.json'],'counts':counts,'encoding':'UTF-8','runtime':'static'})
    print(json.dumps(counts,ensure_ascii=False))
if __name__=='__main__':main()
