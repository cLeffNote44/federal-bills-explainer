"""Generate embeddings using sentence-transformers."""

import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from rich.console import Console

from .types import EmbeddingDTO

logger = logging.getLogger(__name__)
console = Console()


class EmbeddingGenerator:
    """Generate embeddings for text using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the embedding generator."""
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        self.dimensions = 384  # Default for all-MiniLM-L6-v2
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        console.print(f"[bold yellow]Loading embedding model: {self.model_name}...[/bold yellow]")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            
            # Get actual dimensions by encoding a test string
            test_embedding = self.model.encode("test", convert_to_numpy=True)
            self.dimensions = len(test_embedding)
            
            console.print(f"[bold green]Embedding model loaded (dimensions: {self.dimensions})[/bold green]")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
            
    def embed(self, text: str, normalize: bool = True) -> List[float]:
        """Generate embedding for text."""
        if not self.model:
            raise RuntimeError("Model not initialized")
            
        try:
            # Generate embedding
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            # Convert to list of floats
            if isinstance(embedding, np.ndarray):
                embedding_list = embedding.tolist()
            else:
                embedding_list = list(embedding)
                
            return embedding_list
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.dimensions
            
    def batch_embed(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not self.model:
            raise RuntimeError("Model not initialized")
            
        try:
            # Generate embeddings in batch
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=len(texts) > 10,
                batch_size=32
            )
            
            # Convert to list of lists
            if isinstance(embeddings, np.ndarray):
                embeddings_list = embeddings.tolist()
            else:
                embeddings_list = [list(emb) for emb in embeddings]
                
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.dimensions for _ in texts]
            
    def create_embedding_dto(
        self,
        text: str,
        entity_type: str,
        entity_id: str,
        normalize: bool = True
    ) -> EmbeddingDTO:
        """Create an embedding DTO for storage."""
        vector = self.embed(text, normalize)
        
        return EmbeddingDTO(
            entity_type=entity_type,
            entity_id=entity_id,
            vector=vector,
            model_name=self.model_name,
            dimensions=self.dimensions,
            text_used=text[:500]  # Store first 500 chars for reference
        )
