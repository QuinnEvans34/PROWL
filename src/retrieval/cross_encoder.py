"""Bounded local relevance scoring over canonical literature passages, never generation."""
import hashlib
import math
from pathlib import Path
from time import monotonic


def ordered_hits(records, scores, k):
    if len(records) != len(scores) or type(k) is not int or not 1 <= k <= 50:
        raise ValueError('Invalid ranking cardinality')
    ids = [r['passage']['passage_id'] for r in records]
    if len(set(ids)) != len(ids) or any(not math.isfinite(s) for s in scores):
        raise ValueError('Invalid ranking identity or score')
    return sorted([dict(record=r, score=float(s)) for r, s in zip(records, scores)],
                  key=lambda h: (-h['score'], h['record']['passage']['passage_id']))[:k]


class PassageReranker:
    def __init__(self, folder, descriptor):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        expected = dict(device='cpu', dtype='float32', threads=4, batch_size=32,
                        max_tokens=512, max_passages=1179, seconds=30)
        if any(descriptor.get(k) != v for k, v in expected.items()):
            raise ValueError('Unsupported reranker limits')
        for name, checksum in descriptor['files'].items():
            if Path(name).name != name or hashlib.sha256((Path(folder)/name).read_bytes()).hexdigest() != checksum:
                raise ValueError('Reranker file identity mismatch')
        self.tokenizer = AutoTokenizer.from_pretrained(folder, local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(folder, local_files_only=True,
            trust_remote_code=False, use_safetensors=True).float().eval()
        torch.set_num_threads(4)
        self.descriptor = dict(descriptor)

    def rank(self, question, records, k=50):
        import torch
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
            raise ValueError('Invalid question')
        if not 1 <= len(records) <= self.descriptor['max_passages']:
            raise ValueError('Candidate count exceeds bounded corpus')
        if type(k) is not int or not 1 <= k <= 50:
            raise ValueError('Invalid result limit')
        deadline = monotonic() + self.descriptor['seconds']
        scores = []
        for offset in range(0, len(records), self.descriptor['batch_size']):
            if monotonic() >= deadline:
                raise TimeoutError('Reranking deadline')
            batch = records[offset:offset+self.descriptor['batch_size']]
            encoded = self.tokenizer([question]*len(batch), [r['text'] for r in batch],
                                     padding=True, truncation=False, return_tensors='pt')
            if encoded['input_ids'].shape[1] > self.descriptor['max_tokens']:
                raise ValueError('Reranker input exceeds token limit; no truncation')
            with torch.inference_mode():
                values = self.model(**encoded).logits.reshape(-1).tolist()
            scores.extend(values)
        if monotonic() >= deadline:
            raise TimeoutError('Reranking deadline')
        return ordered_hits(records, scores, k)
