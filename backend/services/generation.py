
from collections.abc import Iterator

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from backend.core.config import GROQ_API_KEY


def get_llm() -> ChatGroq:
    """Create the Groq chat model."""

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to the project root .env file."
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0,
        max_tokens=800,
        api_key=GROQ_API_KEY,
    )


def build_messages(question: str, context_chunks: list[dict]):
    """Prepare the question and retrieved manual context."""

    context = "\n\n".join(
        f"Source: {chunk['source']}, Page: {chunk['page']}\n"
        f"{chunk['content']}"
        for chunk in context_chunks
    )

    
    system_prompt = """
You are TechManual AI, an assistant for technicians and product support teams.

Answer the user's question using only the provided technical manual context.

Rules:
1. Give clear, practical, step-by-step answers when appropriate.
2. Do not invent error codes, specifications, or repair instructions.
3. If the context does not contain the answer, clearly say so.
4. NEVER include source citations, PDF filenames, document names,
   page numbers, reference links, or source labels inside your answer.
5. Do not write phrases such as "Source:", "Page:", or "According
   to the manual on page...".
6. Do not add a separate sources list.
7. Include relevant safety precautions for potentially hazardous repairs.
8. Keep the answer concise and easy to follow.
"""


    return [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"""
Question:
{question}

Retrieved manual context:
{context}

Answer based on the rules above.
"""
        ),
    ]


def stream_answer(
    question: str,
    context_chunks: list[dict],
) -> Iterator[str]:
    """Yield answer text as the model generates it."""

    if not context_chunks:
        yield "I couldn't find relevant information in the manual."
        return

    llm = get_llm()
    messages = build_messages(question, context_chunks)

    for chunk in llm.stream(messages):
        if isinstance(chunk.content, str) and chunk.content:
            yield chunk.content
