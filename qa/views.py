
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

from drf_spectacular.utils import extend_schema, inline_serializer

from .serializers import QuestionSerializer
from rag.chain import RAGChain
from rag.exceptions import LLMError, LLMNotConfigured


AnswerResponseSerializer = inline_serializer(
    name="AnswerResponse",
    fields={
        "answer": serializers.CharField(),
        "sources": inline_serializer(
            name="AnswerSource",
            fields={
                "source_id": serializers.IntegerField(),
                "document_id": serializers.IntegerField(),
                "document_title": serializers.CharField(),
                "chunk_id": serializers.IntegerField(),
                "text": serializers.CharField(),
            },
            many=True,
        ),
    },
)


class AskQuestionView(APIView):

    @extend_schema(
        request=QuestionSerializer,
        responses={
            200: AnswerResponseSerializer,
            503: serializers.DictField(),
        },
        description="Answer a question using the indexed documents.",
    )
    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            rag = RAGChain()

            result = rag.answer(
                question=serializer.validated_data["question"],
                top_k=serializer.validated_data["top_k"],
                document_ids=serializer.validated_data.get("document_ids"),
            )

            return Response(result, status=status.HTTP_200_OK)

        except LLMNotConfigured:
            return Response(
                {"error": "LLM service is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        except LLMError:
            return Response(
                {"error": "LLM service is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
