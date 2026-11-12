from rest_framework import serializers


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True
    )

    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20
    )

    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=False
    )