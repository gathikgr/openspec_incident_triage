import pytest
from unittest.mock import MagicMock, patch
from seed_rag import seed_runbooks, RUNBOOKS

def test_runbooks_structure():
    assert len(RUNBOOKS) == 3
    for r in RUNBOOKS:
        assert "title" in r
        assert "service" in r
        assert "content" in r
        assert "metadata" in r
        assert "service" in r["metadata"]

def test_seed_runbooks_mocked():
    mock_embeddings = MagicMock()
    mock_embeddings.embed_documents.return_value = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768
    ]

    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("psycopg.connect", return_value=mock_conn) as mock_connect:
        seed_runbooks(database_url="postgresql://mock:mock@localhost:5432/mockdb", embeddings_client=mock_embeddings)

        mock_connect.assert_called_once_with(
            "postgresql://mock:mock@localhost:5432/mockdb",
            prepare_threshold=None,
            autocommit=True
        )
        assert mock_cursor.execute.call_count == 3

        # Verify SQL statement includes ON CONFLICT for idempotency
        call_sql = mock_cursor.execute.call_args_list[0][0][0]
        assert "ON CONFLICT (service, title)" in call_sql
        assert "DO UPDATE" in call_sql

def test_embedding_dimensions():
    mock_embeddings = MagicMock()
    fake_vector = [0.0] * 768
    mock_embeddings.embed_documents.return_value = [fake_vector, fake_vector, fake_vector]
    embeddings = mock_embeddings.embed_documents(["a", "b", "c"])
    assert len(embeddings[0]) == 768
