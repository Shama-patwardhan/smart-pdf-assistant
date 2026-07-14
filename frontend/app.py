"""Streamlit frontend for the Smart PDF Assistant.

Interacts with the FastAPI backend to support PDF document ingestion, index listings,
and grounded question answering over document vector stores with visual confidence scores.
"""

import os
import streamlit as st
import requests
from pathlib import Path

# Page Layout Configurations
st.set_page_config(
    page_title="Smart PDF Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration Constants
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CSS_PATH = Path(__file__).resolve().parent / "assets" / "custom_styles.css"


def inject_custom_css() -> None:
    """Reads the custom CSS file and injects it into Streamlit's head."""
    if CSS_PATH.exists():
        try:
            with open(CSS_PATH, "r") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading stylesheet: {e}")
    else:
        st.warning("Custom stylesheet assets/custom_styles.css not found.")


def init_session_state() -> None:
    """Initializes chat history and active states on session load."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_document" not in st.session_state:
        st.session_state.selected_document = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = set()


def fetch_documents() -> list:
    """Fetches the list of all indexed documents from the backend API.

    Returns:
        list: A list of dictionaries representing indexed document summaries.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/documents/", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document index list. HTTP {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.sidebar.error("Backend server is unreachable. Check connection.")
        return []


def upload_document(uploaded_file) -> None:
    """Uploads a PDF file to the backend pipeline.

    Args:
        uploaded_file: The Streamlit UploadedFile object.
    """
    if uploaded_file is None:
        return

    # Check file size locally before sending
    file_bytes = uploaded_file.getvalue()
    if len(file_bytes) > 20 * 1024 * 1024:
        st.sidebar.error("File size exceeds 20 MB limit.")
        return

    files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
    
    with st.spinner(f"Ingesting & indexing {uploaded_file.name}..."):
        try:
            response = requests.post(f"{API_BASE_URL}/upload/", files=files, timeout=120)
            if response.status_code == 201:
                result = response.json()
                st.session_state.uploaded_files.add(uploaded_file.name)
                st.sidebar.success(
                    f"Uploaded successfully!\n"
                    f"Pages: {result.get('page_count')} | Chunks: {result.get('chunk_count')}"
                )
                st.rerun()
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown backend processing error.")
                except ValueError:
                    error_detail = response.text
                st.sidebar.error(f"Upload failed: {error_detail}")
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Failed to connect to upload service: {e}")


def remove_document(filename: str) -> None:
    """Instructs the backend to delete the document and its associated vectors.

    Args:
        filename: Name of the PDF file to delete.
    """
    with st.spinner(f"Removing {filename}..."):
        try:
            # URL encode filename space components
            encoded_name = requests.utils.quote(filename)
            response = requests.delete(f"{API_BASE_URL}/documents/{encoded_name}", timeout=30)
            if response.status_code == 200:
                st.sidebar.success(f"Deleted '{filename}' successfully.")
                if st.session_state.selected_document == filename:
                    st.session_state.selected_document = None
                st.rerun()
            else:
                try:
                    error_detail = response.json().get("detail", "Failed to delete file.")
                except ValueError:
                    error_detail = response.text
                st.sidebar.error(f"Deletion failed: {error_detail}")
        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Failed to connect to document deletion service: {e}")


def handle_ask_question(question: str) -> None:
    """Submits a chat question, retrieves answers, and updates st.session_state.

    Args:
        question: User query text.
    """
    if not question or not question.strip():
        return

    # Add user query to conversation history representation
    st.session_state.messages.append({"role": "user", "content": question.strip()})

    # Prepare chat payload
    payload = {
        "question": question.strip(),
        "filename": st.session_state.selected_document
    }

    # API Request execution
    try:
        response = requests.post(f"{API_BASE_URL}/chat/", json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            st.session_state.messages.append({
                "role": "assistant",
                "content": result.get("answer", "No answer resolved."),
                "confidence": result.get("confidence", 0.0),
                "sources": result.get("sources", [])
            })
        else:
            try:
                error_detail = response.json().get("detail", "Error resolving answer.")
            except ValueError:
                error_detail = response.text
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🚨 **Error responding to query:** {error_detail}",
                "confidence": 0.0,
                "sources": []
            })
    except requests.exceptions.RequestException as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"🚨 **Connection Error:** Backend server is currently unreachable. Error description: {str(e)}",
            "confidence": 0.0,
            "sources": []
        })


def get_confidence_class(score: float) -> tuple:
    """Returns CSS badge class and rating string for confidence metrics.

    Args:
        score: The float confidence score (0.0 to 1.0).

    Returns:
        tuple: (css class name, readable score rating)
    """
    if score >= 0.70:
        return "confidence-high", f"High ({score * 100:.1f}%)"
    elif score >= 0.40:
        return "confidence-medium", f"Moderate ({score * 100:.1f}%)"
    else:
        return "confidence-low", f"Low / Groundless ({score * 100:.1f}%)"


def main() -> None:
    """Renders the Streamlit application layout."""
    # 1. Initialize custom CSS and states
    inject_custom_css()
    init_session_state()

    # 2. Sidebar Navigation Layout
    st.sidebar.markdown("### 🤖 Smart PDF Assistant")
    st.sidebar.markdown("---")

    # Document Uploader Section
    st.sidebar.subheader("Ingest Documents")
    uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF document (Max 20MB)",
    type=["pdf"],
    help="PDF is processed and converted into overlapping vector text chunks.",
    label_visibility="collapsed"
)

    if uploaded_file is not None:

        if uploaded_file.name in st.session_state.uploaded_files:
            st.sidebar.success("✅ This document has already been uploaded.")

        elif st.sidebar.button("📤 Upload PDF", use_container_width=True):
            upload_document(uploaded_file)

    st.sidebar.markdown("---")

    # Document list section
    st.sidebar.subheader("Indexed Documents")
    documents = fetch_documents()

    if not documents:
        st.sidebar.info("No documents indexed yet. Upload a PDF above to begin.")
    else:
        # Create dropdown to filter conversation scope globally or to a specific PDF
        doc_options = [None] + [doc["filename"] for doc in documents]
        doc_display = {None: "🌍 Search All Documents"}
        for doc in documents:
            doc_display[doc["filename"]] = f"📄 {doc['filename']}"

        st.session_state.selected_document = st.sidebar.selectbox(
            "Search Scope",
            options=doc_options,
            format_func=lambda x: doc_display[x],
            help="Scope chat queries to a specific PDF index or query globally."
        )

        st.sidebar.markdown("<br>", unsafe_allow_html=True)

        # Document cards display with counts & deletes
        for doc in documents:
            filename = doc["filename"]
            page_count = doc["page_count"]
            chunk_count = doc["chunk_count"]

            card_html = f"""
            <div class="document-card">
                <div class="document-title">{filename}</div>
                <div class="document-stats">
                    <span>📄 {page_count} pages</span>
                    <span>🧩 {chunk_count} chunks</span>
                </div>
            </div>
            """
            st.sidebar.markdown(card_html, unsafe_allow_html=True)
            
            # Delete button using uniquely structured keys
            col1, col2 = st.sidebar.columns([4, 1])
            with col2:
                # Wrap inside red styling container
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"delete_btn_{filename}"):
                    remove_document(filename)
                st.markdown('</div>', unsafe_allow_html=True)

    # Sidebar utility actions
    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    # 3. Main Chat Interface Panel
    st.title("Smart PDF Assistant 💬")
    st.markdown(
        "Ask questions grounded strictly to the uploaded PDF documents. "
        "The assistant retrieves supporting contexts and computes answer reliability metrics."
    )

    # Empty State Welcome Card
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="chat-bubble assistant-bubble">
                <div class="avatar assistant-avatar">AI</div>
                <div class="bubble-content">
                    <p><b>Welcome to Smart PDF Assistant!</b></p>
                    <p>Get started by uploading a PDF document in the sidebar. Once indexed, you can ask questions 
                    based on its contents. The assistant will search the text, cite source pages, and provide a 
                    grounded response.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Render Active Conversation Message History
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            user_html = f"""
            <div class="chat-bubble user-bubble">
                <div class="avatar user-avatar">ME</div>
                <div class="bubble-content">
                    <p>{content}</p>
                </div>
            </div>
            """
            st.markdown(user_html, unsafe_allow_html=True)
        else:
            confidence = msg.get("confidence", 0.0)
            sources = msg.get("sources", [])
            badge_class, badge_label = get_confidence_class(confidence)

            # Standard markdown formatting for assistant output
            st.markdown(
                f"""
                <div class="chat-bubble assistant-bubble">
                    <div class="avatar assistant-avatar">AI</div>
                    <div class="bubble-content">
                        <div>{content}</div>
                        <div class="confidence-badge {badge_class}">
                            <span>🛡️ Confidence Score: {badge_label}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Document Citation Sources dropdown list
            if sources:
                with st.expander(f"🔍 View Sources ({len(sources)} chunks matched)", expanded=False):
                    for src_idx, source in enumerate(sources):
                        src_name = source.get("filename", "Unknown")
                        src_page = source.get("page_number", 0)
                        src_text = source.get("chunk_text", "")
                        src_similarity = source.get("similarity_score", 0.0)

                        st.markdown(
                            f"""
                            <div class="source-container">
                                <div class="source-header">[Source {src_idx + 1}] - {src_name} (Page {src_page}) | Score: {src_similarity:.2f}</div>
                                <div>"{src_text}"</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # Question Input Bar at the Bottom
    user_query = st.chat_input("Ask a question about the indexed documents...")

    if user_query:
        # Avoid duplicate submissions
        if not st.session_state.messages or st.session_state.messages[-1]["content"] != user_query:
            with st.spinner("Analyzing context documents and drafting response..."):
                handle_ask_question(user_query)
            st.rerun()


if __name__ == "__main__":
    main()
