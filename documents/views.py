from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .models import Document
from .serializers import DocumentListSerializer, DocumentDetailSerializer


class DocumentViewSet(viewsets.ModelViewSet):

    queryset = Document.objects.prefetch_related("chunks")

    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer

        return DocumentDetailSerializer