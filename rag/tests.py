
from unittest.mock import Mock, patch

import numpy as np
from django.test import TestCase, override_settings

from documents.models import Document, Chunk
from rag.llm_client import LLMClient
from .retriever import retrieve, IndexMismatchError, Hit
from .chain import RAGChain


class RetrieverTests(TestCase):

    def test_retrieve_returns_empty_list_when_no_chunks_exist(self):
        results = retrieve(["What is machine learning?"])

        self.assertEqual(results, [])

    @patch("documents.services.index_document")
    @patch("rag.retriever.get_embeddings")
    def test_retrieve_filters_by_document_ids(
        self, mock_embeddings, mock_index
    ):
        document1 = Document.objects.create(
            title="VPN",
            content="VPN encrypts network traffic."
        )

        document2 = Document.objects.create(
            title="Machine Learning",
            content="Machine learning uses training data."
        )

        Chunk.objects.create(
            document=document1,
            index=0,
            text="VPN encrypts network traffic.",
            embedding=[1.0, 0.0]
        )

        Chunk.objects.create(
            document=document1,
            index=1,
            text="VPN provides secure communication over public networks.",
            embedding=[0.9, 0.1]
        )

        Chunk.objects.create(
            document=document2,
            index=0,
            text="Machine learning uses training data.",
            embedding=[0.0, 1.0]
        )

        embeddings = Mock()
        embeddings.embed_query.return_value = [1.0, 0.0]
        mock_embeddings.return_value = embeddings

        results = retrieve(
            queries=["VPN"],
            document_ids=[document1.id]
        )

        self.assertEqual(len(results), 2)

        for result in results:
            self.assertEqual(result.document_id, document1.id)

    @patch("documents.services.index_document")
    @patch("rag.retriever.get_embeddings")
    def test_retrieve_raises_error_on_dimension_mismatch(
        self, mock_embeddings, mock_index
    ):
        document = Document.objects.create(
            title="VPN",
            content="VPN encrypts network traffic."
        )

        Chunk.objects.create(
            document=document,
            index=0,
            text="VPN encrypts network traffic.",
            embedding=[1.0, 0.0]
        )

        embeddings = Mock()
        embeddings.embed_query.return_value = [1.0, 0.0, 0.0]
        mock_embeddings.return_value = embeddings

        with self.assertRaises(IndexMismatchError):
            retrieve(queries=["VPN"])

    @patch("documents.services.index_document")
    @patch("rag.retriever.get_embeddings")
    def test_retrieve_respects_top_k(
        self, mock_embeddings, mock_index
    ):
        document = Document.objects.create(
            title="VPN",
            content="VPN encrypts network traffic."
        )

        for i in range(5):
            Chunk.objects.create(
                document=document,
                index=i,
                text=f"VPN information chunk {i}",
                embedding=[1.0, 0.0]
            )

        embeddings = Mock()
        embeddings.embed_query.return_value = [1.0, 0.0]
        mock_embeddings.return_value = embeddings

        results = retrieve(
            queries=["VPN"],
            top_k=2
        )

        self.assertEqual(len(results), 2)

    @patch("documents.services.index_document")
    @patch("rag.retriever.BM25Okapi")
    @patch("rag.retriever.get_embeddings")
    def test_retrieve_combines_dense_and_sparse_rankings(
        self, mock_embeddings, mock_bm25, mock_index
    ):
        document = Document.objects.create(
            title="VPN",
            content="VPN security and network traffic."
        )

        chunks = [
            Chunk.objects.create(
                document=document,
                index=i,
                text=text,
                embedding=vector
            )
            for i, (text, vector) in enumerate([
                ("VPN security", [1.0, 0.0]),
                ("VPN encryption", [0.9, 0.1]),
                ("Network traffic", [0.0, 1.0]),
            ])
        ]

        embeddings = Mock()
        embeddings.embed_query.return_value = [1.0, 0.0]
        mock_embeddings.return_value = embeddings

        mock_bm25.return_value.get_scores.return_value = np.array(
            [1.0, 3.0, 2.0]
        )

        results = retrieve(
            queries=["VPN"],
            top_k=3
        )

        self.assertEqual(results[0].chunk_id, chunks[1].id)


class LLMClientTests(TestCase):

    @override_settings(
        OPENROUTER_API_KEY="test-key",
        OPENROUTER_MODEL="test-model",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
        LLM_TEMPERATURE=0.2,
        LLM_MAX_TOKENS=1500,
        LLM_TIMEOUT=30,
    )
    @patch("rag.llm_client.ChatOpenAI")
    def test_generate_returns_response_content(self, mock_chat):

        mock_llm = mock_chat.return_value
        mock_llm.invoke.return_value.content = (
            "VPN provides secure communication."
        )

        client = LLMClient()

        result = client.generate([
            ("user", "What is VPN?")
        ])

        self.assertEqual(
            result,
            "VPN provides secure communication."
        )

        mock_llm.invoke.assert_called_once()


class RAGChainTests(TestCase):

    @patch("rag.chain.retrieve")
    def test_answer_does_not_call_llm_when_no_hits(self, mock_retrieve):

        mock_retrieve.return_value = []

        mock_llm = Mock()
        chain = RAGChain(llm_client=mock_llm)

        result = chain.answer("What is VPN?")

        self.assertEqual(
            result,
            {
                "answer": "No relevant information was found in the documents.",
                "sources": []
            }
        )

        mock_llm.generate_with_prompt.assert_not_called()

    @patch("rag.chain.retrieve")
    def test_answer_returns_answer_and_sources(self, mock_retrieve):

        hit = Hit(
            chunk_id=12,
            document_id=1,
            document_title="Network Security",
            chunk_index=2,
            text="VPN encrypts network traffic.",
            score=0.03,
            dense_score=0.9,
            bm25_score=4.2
        )

        mock_retrieve.return_value = [hit]

        mock_llm = Mock()
        mock_llm.generate_with_prompt.return_value = (
            "A VPN encrypts network traffic. [1]"
        )

        chain = RAGChain(llm_client=mock_llm)

        result = chain.answer(
            question="How does VPN work?",
            top_k=3,
            document_ids=[1]
        )

        self.assertEqual(
            result["answer"],
            "A VPN encrypts network traffic. [1]"
        )

        self.assertEqual(len(result["sources"]), 1)

        self.assertEqual(
            result["sources"][0]["chunk_id"],
            12
        )

        self.assertEqual(
            result["sources"][0]["document_id"],
            1
        )

        mock_retrieve.assert_called_once_with(
            queries=["How does VPN work?"],
            top_k=3,
            document_ids=[1]
        )

        mock_llm.generate_with_prompt.assert_called_once()

        prompt, inputs = mock_llm.generate_with_prompt.call_args.args

        self.assertEqual(
            inputs["question"],
            "How does VPN work?"
        )

        self.assertIn(
            "VPN encrypts network traffic.",
            inputs["context"]
        )
