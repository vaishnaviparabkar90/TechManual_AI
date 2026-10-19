
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Question about the uploaded technical manual",
    )
    k: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of relevant chunks to retrieve",
    )


class SourceDocument(BaseModel):
    filename: str
    page: int


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceDocument]


class UploadResponse(BaseModel):
    filename: str
    pages_extracted: int
    chunks_created: int
    chunks_submitted: int
    status: str
