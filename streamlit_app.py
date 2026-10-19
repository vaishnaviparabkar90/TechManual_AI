
import requests
import streamlit as st

# -----------------------------
# Configuration
# -----------------------------
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="TechManual AI",
    page_icon="🔧",
    layout="wide",
)

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "upload_result" not in st.session_state:
    st.session_state.upload_result = None


# -----------------------------
# Backend health check
# -----------------------------
def check_backend() -> bool:
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            timeout=3,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


# -----------------------------
# PDF upload
# -----------------------------
def upload_manual(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }

    response = requests.post(
        f"{API_BASE_URL}/manuals/upload",
        files=files,
        timeout=(10, 300),
    )

    response.raise_for_status()
    return response.json()


# -----------------------------
# Stream the answer
# -----------------------------
def stream_answer(question: str, k: int = 4):
    payload = {
        "question": question,
        "k": k,
    }

    with requests.post(
        f"{API_BASE_URL}/chat/stream",
        json=payload,
        stream=True,
        timeout=(10, 300),
    ) as response:

        response.raise_for_status()
        response.encoding = "utf-8"

        # Yield text as it arrives from FastAPI.
        for text_chunk in response.iter_content(
            chunk_size=None,
            decode_unicode=True,
        ):
            if text_chunk:
                yield text_chunk


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("TechManual AI")
    st.caption("Technical Manual Assistant")
    st.info(
    "Upload and process a manual to get started. "
)

    st.divider()

    st.subheader("Upload a manual")

    uploaded_file = st.file_uploader(
        "Choose a technical manual PDF",
        type=["pdf"],
        help="Upload a product service or troubleshooting manual.",
    )

    if st.button(
        "Upload and process PDF",
        use_container_width=True,
        disabled=uploaded_file is None,
    ):
        try:
            with st.spinner("Extracting text and creating embeddings..."):
                result = upload_manual(uploaded_file)

            st.session_state.upload_result = result

            st.success("Manual processed successfully!")

        except requests.HTTPError as error:
            detail = error.response.text if error.response is not None else str(error)
            st.error(f"Upload failed: {detail}")

        except requests.RequestException as error:
            st.error(f"Could not connect to the backend: {error}")

    if st.session_state.upload_result:
        result = st.session_state.upload_result

        st.divider()
        st.subheader("Latest upload")
        st.write(f"**File:** {result['filename']}")
        st.write(f"**Pages extracted:** {result['pages_extracted']}")
        st.write(f"**Chunks created:** {result['chunks_created']}")
        st.write(f"**Status:** {result['status']}")

    st.divider()

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Check whether FastAPI is running.
    if check_backend():
        st.success("Backend connected")
    else:
        st.error("Backend offline. Start FastAPI first.")


# -----------------------------
# Main chat interface
# -----------------------------
st.title("TechManual AI")
st.badge("Your Technical Manual Assistant")
st.markdown(
    "Ask questions about technical manuals and get answers "
    "grounded in the retrieved manual content."
)



# Display previous messages.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# -----------------------------
# Ask a question
# -----------------------------
question = st.chat_input(
    "Ask a troubleshooting or technical question..."
)

if question:
    # Display and save the user's question.
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    # Retrieve and stream the answer through FastAPI.
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(
                stream_answer(question, k=4)
            )

            # Save the complete streamed response.
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

        except requests.HTTPError as error:
            detail = (
                error.response.text
                if error.response is not None
                else str(error)
            )
            st.error(f"Backend returned an error: {detail}")

        except requests.RequestException as error:
            st.error(f"Could not connect to the backend: {error}")

        except Exception as error:
            st.error(f"Something went wrong: {error}")
