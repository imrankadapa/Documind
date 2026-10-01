import React, { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import "./style.css";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 120000,
});

function fileType(filename) {
  return filename.split(".").pop()?.toUpperCase() || "FILE";
}

function App() {
  const inputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [online, setOnline] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api.get("/health").then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  async function uploadFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    setUploading(true);
    setNotice("");
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const response = await api.post("/documents/upload", formData);
      setDocuments((current) => [...current, ...(response.data.documents || [])]);
      const failed = response.data.failed || [];
      if (failed.length) {
        setNotice(`${failed[0].filename}: ${failed[0].error}`);
      }
    } catch (error) {
      setNotice(error.response?.data?.detail || "Upload failed. Check that FastAPI is running.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function askQuestion(event) {
    event.preventDefault();
    const cleanQuestion = question.trim();
    if (!cleanQuestion || thinking) return;

    setMessages((current) => [...current, { role: "user", text: cleanQuestion }]);
    setQuestion("");
    setThinking(true);
    setNotice("");

    try {
      const params = new URLSearchParams({ query: cleanQuestion });
      documents.forEach((document) => params.append("document_ids", document.document_id));
      const response = await api.get(`/llm?${params.toString()}`);
      setMessages((current) => [
        ...current,
        {
          role: "bot",
          text: response.data.answer || "No answer received.",
          sources: response.data.sources || [],
        },
      ]);
    } catch (error) {
      const message = error.response?.data?.detail || "Could not get an answer from the backend.";
      setNotice(message);
      setMessages((current) => [...current, { role: "bot", text: message }]);
    } finally {
      setThinking(false);
    }
  }

  function clearChat() {
    setMessages([]);
    setNotice("");
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">DocuMind</div>
        <div className="brand-sub">Document Q&amp;A</div>

        <div className="section-label">Upload a document</div>
        <label
          className="upload-zone"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            uploadFiles(event.dataTransfer.files);
          }}
        >
          <strong>{uploading ? "Processing documents..." : "Drop a file here"}</strong>
          {uploading ? "Extracting text and creating embeddings" : "or click to browse — PDF, DOCX, TXT"}
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            multiple
            onChange={(event) => uploadFiles(event.target.files)}
          />
        </label>

        <div className="section-label documents-label">Your documents</div>
        <div className="doc-list">
          {documents.length === 0 ? (
            <div className="empty-docs">No documents uploaded yet.</div>
          ) : (
            documents.map((document) => (
              <div className="doc-item" key={document.document_id}>
                <div className="doc-icon">{fileType(document.filename)}</div>
                <div className="doc-meta">
                  <div className="doc-name" title={document.filename}>{document.filename}</div>
                  <div className="doc-status">Ready · {document.chunks} chunks</div>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="sidebar-footer">
          {documents.length} document{documents.length === 1 ? "" : "s"} · local search
        </div>
      </aside>

      <main className="main">
        <header className="chat-header">
          <div>
            <h1>Ask your documents</h1>
            <p>Answers are grounded in the files on the left</p>
          </div>
          <div className={`pill ${online ? "" : "offline"}`}>
            ● {online ? "Connected" : "Offline"}
          </div>
        </header>

        <section className="thread">
          {messages.length === 0 && !thinking && (
            <div className="empty-chat">
              <div className="empty-mark">D</div>
              <h2>Start with a question</h2>
              <p>Upload a document, then ask about its content.</p>
            </div>
          )}

          {messages.map((message, index) => (
            <div className={`msg-row ${message.role}`} key={`${message.role}-${index}`}>
              <div className="bubble">
                {message.text}
                {message.sources?.length > 0 && (
                  <div className="source">
                    <b>Source</b>
                    {" — "}
                    {[...new Set(message.sources.map((source) => source.filename))].join(", ")}
                  </div>
                )}
              </div>
            </div>
          ))}

          {thinking && (
            <div className="msg-row bot">
              <div className="thinking">
                <span className="dot" /><span className="dot" /><span className="dot" />
                <span>Reading your documents…</span>
              </div>
            </div>
          )}
        </section>

        {notice && <div className="notice">{notice}</div>}

        <form className="composer" onSubmit={askQuestion}>
          <div className="composer-inner">
            <textarea
              rows="1"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your documents…"
            />
            <button className="send-btn" type="submit" aria-label="Send" disabled={thinking}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <div className="composer-footer">
            <span>Answers are generated from your uploaded documents only</span>
            <button type="button" onClick={clearChat}>Clear chat</button>
          </div>
        </form>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
