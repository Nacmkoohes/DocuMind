
from rest_framework import serializers

from .models import Document


class DocumentListSerializer(serializers.ModelSerializer):

    chunk_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "chunk_count",
            "indexed_at",
            "created_at",
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):

    chunk_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "file",
            "content",
            "content_hash",
            "chunk_count",
            "indexed_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "content_hash",
            "indexed_at",
            "created_at",
            "updated_at",
        ]
