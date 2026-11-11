from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255, blank=True)

    file = models.FileField(
        upload_to="documents/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["docx"])],
        help_text="Optional .docx file."
    )

    content = models.TextField(blank=True)

    content_hash = models.CharField(
        max_length=64,
        blank=True,
        editable=False
    )

    indexed_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Document #{self.pk}"

    @property #call the method like an attribute document.chunk_count 
    def chunk_count(self) -> int:
        return self.chunks.count()

    def save(self, *args, **kwargs):
        from .services import content_hash, extract_docx_text, index_document

        if self.file and not self.file._committed:
            upload = self.file.file
            upload.seek(0)
            self.content = extract_docx_text(upload)
            upload.seek(0)

            if not self.title:
                self.title = Path(self.file.name).stem # Removes the file extension, e.g. report.docx -> report

        if not self.title:
            self.title = "Untitled document"

        new_hash = content_hash(self.content)
        needs_index = self._state.adding or new_hash != self.content_hash
        self.content_hash = new_hash

        super().save(*args, **kwargs)

        if needs_index:
            index_document(self)


class Chunk(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="chunks"
    )

    index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = models.JSONField()

    class Meta:
        ordering = ["document_id", "index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "index"],
                name="unique_chunk_per_document"
            )
        ]

    def __str__(self):
        return f"{self.document} #{self.index}"
