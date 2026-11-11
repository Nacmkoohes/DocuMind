from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from django.conf import settings
from rank_bm25 import BM25Okapi

from documents.models import Chunk

from .embeddings import get_embeddings
from .text import tokenize

RRF_K = 60


class IndexMismatchError(RuntimeError):
    """Stored embeddings are incompatible with the current embedding model."""


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    document_title: str
    chunk_index: int
    text: str
    score: float
    #vector search score
    dense_score: float

    bm25_score: float
def retrieve(queries, top_k=None, document_ids=None)->list[Hit]:
    top_k=top_k or settings.RETRIEVAL_TOP_K
    candidates=settings.RETRIEVAL_CANDIDATES

    qs=Chunk.objects.select_related("documents").order_by("id")
    if document_ids:
        qs=qs.filter(document_ids__in=document_ids)
    chunks=list(qs)
    if not chunks:
        return []

    embeddings=get_embeddings()
    query_vecs=[
        np.array(embeddings.embed_query(q),dtype=np.float32)
        for q in queries
        ]

    dim=len(query_vecs[0])

    if any(len(c.embedding) != dim for c in chunks):
        raise IndexMismatchError(
            "Embedding size changed. Run: python manage.py reindex"
        )

    matrix = np.array([c.embedding for c in chunks], dtype=np.float32)
    bm25 = BM25Okapi([tokenize(c.text) or ["_"] for c in chunks])

    fused = defaultdict(float)
    best_dense = defaultdict(lambda: -1.0)
    best_bm25 = defaultdict(float)

    for query, qvec in zip(queries, query_vecs):
        dense = matrix @ qvec                  # cosine similarity
        sparse = bm25.get_scores(tokenize(query))

        dense_order = np.argsort(-dense)[:candidates]
        sparse_order = [i for i in np.argsort(-sparse)[:candidates] if sparse[i] > 0]

        for ranking in (dense_order, sparse_order):          # Reciprocal Rank Fusion
            for rank, idx in enumerate(ranking):
                fused[int(idx)] += 1.0 / (RRF_K + rank + 1)
        for idx in range(len(chunks)):
            best_dense[idx] = max(best_dense[idx], float(dense[idx]))
            best_bm25[idx] = max(best_bm25[idx], float(sparse[idx]))

    top = sorted(fused, key=fused.get, reverse=True)[:top_k]
    return [
        Hit(chunk_id=chunks[i].id, document_id=chunks[i].document_id,
            document_title=chunks[i].document.title, chunk_index=chunks[i].index,
            text=chunks[i].text, score=round(fused[i], 5),
            dense_score=round(best_dense[i], 4), bm25_score=round(best_bm25[i], 4))
        for i in top
    ]
