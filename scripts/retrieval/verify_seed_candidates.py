#!/usr/bin/env python3
"""Resolve approved seed citation titles against final local catalog; never run selection.

Title-led lookup is a candidate locator. DOI/title conflicts remain unresolved; no
claim of global DOI uniqueness, seed freeze or relevance qualification is made.
"""
import argparse
import fcntl
import os
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import unicodedata
from xml.etree import ElementTree as ET


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKC',value).casefold() if c.isalnum())


def venue_tokens(value):
    value=unicodedata.normalize('NFKC',value).casefold()
    value=re.sub(r'\([^)]*\)','',value)
    tokens=re.findall(r'[^\W_]+',value,flags=re.UNICODE)
    return tokens[1:] if tokens[:1]==['the'] else tokens


def candidates(text):
    chosen={'S-01','S-02','C-01','C-05','C-06','C-07','C-10','C-11','C-12','C-13','C-14','C-17','C-27','C-28','C-29','C-30','C-31','C-32','C-33','C-40','C-42','C-25','C-36'}
    result=[]
    for line in text.splitlines():
        cells=[c.strip() for c in line.split('|')]
        if len(cells)<5 or cells[1] not in chosen:continue
        citation=cells[2].split('**Original appendix')[0]
        m=re.search(r'\((\d{4})\)\.\s*(.*?)\s+\*([^*]+)\*',citation)
        if not m:raise ValueError(f'Citation parse failed: {cells[1]}')
        doi=re.search(r'doi:([^\s;]+)',cells[3]);pmid=re.search(r'PMID (\d+)',cells[3])
        result.append(dict(id=cells[1],title=m[2].rstrip('.'),year=int(m[1]),venue=m[3],
                           doi=doi[1].lower() if doi else None,pmid=pmid[1] if pmid else None,
                           conditional=cells[1] in {'C-25','C-36'},needs=cells[4]))
    if {x['id'] for x in result}!=chosen or len(result)!=len(chosen):raise ValueError('Candidate inventory mismatch')
    return result


def record(xml):
    node=ET.fromstring(xml)
    def content(path):return ''.join(node.find(path).itertext()) if node.find(path) is not None else ''
    base='MedlineCitation/Article/'
    year=None
    for path in [base+'Journal/JournalIssue/PubDate/Year',base+'Journal/JournalIssue/PubDate/MedlineDate',base+'ArticleDate/Year','PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]/Year']:
        for value in node.findall(path):
            match=re.search(r'(?<![0-9])[0-9]{4}(?![0-9])',''.join(value.itertext()))
            if match:year=int(match[0]);break
        if year is not None:break
    ids=node.findall('PubmedData/ArticleIdList/ArticleId')+node.findall(base+'ELocationID')
    return dict(title=content(base+'ArticleTitle'),year=year,
      venues=[content(path) for path in ['MedlineCitation/MedlineJournalInfo/MedlineTA',base+'Journal/ISOAbbreviation',base+'Journal/Title']],
      dois=sorted({''.join(x.itertext()).casefold() for x in ids if (x.get('IdType') or x.get('EIdType'))=='doi'}),
      mesh_present=bool(node.findall('MedlineCitation/MeshHeadingList/MeshHeading')),
      indexing_status=node.find('MedlineCitation').get('Status') if node.find('MedlineCitation') is not None else None)


def citation_matches(candidate,found):
    cited=venue_tokens(candidate['venue'])
    return (normalize(candidate['title'])==normalize(found['title']) and
            (found['year'] is None or abs(candidate['year']-found['year'])<=1) and
            any(venue_tokens(v)[:len(cited)]==cited for v in found['venues']))


def atomic_json(path, value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,indent=2)
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def load_checkpoint(path, identity):
    state=json.loads(path.read_text())
    if state['identity']!=identity:
        raise ValueError('Checkpoint source/code/candidate identity mismatch')
    return state


def scan_titles(db,index,state,checkpoint,batch_size=10000):
    while True:
        batch=db.execute('SELECT rowid,pmid,title FROM documents WHERE rowid>? ORDER BY rowid LIMIT ?',
                         (state['last_rowid'],batch_size)).fetchall()
        if not batch:return state
        # Publish only complete batches. An interrupted partial batch replays safely.
        matches={key:list(values) for key,values in state['matched'].items()}
        for rowid,pmid,title in batch:
            for candidate_id in index.get(normalize(title or ''),[]):matches[candidate_id].append(pmid)
        state=dict(state,last_rowid=batch[-1][0],records_scanned=state['records_scanned']+len(batch),matched=matches)
        checkpoint(state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,required=True);p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=int,default=14400)
    p.add_argument('--resume',action='store_true')
    args=p.parse_args()
    if not 1<=args.seconds<=43200:raise ValueError('Time limit must be 1..43200 seconds')
    rows=candidates(args.candidates.read_text())
    if args.resume:
        if not args.output.is_dir():raise ValueError('Missing checkpoint directory')
        if (args.output/'matches.json').exists():raise ValueError('Lookup already complete; preserve results')
    else:args.output.mkdir(parents=True,exist_ok=False)
    lock=(args.output/'lookup.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    writer_lock=(args.catalog.parent/'writer.lock').open('rb')
    fcntl.flock(writer_lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
    db=sqlite3.connect(args.catalog.resolve().as_uri()+'?mode=ro',uri=True)
    db.execute('PRAGMA cache_size=-32768');db.execute('BEGIN')
    stat=args.catalog.stat()
    identity=dict(version=2,catalog_path=str(args.catalog.resolve()),catalog_size=stat.st_size,
                  catalog_mtime_ns=stat.st_mtime_ns,catalog_metadata=dict(db.execute('SELECT key,value FROM metadata')),
                  candidate_sha256=hashlib.sha256(args.candidates.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    checkpoint_path=args.output/'checkpoint.json'
    state=(load_checkpoint(checkpoint_path,identity) if args.resume else
           dict(identity=identity,last_rowid=0,records_scanned=0,matched={r['id']:[] for r in rows}))
    if not args.resume:
        atomic_json(args.output/'candidate-input.json',rows);atomic_json(checkpoint_path,state)
    start=time.monotonic();index={}
    for r in rows:index.setdefault(normalize(r['title']),[]).append(r['id'])
    db.set_progress_handler(lambda:int(time.monotonic()-start>args.seconds),10000)
    report=dict(state='scanning_titles',selection_run=False,seed_frozen=False,resumed=args.resume,
                records_scanned=state['records_scanned'],title_matches=sum(map(len,state['matched'].values())))
    def status():
        report['seconds_this_invocation']=time.monotonic()-start
        atomic_json(args.output/'status.json',report)
    def checkpoint(current):
        atomic_json(checkpoint_path,current)
        report.update(records_scanned=current['records_scanned'],title_matches=sum(map(len,current['matched'].values())))
        status()
        if time.monotonic()-start>args.seconds:raise TimeoutError('Lookup deadline; checkpoint retained')
    status()
    try:
        state=scan_titles(db,index,state,checkpoint)
        matched=state['matched'];outcomes=[]
        for c in rows:
            pmids=[c['pmid']] if c['pmid'] else matched[c['id']]
            found=[]
            for pmid in pmids:
                hit=db.execute('SELECT xml,source_file,source_sha256 FROM documents WHERE pmid=?',(pmid,)).fetchone()
                if hit:
                    metadata=record(hit[0]);found.append(dict(pmid=pmid,metadata=metadata,
                       citation_matches=citation_matches(c,metadata),doi_matches=c['doi'] in metadata['dois'] if c['doi'] else None,
                       source_file=hit[1],source_sha256=hit[2]))
            outcomes.append(dict(candidate=c,matches=found,lookup_complete=True))
        atomic_json(args.output/'matches.json',outcomes)
        report.update(state='lookup_complete_review_pending',records_scanned=state['records_scanned'],matched_candidates=sum(bool(x['matches']) for x in outcomes))
    except BaseException as exc:
        report.update(state='stopped',error=type(exc).__name__+': '+str(exc));raise
    finally:status();db.close();writer_lock.close();lock.close()


if __name__=='__main__':main()
