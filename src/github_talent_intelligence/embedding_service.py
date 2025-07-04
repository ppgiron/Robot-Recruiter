from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class EmbeddingService:
    def __init__(self, model_name: str = MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Model loaded.")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate a single embedding for a text string."""
        if not text or not text.strip():
            raise ValueError("Input text for embedding is empty.")
        emb = self.model.encode([text], normalize_embeddings=True)[0]
        return emb

    def batch_generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of text strings."""
        if not texts:
            raise ValueError("Input list for batch embedding is empty.")
        embs = self.model.encode(texts, normalize_embeddings=True)
        return embs

# Singleton instance for use in API and batch jobs
embedding_service = EmbeddingService()

# Example usage (for testing):
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        emb = embedding_service.generate_embedding(text)
        print(f"Embedding shape: {emb.shape}")
        print(emb)
    else:
        print("Usage: python embedding_service.py <text to embed>") 