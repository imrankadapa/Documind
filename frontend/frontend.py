import requests
import streamlit as st

st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "documents" not in st.session_state:
    st.session_state.documents = []

try:
    health_response = requests.get("http://127.0.0.1:8000/health", timeout=2)
    backend_online = health_response.ok
except requests.RequestException:
    backend_online = False

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #0e1117;
    color: #f5f7fa;
}
[data-testid="stHeader"] {
    background: #0e1117;
}
[data-testid="stMainBlockContainer"] {
    max-width: 1180px;
    padding-top: 1.5rem;
    padding-bottom: 5rem;
}
[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.5rem 1.2rem;
}
[data-testid="stSidebar"] * {
    color: #f5f7fa;
}
.side-title {
    color: #f5f7fa;
    font-size: 1.15rem;
    font-weight: 700;
}
.side-subtitle, .subtitle, [data-testid="stSidebar"] small {
    color: #aab2c0;
}
.side-subtitle {
    margin-top: -0.2rem;
    margin-bottom: 1rem;
}
.section-label {
    color: #8b949e;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08rem;
    margin: 1.7rem 0 0.6rem;
}
.title {
    color: #f5f7fa;
    font-size: 2.35rem;
    font-weight: 700;
    letter-spacing: -0.04rem;
}
.subtitle {
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}
.top-line {
    align-items: center;
    border-bottom: 1px solid #30363d;
    display: flex;
    justify-content: space-between;
    margin-bottom: 1.3rem;
    padding-bottom: 1rem;
}
.status {
    background: #193b2b;
    border: 1px solid #2d8054;
    border-radius: 20px;
    color: #7ee2a8;
    font-size: 0.78rem;
    padding: 0.35rem 0.7rem;
}
.file-card {
    background: #1e2430;
    border: 1px solid #30363d;
    border-radius: 9px;
    margin: 0.5rem 0;
    padding: 0.65rem 0.75rem;
}
.file-name {
    color: #f5f7fa;
    font-size: 0.88rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.file-ready {
    color: #7ee2a8;
    font-size: 0.74rem;
}
[data-testid="stFileUploader"] section {
    background: #1e2430;
    border: 1px dashed #4f8bf9;
    border-radius: 12px;
    padding: 0.5rem;
}
[data-testid="stFileUploader"] button {
    background: #252b36;
    border: 1px solid #4f8bf9;
    color: #f5f7fa;
}
div.stButton > button {
    background: #4f8bf9;
    border: 1px solid #4f8bf9;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    transition: background 0.2s ease;
}
div.stButton > button:hover {
    background: #3b73d1;
    border-color: #3b73d1;
    color: white;
}
[data-testid="stChatMessage"] {
    background: #1e2430;
    border: 1px solid #30363d;
    border-radius: 12px;
    margin: 0 auto 0.8rem;
    max-width: 900px;
    padding: 0.75rem 1rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #18243b;
    border-color: #294a80;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background: #4f8bf9;
}
[data-testid="stChatMessage"] p {
    color: #f5f7fa;
}
[data-testid="stChatInput"] {
    background: #252b36;
    border: 1px solid #30363d;
    border-radius: 12px;
}
[data-testid="stChatInput"] textarea {
    color: #f5f7fa;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #8b949e;
}
[data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}
.welcome {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 16px;
    margin: 3rem auto 2rem;
    max-width: 700px;
    padding: 2.3rem;
    text-align: center;
}
.welcome-icon { font-size: 2.8rem; }
.welcome h2 { color: #f5f7fa; margin: 0.5rem 0; }
.welcome p, .welcome li { color: #aab2c0; }
.welcome ul {
    display: inline-block;
    padding-left: 1.2rem;
    text-align: left;
}
.example {
    background: #1e2430;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #aab2c0;
    display: inline-block;
    font-size: 0.85rem;
    margin: 0.2rem;
    padding: 0.45rem 0.65rem;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        '<div class="side-title">🤖 AI Knowledge Assistant</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="side-subtitle">Chat with your documents</div>',
        unsafe_allow_html=True,
    )
    if backend_online:
        st.success("Backend connected")
    else:
        st.warning("Start FastAPI to use chat")
    st.markdown('<div class="section-label">📁 DOCUMENTS</div>', unsafe_allow_html=True)

    files_to_upload = st.file_uploader(
        "Upload documents",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
    )

    if files_to_upload and st.button("Upload documents", use_container_width=True):
        files = [
            ("files", (file.name, file.getvalue(), file.type))
            for file in files_to_upload
        ]
        try:
            response = requests.post(
                "http://127.0.0.1:8000/documents/upload",
                files=files,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()
            st.session_state.documents.extend(result["documents"])
            st.session_state.document_ids = [
                document["document_id"]
                for document in st.session_state.documents
            ]
            st.success(result["message"])
            for failed in result.get("failed", []):
                st.warning(f"{failed['filename']}: {failed['error']}")
        except requests.RequestException as error:
            st.error(f"Upload failed: {error}")

    st.markdown(
        f'<div class="section-label">UPLOADED FILES · {len(st.session_state.documents)}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.documents:
        for document in st.session_state.documents:
            st.markdown(
                f"""
                <div class="file-card">
                    <div class="file-name">📄 {document['filename']}</div>
                    <div class="file-ready">● Ready for questions</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No documents uploaded yet.")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown(
    '<div class="top-line"><div class="title">🤖 AI Knowledge Assistant</div>'
    f'<div class="status">● {"Online" if backend_online else "Offline"}</div></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Ask questions and get clear answers from your documents.</div>',
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <div class="welcome-icon">🤖</div>
        <h2>Welcome to AI Knowledge Assistant</h2>
        <p>Upload a document from the sidebar and start asking questions.</p>
        <div class="example">Summarize this document</div>
        <div class="example">What are the main topics?</div>
        <div class="example">Explain the important points</div>
    </div>
    """, unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask anything about your documents..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Finding an answer..."):
            try:
                response = requests.get(
                    "http://127.0.0.1:8000/llm",
                    params=[
                        ("query", prompt),
                        *[
                            ("document_ids", document_id)
                            for document_id in st.session_state.get("document_ids", [])
                        ],
                    ],
                    timeout=70,
                )
                response.raise_for_status()
                data = response.json()
                answer = data.get("answer", "No answer received.")
                sources = data.get("sources", [])
                graph_facts = data.get("graph_facts", [])
            except requests.RequestException as error:
                if error.response is not None:
                    answer = error.response.json().get("detail", error.response.text)
                else:
                    answer = f"Could not connect to the backend: {error}"
                sources = []
                graph_facts = []

            st.write(answer)
            if sources:
                with st.expander(f"Sources ({len(sources)})"):
                    for source in sources:
                        citation = source.get(
                            "citation",
                            f"[Source {source.get('rank', '?')}]",
                        )
                        st.write(
                            f"**{citation}**"
                        )
                        st.caption(source.get("text", ""))
                        st.caption(
                            f"FAISS distance: {source.get('distance', 'unknown')}"
                        )
            if graph_facts:
                with st.expander(f"Knowledge graph ({len(graph_facts)})"):
                    for fact in graph_facts:
                        page = f", page {fact['page']}" if fact.get("page") else ""
                        st.write(f"🔗 {fact['name']} · {fact['filename']}{page}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
