
from backend.db.chroma_store import get_vector_store


def retrieve_relevant_chunks(
    question: str,
    k: int = 4,
) -> list[dict]:
    """Retrieve the most relevant manual chunks for a question."""

    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(
        query=question,
        k=k,
    )

    retrieved_chunks = []

    for document, score in results:
        retrieved_chunks.append(
            {
                "content": document.page_content,
                "source": document.metadata.get("source"),
                "page": document.metadata.get("page"),
                "score": float(score),
            }
        )

    return retrieved_chunks
