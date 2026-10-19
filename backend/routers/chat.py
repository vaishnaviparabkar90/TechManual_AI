
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.schemas import ChatRequest
from backend.services.retrieval import retrieve_relevant_chunks
from backend.services.generation import stream_answer

router = APIRouter(prefix="/chat", tags=["Chat"])


def is_greeting(message: str) -> bool:
    """Identify simple greetings and conversational messages."""
    normalized = message.lower().strip(" \t\n.,!?")

    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how are you doing",
        "thanks",
        "thank you",
        "ok",
        "okay",
        "got it",
        "bye",
        "goodbye",
    }

    return normalized in greetings


@router.post("/stream")
def chat_stream(request: ChatRequest):
    """Stream an answer and append only page numbers."""

    question = request.question.strip()

    # Handle greetings without searching the manual.
    if is_greeting(question):

        def greeting_response() -> Iterator[str]:
            yield (
                "Hi! I'm TechManual AI. You can ask me questions "
                "about the technical manual you've uploaded."
            )

        return StreamingResponse(
            greeting_response(),
            media_type="text/plain; charset=utf-8",
        )

    # Retrieve relevant manual chunks.
    chunks = retrieve_relevant_chunks(
        question,
        k=request.k,
    )

    def generate() -> Iterator[str]:

        if not chunks:
            yield (
                "I couldn't find relevant information in the "
                "uploaded manual."
            )
            return

        # Stream the LLM answer without source citations.
        yield from stream_answer(question, chunks)

        # Append unique page numbers once, at the end.
        pages = sorted({
            chunk["page"]
            for chunk in chunks
            if chunk.get("page") is not None
        })

        if pages:
            page_text = ", ".join(str(page) for page in pages)
            yield f"\n\nPages: {page_text}"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
    )
