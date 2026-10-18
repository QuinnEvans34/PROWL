"""Complete canonical section retrieval from bounded local cross-encoder windows."""
from collections import Counter
from time import monotonic
import math


class SectionRanker:
    def __init__(self, model, bundles, records):
        self.model=model
        self.records=sorted(records,key=lambda r:(r['passage']['work_id'],r['passage']['ordinal']))
        self.sections=[]
        for b in sorted(bundles,key=lambda b:b['work']['work_id']):
            rep=b['representation']
            for s in rep['sections']:
                self.sections.append(dict(key=(rep['work_id'],s['section_id']),
                    prefix=b['citation']['title']+'\n'+s['title']+'\n',
                    text=rep['text'][s['start']:s['end']]))

    def search(self, question):
        import torch
        if not isinstance(question,str) or not 1<=len(question.strip())<=500:
            raise ValueError('Invalid question')
        deadline=monotonic()+45
        windows=[]
        def add(section,start,end):
            text=section['prefix']+section['text'][start:end]
            tokens=self.model.tokenizer(question,text,truncation=False)['input_ids']
            if len(tokens)>512:
                if end-start<100:raise ValueError('Question/context exceeds token limit')
                middle=(start+end)//2
                add(section,start,middle);add(section,middle,end)
            else:windows.append((section['key'],text))
        for section in self.sections:
            for start in range(0,len(section['text']),1000):
                add(section,start,min(start+1200,len(section['text'])))
        if not 1<=len(windows)<=1600:
            raise ValueError('Section window budget exceeded')
        scores={}
        for start in range(0,len(windows),32):
            if monotonic()>=deadline:raise TimeoutError('Section ranking deadline')
            batch=windows[start:start+32]
            encoded=self.model.tokenizer([question]*len(batch),[w[1] for w in batch],
                padding=True,truncation=False,return_tensors='pt')
            if encoded['input_ids'].shape[1]>512:raise ValueError('Unexpected overlong pair')
            with torch.inference_mode():values=self.model.model(**encoded).logits.reshape(-1).tolist()
            if len(values)!=len(batch) or any(not math.isfinite(v) for v in values):
                raise ValueError('Invalid section scores')
            for (key,_),value in zip(batch,values):scores[key]=max(scores.get(key,-math.inf),value)
        if monotonic()>=deadline:raise TimeoutError('Section ranking deadline')
        chosen=[];counts=Counter()
        for key,value in sorted(scores.items(),key=lambda item:(-item[1],item[0])):
            if counts[key[0]]<3:
                chosen.append((key,value));counts[key[0]]+=1
            if len(chosen)==5:break
        hits=[]
        for (work,section),score in chosen:
            hits.extend(dict(record=r,score=score) for r in self.records
                        if (r['passage']['work_id'],r['passage']['section_id'])==(work,section))
        chars=sum(len(h['record']['text'])+len(h['record']['citation']['title']) for h in hits)
        if not hits or len(hits)>50 or chars>30000:
            raise ValueError('Selected section evidence budget exceeded')
        return dict(hits=hits,characters=chars,window_count=len(windows),selection=dict(sections=[
            dict(work_id=key[0],section_id=key[1],score=score) for key,score in chosen]))
