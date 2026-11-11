import hashlib
import math
from functools import lru_cache

from django.conf import settings
from langchain_core.embeddings import Embeddings

from .text import normalize, tokenize
class FastEmbedEmbeddings(Embeddings):

    def __init__(self, model_name: str):

        from fastembed import TextEmbedding
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts):
        return [
            self._unit(v)
            for v in self._model.embed([normalize(t) for t in texts])
        ]
    def embed_query(self, text):
        return self.embed_documents([text])[0]

    @staticmethod
    def _unit(vec):
        vec=[float(x) for x in vec]
        norm= math. sqrt(sum(x * x for x in vec)) or 1.0
        return [x/ norm for x in vec]
    
class HashEmbeddings(Embeddings):
    #substitute in offline cases
    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]
    def embed_query(self, text):
        return self._embed(text)

    def _embed(self,text):
        vec=[0.0]* self.dim
        for tok in tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0 if (h >> 64) % 2 else -1.0

        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

@lru_cache(maxsize=1)
def get_embeddings()->Embeddings:
    if settings.EMBEDDING_BACKEND =='hash':
        return HashEmbeddings()
    return FastEmbedEmbeddings(settings.EMBEDDING_MODEL)