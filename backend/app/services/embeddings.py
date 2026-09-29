from abc import ABC, abstractmethod
from typing import List, Optional
import math
import hashlib
import logging

logger = logging.getLogger(__name__)

class BaseEmbeddingProvider(ABC):
    """Abstract base class for text embedding generation."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

class LocalDeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    High-speed deterministic feature embedding generator producing normalized vectors.
    Ensures tests and offline RAG function immediately without requiring external API credits.
    Uses MD5/SHA256 projection + word token frequency distribution with L2 normalization.
    Default dimension is 768 to match Google GenAI embedding provider output.
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension

    def _text_to_vector(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        vec = [0.0] * self.dimension
        words = text.lower().split()
        
        # Word-level n-gram hashing
        for word in words:
            # Generate stable hash buckets
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 4) % 2 == 0) else -1.0
            vec[idx] += sign * (1.0 + math.log(len(word) + 1.0))

        # Bigram hashing for phrase semantic capturing
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h2 = int(hashlib.sha256(bigram.encode('utf-8')).hexdigest(), 16)
            idx2 = h2 % self.dimension
            sign2 = 1.0 if ((h2 >> 4) % 2 == 0) else -1.0
            vec[idx2] += sign2 * 2.0

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 1e-8:
            return [v / norm for v in vec]
        return [1.0 / math.sqrt(self.dimension)] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)

class GoogleGenAIEmbeddingProvider(BaseEmbeddingProvider):
    """
    Modern google-genai SDK embedding provider.
    Uses gemini-embedding-001 (text-embedding-004 was retired).
    Pinned to 768 dimensions via Matryoshka Representation Learning (MRL)
    for ChromaDB compatibility and storage efficiency.
    """
    def __init__(self, api_key: str, model: str = "gemini-embedding-001", dimensions: int = 768):
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions
        self.fallback = LocalDeterministicEmbeddingProvider(dimension=dimensions)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            all_embeddings = []
            
            # Gemini API has a limit of 100 requests per batch for embeddings
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                result = client.models.embed_content(
                    model=self.model,
                    contents=batch_texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=self.dimensions
                    )
                )
                all_embeddings.extend([e.values for e in result.embeddings])
                
            return all_embeddings
        except Exception as e:
            logger.warning(f"Google GenAI embedding failed ({str(e)}), falling back to local deterministic embedding.")
            return self.fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            result = client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self.dimensions
                )
            )
            if hasattr(result, "embedding") and result.embedding:
                return result.embedding.values
            if hasattr(result, "embeddings") and len(result.embeddings) > 0:
                return result.embeddings[0].values
            return self.fallback.embed_query(text)
        except Exception as e:
            logger.warning(f"Google GenAI query embedding failed ({str(e)}), falling back to local embedding.")
            return self.fallback.embed_query(text)

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embeddings provider."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.fallback = LocalDeterministicEmbeddingProvider()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.embeddings.create(input=texts, model=self.model)
            return [d.embedding for d in resp.data]
        except Exception as e:
            logger.warning(f"OpenAI embedding failed ({str(e)}), falling back to local embedding.")
            return self.fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            resp = client.embeddings.create(input=[text], model=self.model)
            return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI query embedding failed ({str(e)}), falling back to local embedding.")
            return self.fallback.embed_query(text)

def get_embedding_provider(provider: str = "gemini", api_key: Optional[str] = None) -> BaseEmbeddingProvider:
    if api_key and api_key not in ["mock_key", "test_key", "mock"] and provider == "gemini":
        return GoogleGenAIEmbeddingProvider(api_key=api_key)
    elif api_key and api_key not in ["mock_key", "test_key", "mock"] and provider == "openai":
        return OpenAIEmbeddingProvider(api_key=api_key)
    return LocalDeterministicEmbeddingProvider()
