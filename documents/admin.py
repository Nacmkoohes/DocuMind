# Register your models here.
from django.contrib import admin

from .models import Document, Chunk


class ChunkInline(admin.TabularInline):
    model = Chunk
    extra = 0
    readonly_fields = ["index", "text"]
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "chunk_count",
        "indexed_at",
        "created_at",
    ]

    search_fields = ["title", "content"]
    readonly_fields = ["content_hash", "indexed_at", "created_at", "updated_at"]
    inlines = [ChunkInline]


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ["id", "document", "index"]
    search_fields = ["document__title", "text"]
    readonly_fields = ["document", "index", "text", "embedding"]