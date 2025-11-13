"""
Elasticsearch client configuration and connection management.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from elasticsearch import AsyncElasticsearch, NotFoundError

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    """Elasticsearch client wrapper with connection management."""

    def __init__(self, hosts: Optional[List[str]] = None, **kwargs):
        """
        Initialize Elasticsearch client.

        Args:
            hosts: List of Elasticsearch host URLs
            **kwargs: Additional Elasticsearch client options
        """
        self.hosts = hosts or [os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")]
        self.client: Optional[AsyncElasticsearch] = None
        self.options = kwargs

    async def connect(self) -> AsyncElasticsearch:
        """
        Connect to Elasticsearch.

        Returns:
            AsyncElasticsearch client instance
        """
        if self.client is None:
            self.client = AsyncElasticsearch(
                self.hosts,
                **self.options
            )

            # Test connection
            try:
                info = await self.client.info()
                logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
            except Exception as e:
                logger.error(f"Failed to connect to Elasticsearch: {e}")
                raise

        return self.client

    async def disconnect(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Elasticsearch")

    async def create_index(self, index_name: str, mappings: Dict[str, Any], settings: Optional[Dict[str, Any]] = None):
        """
        Create an index with mappings and settings.

        Args:
            index_name: Name of the index
            mappings: Index mappings
            settings: Index settings (optional)
        """
        client = await self.connect()

        # Check if index exists
        exists = await client.indices.exists(index=index_name)
        if exists:
            logger.info(f"Index '{index_name}' already exists")
            return

        # Create index
        body = {"mappings": mappings}
        if settings:
            body["settings"] = settings

        await client.indices.create(index=index_name, body=body)
        logger.info(f"Created index '{index_name}'")

    async def delete_index(self, index_name: str):
        """
        Delete an index.

        Args:
            index_name: Name of the index to delete
        """
        client = await self.connect()

        try:
            await client.indices.delete(index=index_name)
            logger.info(f"Deleted index '{index_name}'")
        except NotFoundError:
            logger.warning(f"Index '{index_name}' not found")

    async def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]):
        """
        Index a document.

        Args:
            index_name: Name of the index
            doc_id: Document ID
            document: Document data
        """
        client = await self.connect()
        await client.index(index=index_name, id=doc_id, document=document)

    async def bulk_index(self, index_name: str, documents: List[Dict[str, Any]], id_field: str = "id"):
        """
        Bulk index documents.

        Args:
            index_name: Name of the index
            documents: List of documents
            id_field: Field to use as document ID
        """
        from elasticsearch.helpers import async_bulk

        client = await self.connect()

        # Prepare bulk actions
        actions = [
            {
                "_index": index_name,
                "_id": doc[id_field],
                "_source": doc
            }
            for doc in documents
        ]

        success, failed = await async_bulk(client, actions, raise_on_error=False)
        logger.info(f"Bulk indexed {success} documents, {len(failed)} failed")

        return success, failed

    async def search(
        self,
        index_name: str,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a search query.

        Args:
            index_name: Name of the index
            query: Elasticsearch query DSL
            size: Number of results
            from_: Offset for pagination
            sort: Sort criteria
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        client = await self.connect()

        body = {"query": query, "size": size, "from": from_}
        if sort:
            body["sort"] = sort

        body.update(kwargs)

        result = await client.search(index=index_name, body=body)
        return result

    async def suggest(
        self,
        index_name: str,
        text: str,
        field: str,
        suggester_name: str = "suggestions"
    ) -> Dict[str, Any]:
        """
        Get suggestions for a text.

        Args:
            index_name: Name of the index
            text: Text to get suggestions for
            field: Field to suggest from
            suggester_name: Name for the suggester

        Returns:
            Suggestions
        """
        client = await self.connect()

        body = {
            "suggest": {
                suggester_name: {
                    "text": text,
                    "completion": {
                        "field": field,
                        "skip_duplicates": True,
                        "size": 10
                    }
                }
            }
        }

        result = await client.search(index=index_name, body=body)
        return result.get("suggest", {}).get(suggester_name, [])

    async def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            index_name: Name of the index
            doc_id: Document ID

        Returns:
            Document or None if not found
        """
        client = await self.connect()

        try:
            result = await client.get(index=index_name, id=doc_id)
            return result["_source"]
        except NotFoundError:
            return None

    async def update_document(self, index_name: str, doc_id: str, partial_document: Dict[str, Any]):
        """
        Update a document partially.

        Args:
            index_name: Name of the index
            doc_id: Document ID
            partial_document: Partial document to update
        """
        client = await self.connect()
        await client.update(index=index_name, id=doc_id, doc=partial_document)

    async def delete_document(self, index_name: str, doc_id: str):
        """
        Delete a document.

        Args:
            index_name: Name of the index
            doc_id: Document ID
        """
        client = await self.connect()

        try:
            await client.delete(index=index_name, id=doc_id)
        except NotFoundError:
            logger.warning(f"Document '{doc_id}' not found in index '{index_name}'")


# Global client instance
_elasticsearch_client: Optional[ElasticsearchClient] = None


def get_elasticsearch_client() -> ElasticsearchClient:
    """
    Get or create the global Elasticsearch client.

    Returns:
        ElasticsearchClient instance
    """
    global _elasticsearch_client

    if _elasticsearch_client is None:
        _elasticsearch_client = ElasticsearchClient()

    return _elasticsearch_client
