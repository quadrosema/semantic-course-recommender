from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-base-en-v1.5"

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: list[str]):
    model = get_model()
    return model.encode(texts, normalize_embeddings=True)


def embed_text(text: str):
    return embed_texts([text])[0]
