import hashlib
from typing import Tuple, List

def compute_text_and_hash(title: str, summary: str, explanation: str, model_name: str) -> Tuple[str, str]:
    combined = "\n\n".join([s for s in [title, summary, explanation] if s])
    sha = hashlib.sha256()
    sha.update((combined + model_name).encode("utf-8"))
    return combined, sha.hexdigest()

def embed_text(text: str, model_name: str) -> List[float]:
    # Lazy import so that the module can be imported without heavy deps when embeddings are disabled
    from sentence_transformers import SentenceTransformer  # type: ignore

    model = SentenceTransformer(model_name)
    vec = model.encode([text], normalize_embeddings=True)[0]
    # Ensure we return a plain Python list for compatibility
    try:
        return vec.tolist()  # handles numpy arrays
    except AttributeError:
        # Already a list-like
        return list(vec)

