# ruff: noqa: E501

import os

import pytest
from unittest import mock
from unittest.mock import patch, Mock

from embedchain.config import ZillizDBConfig
from embedchain.vectordb.zilliz import ZillizVectorDB

# to run tests, provide the URI and TOKEN in .env file
class TestZillizVectorDBConfig:
    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def test_init_with_uri_and_token(self):
        """
        Test if the `ZillizVectorDBConfig` instance is initialized with the correct uri and token values.
        """
        # Create a ZillizDBConfig instance with mocked values
        expected_uri = "mocked_uri"
        expected_token = "mocked_token"
        db_config = ZillizDBConfig()

        # Assert that the values in the ZillizVectorDB instance match the mocked values
        assert db_config.uri == expected_uri
        assert db_config.token == expected_token

    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def test_init_without_uri(self):
        """
        Test if the `ZillizVectorDBConfig` instance throws an error when no URI found.
        """
        try:
            del os.environ["ZILLIZ_CLOUD_URI"]
        except KeyError:
            pass

        with pytest.raises(AttributeError):
            ZillizDBConfig()

    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def test_init_without_token(self):
        """
        Test if the `ZillizVectorDBConfig` instance throws an error when no Token found.
        """
        try:
            del os.environ["ZILLIZ_CLOUD_TOKEN"]
        except KeyError:
            pass
        # Test if an exception is raised when ZILLIZ_CLOUD_TOKEN is missing
        with pytest.raises(AttributeError):
            ZillizDBConfig()

class TestZillizVectorDB:
    @pytest.fixture
    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def mock_config(self, mocker):
        return mocker.Mock(spec=ZillizDBConfig())

    @patch("embedchain.vectordb.zilliz.MilvusClient", autospec=True)
    @patch("embedchain.vectordb.zilliz.connections.connect", autospec=True)
    def test_zilliz_vector_db_setup(self, mock_connect, mock_client, mock_config):
        """
        Test if the `ZillizVectorDB` instance is initialized with the correct uri and token values.
        """
        # Create an instance of ZillizVectorDB with the mock config
        # zilliz_db = ZillizVectorDB(config=mock_config)
        ZillizVectorDB(config=mock_config)

        # Assert that the MilvusClient and connections.connect were called
        mock_client.assert_called_once_with(uri=mock_config.uri, token=mock_config.token)
        mock_connect.assert_called_once_with(uri=mock_config.uri, token=mock_config.token)


class TestZillizDBCollection:
    @pytest.fixture
    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def mock_config(self, mocker):
        return mocker.Mock(spec=ZillizDBConfig())

    @pytest.fixture
    def mock_embedder(self, mocker):
        return mocker.Mock()

    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def test_init_with_default_collection(self):
        """
        Test if the `ZillizVectorDB` instance is initialized with the correct default collection name.
        """
        # Create a ZillizDBConfig instance
        db_config = ZillizDBConfig()

        assert db_config.collection_name == "embedchain_store"

    @mock.patch.dict(os.environ, {"ZILLIZ_CLOUD_URI": "mocked_uri", "ZILLIZ_CLOUD_TOKEN": "mocked_token"})
    def test_init_with_custom_collection(self):
        """
        Test if the `ZillizVectorDB` instance is initialized with the correct custom collection name.
        """
        # Create a ZillizDBConfig instance with mocked values

        expected_collection = "test_collection"
        db_config = ZillizDBConfig(collection_name="test_collection")

        assert db_config.collection_name == expected_collection

    @patch("embedchain.vectordb.zilliz.MilvusClient", autospec=True)
    @patch("embedchain.vectordb.zilliz.connections", autospec=True)
    def test_query_with_skip_embedding(self, mock_connect, mock_client, mock_config):
        """
        Test if the `ZillizVectorDB` instance is takes in the query with skip_embeddings.
        """
        # Create an instance of ZillizVectorDB with mock config
        zilliz_db = ZillizVectorDB(config=mock_config)

        # Add a 'collection' attribute to the ZillizVectorDB instance for testing
        zilliz_db.collection = Mock(is_empty=False)  # Mock the 'collection' object

        assert zilliz_db.client == mock_client()

        # Mock the MilvusClient search method
        with patch.object(zilliz_db.client, "search") as mock_search:
            # Mock the search result
            mock_search.return_value = [[{"entity": {"text": "result_doc"}}]]

            # Call the query method with skip_embedding=True
            query_result = zilliz_db.query(input_query=["query_text"], n_results=1, where={}, skip_embedding=True)

            # Assert that MilvusClient.search was called with the correct parameters
            mock_search.assert_called_once_with(
                collection_name=mock_config.collection_name,
                data=["query_text"],
                limit=1,
                output_fields=["text"],
            )

            # Assert that the query result matches the expected result
            assert query_result == ["result_doc"]

    @patch("embedchain.vectordb.zilliz.MilvusClient", autospec=True)
    @patch("embedchain.vectordb.zilliz.connections", autospec=True)
    def test_query_without_skip_embedding(self, mock_connect, mock_client, mock_embedder, mock_config):
        """
        Test if the `ZillizVectorDB` instance is takes in the query without skip_embeddings.
        """
        # Create an instance of ZillizVectorDB with mock config
        zilliz_db = ZillizVectorDB(config=mock_config)

        # Add a 'embedder' attribute to the ZillizVectorDB instance for testing
        zilliz_db.embedder = mock_embedder # Mock the 'collection' object

        # Add a 'collection' attribute to the ZillizVectorDB instance for testing
        zilliz_db.collection = Mock(is_empty=False)  # Mock the 'collection' object

        assert zilliz_db.client == mock_client()

        # Mock the MilvusClient search method
        with patch.object(zilliz_db.client, "search") as mock_search:
            # Mock the embedding function
            mock_embedder.embedding_fn.return_value = ["query_vector"]

            # Mock the search result
            mock_search.return_value = [[{"entity": {"text": "result_doc"}}]]

            # Call the query method with skip_embedding=False
            query_result = zilliz_db.query(input_query=["query_text"], n_results=1, where={}, skip_embedding=False)

            # Assert that MilvusClient.search was called with the correct parameters
            mock_search.assert_called_once_with(
                collection_name=mock_config.collection_name,
                data=["query_vector"],
                limit=1,
                output_fields=["text"],
            )

            # Assert that the query result matches the expected result
            assert query_result == ["result_doc"]