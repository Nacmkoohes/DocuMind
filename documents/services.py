import hashlib
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings

def extract_docx_text(file_obj) -> str:
    doc = DocxDocument(file_obj)
    parts=[]
    for child in doc.element.body.iterchildren():
        if child.tag.endswith("}p"):
            text = Paragraph(child, doc).text.strip()
            if text:
                parts.append(text)
        elif child.tag.endswith("}tbl"):
            for row in Table(child,doc).rows:
                cells=[c.text.strip() for c in row.cells if c.text.strip()]

                if cells:
                    parts.append("|".join(cells))
    return "\n\n".join(parts)

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def split_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "؟ ", "! ", "؛ ", "، ", " ", ""],
    )
    return [c.strip() for c in splitter.split_text(text) if c.strip()]

@transaction.atomic
def index_document(document) -> int:
    from .models import Chunk, Document

    document.chunks.all().delete()
    pieces = split_text(document.content or "")
    if pieces:
        vectors = get_embeddings().embed_documents(pieces)
        Chunk.objects.bulk_create(
            [Chunk(document=document, index=i, text=t, embedding=v)
             for i, (t, v) in enumerate(zip(pieces, vectors))]
        )
    now = timezone.now()
    Document.objects.filter(pk=document.pk).update(indexed_at=now)
    document.indexed_at = now
    return len(pieces)