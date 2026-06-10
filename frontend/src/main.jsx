import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileText,
  Lock,
  LogOut,
  MessageSquare,
  Search,
  Shield,
  UploadCloud,
  Users,
  Workflow,
} from "lucide-react";
import { api, clearSession, getToken, getUser, setSession } from "./api";
import "./styles.css";

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: Activity },
  { id: "upload", label: "Documents", icon: UploadCloud },
  { id: "chat", label: "AI Chat", icon: MessageSquare },
  { id: "history", label: "History", icon: FileText },
  { id: "admin", label: "Admin", icon: Shield, adminOnly: true },
];

function Badge({ children, tone = "blue" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function Card({ title, icon: Icon, children, action }) {
  return (
    <section className="card">
      <div className="card-head">
        <div className="card-title">
          {Icon ? <Icon size={18} /> : null}
          <h3>{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = mode === "login" ? await api.login(email, password) : await api.register(email, password);
      setSession(data.access_token, data.user);
      onAuth(data.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-shell">
      <div className="auth-hero">
        <Badge>Enterprise AI Portfolio Project</Badge>
        <h1>Multi-Agent Enterprise RAG System</h1>
        <p>
          Upload company policies, manuals, HR documents, PDFs, DOCX, CSV, and Excel files. Ask source-grounded
          questions powered by LangGraph agents, FastAPI, OpenAI, Hugging Face embeddings, and ChromaDB.
        </p>
        <div className="hero-grid">
          <span><BrainCircuit size={18} /> LangGraph Agents</span>
          <span><Database size={18} /> Vector Search</span>
          <span><Shield size={18} /> JWT Auth</span>
          <span><Workflow size={18} /> Agent Workflow</span>
        </div>
      </div>

      <form className="auth-card" onSubmit={submit}>
        <Lock size={30} />
        <h2>{mode === "login" ? "Login" : "Create Account"}</h2>
        <p>Backend API: {api.baseUrl}</p>
        {error ? <div className="alert error">{error}</div> : null}
        <label>Email</label>
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className="primary" disabled={loading}>{loading ? "Please wait..." : mode === "login" ? "Login" : "Register"}</button>
        <button type="button" className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account? Register" : "Already have an account? Login"}
        </button>
      </form>
    </main>
  );
}

function Sidebar({ active, setActive, user, onLogout }) {
  const visible = navItems.filter((item) => !item.adminOnly || user?.is_admin);
  return (
    <aside className="sidebar">
      <div className="brand">
        <Bot />
        <div>
          <strong>Enterprise RAG</strong>
          <small>AI Knowledge System</small>
        </div>
      </div>
      <nav>
        {visible.map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.id} className={active === item.id ? "active" : ""} onClick={() => setActive(item.id)}>
              <Icon size={18} /> {item.label}
            </button>
          );
        })}
      </nav>
      <div className="profile">
        <div>{user?.email}</div>
        <small>{user?.is_admin ? "Administrator" : "User"}</small>
        <button onClick={onLogout}><LogOut size={16} /> Logout</button>
      </div>
    </aside>
  );
}

function Dashboard({ user }) {
  return (
    <div className="page-grid">
      <Card title="Architecture" icon={Workflow}>
        <div className="flow">
          {['Upload', 'Chunk', 'Embed', 'Retrieve', 'Analyze', 'Verify', 'Answer'].map((step) => <span key={step}>{step}</span>)}
        </div>
      </Card>
      <Card title="Technology Stack" icon={BrainCircuit}>
        <div className="stack-grid">
          <Badge>React</Badge><Badge>FastAPI</Badge><Badge>LangGraph</Badge><Badge>LangChain</Badge>
          <Badge>OpenAI</Badge><Badge>Hugging Face</Badge><Badge>ChromaDB</Badge><Badge>SQLite</Badge>
        </div>
      </Card>
      <Card title="Logged In" icon={Users}>
        <p>{user.email}</p>
        <Badge tone={user.is_admin ? "green" : "blue"}>{user.is_admin ? "Admin" : "Standard User"}</Badge>
      </Card>
    </div>
  );
}

function Documents() {
  const [docs, setDocs] = useState([]);
  const [files, setFiles] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadDocs() {
    try { setDocs(await api.listDocuments()); } catch (err) { setMessage(err.message); }
  }
  useEffect(() => { loadDocs(); }, []);

  async function upload(e) {
    e.preventDefault();
    if (!files?.length) return setMessage("Choose at least one file.");
    setLoading(true); setMessage("");
    try {
      const data = await api.uploadDocuments(files);
      setMessage(`Uploaded ${data.uploaded.length} document(s).`);
      setFiles(null);
      await loadDocs();
    } catch (err) { setMessage(err.message); }
    finally { setLoading(false); }
  }

  async function remove(id) {
    if (!confirm("Delete this document and its vectors?")) return;
    try { await api.deleteDocument(id); await loadDocs(); } catch (err) { setMessage(err.message); }
  }

  return (
    <div className="page-grid single">
      <Card title="Upload Company Documents" icon={UploadCloud}>
        <form className="upload-box" onSubmit={upload}>
          <input type="file" multiple accept=".pdf,.docx,.txt,.csv,.xlsx,.xls" onChange={(e) => setFiles(e.target.files)} />
          <button className="primary" disabled={loading}>{loading ? "Indexing..." : "Upload & Index"}</button>
        </form>
        {message ? <div className="alert">{message}</div> : null}
      </Card>
      <Card title="Indexed Documents" icon={FileText}>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Filename</th><th>Type</th><th>Chunks</th><th>Action</th></tr></thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}><td>{d.id}</td><td>{d.filename}</td><td>{d.filetype}</td><td>{d.chunks}</td><td><button className="danger" onClick={() => remove(d.id)}>Delete</button></td></tr>
              ))}
              {!docs.length ? <tr><td colSpan="5">No documents uploaded yet.</td></tr> : null}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function Chat() {
  const [question, setQuestion] = useState("What is the company password policy?");
  const [topK, setTopK] = useState(5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask(e) {
    e.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try { setResult(await api.ask(question, Number(topK))); }
    catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  return (
    <div className="chat-layout">
      <Card title="Ask Your Enterprise Documents" icon={Search}>
        <form className="ask-form" onSubmit={ask}>
          <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows="5" />
          <div className="inline-controls">
            <label>Top K <input type="number" min="1" max="10" value={topK} onChange={(e) => setTopK(e.target.value)} /></label>
            <button className="primary" disabled={loading}>{loading ? "Running agents..." : "Ask AI"}</button>
          </div>
        </form>
        {error ? <div className="alert error">{error}</div> : null}
        {result ? <Answer result={result} /> : null}
      </Card>
      <Card title="Agent Workflow" icon={Workflow}>
        <WorkflowPanel steps={result?.workflow || []} />
      </Card>
    </div>
  );
}

function Answer({ result }) {
  return (
    <div className="answer">
      <h3>Final Answer</h3>
      <p>{result.answer}</p>
      <h3>Citations</h3>
      <div className="citations">
        {result.citations?.map((c, i) => (
          <div className="citation" key={`${c.chunk_id}-${i}`}>
            <strong>[Source {i + 1}] {c.source}</strong>
            <small>Page: {c.page} | Chunk: {c.chunk_id}</small>
            <p>{c.content_preview}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function WorkflowPanel({ steps }) {
  if (!steps.length) return <p className="muted">Workflow appears after asking a question.</p>;
  return (
    <div className="workflow-list">
      {steps.map((step, idx) => (
        <div className="workflow-step" key={`${step.agent}-${idx}`}>
          <CheckCircle2 size={18} />
          <div><strong>{step.agent}</strong><p>{step.detail}</p></div>
        </div>
      ))}
    </div>
  );
}

function History() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  const loadHistory = () => {
    setError("");
    api.history().then(setRows).catch((err) => setError(err.message));
  };

  useEffect(() => { loadHistory(); }, []);

  const deleteItem = async (id) => {
    if (!confirm("Delete this conversation from memory?")) return;
    try {
      await api.deleteHistoryItem(id);
      setRows((current) => current.filter((row) => row.id !== id));
      setStatus("Conversation deleted.");
    } catch (err) {
      setError(err.message);
    }
  };

  const clearAll = async () => {
    if (!rows.length) return;
    if (!confirm("Delete ALL conversation memory for your account?")) return;
    try {
      await api.clearHistory();
      setRows([]);
      setStatus("All conversation memory cleared.");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Card title="Conversation Memory" icon={MessageSquare}>
      <div className="history-toolbar">
        <p className="muted">Review or delete saved question-answer history for your account.</p>
        <button className="danger" onClick={clearAll} disabled={!rows.length}>Clear All</button>
      </div>
      {error ? <div className="alert error">{error}</div> : null}
      {status ? <div className="alert">{status}</div> : null}
      <div className="history-list">
        {rows.map((r) => (
          <div className="history-item" key={r.id}>
            <div className="history-item-head">
              <strong>{r.question}</strong>
              <button className="danger small-danger" onClick={() => deleteItem(r.id)}>Delete</button>
            </div>
            <p>{r.answer}</p>
            <small>{new Date(r.created_at).toLocaleString()}</small>
          </div>
        ))}
        {!rows.length ? <p className="muted">No chat history yet.</p> : null}
      </div>
    </Card>
  );
}

function Admin() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.adminDashboard().then(setData).catch((err) => setError(err.message)); }, []);
  if (error) return <div className="alert error">{error}</div>;
  if (!data) return <div className="muted">Loading admin dashboard...</div>;
  return (
    <div className="page-grid">
      <Card title="Users" icon={Users}><div className="metric">{data.users}</div></Card>
      <Card title="Documents" icon={FileText}><div className="metric">{data.documents}</div></Card>
      <Card title="Chat Messages" icon={MessageSquare}><div className="metric">{data.chat_messages}</div></Card>
      <Card title="Vector Database" icon={Database}><pre>{JSON.stringify(data.vector_stats, null, 2)}</pre></Card>
      <Card title="Recent Documents" icon={FileText}>
        <ul>{data.recent_documents?.map((name) => <li key={name}>{name}</li>)}</ul>
      </Card>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(getUser());
  const [active, setActive] = useState("dashboard");
  const isAuthenticated = useMemo(() => Boolean(getToken() && user), [user]);

  function logout() { clearSession(); setUser(null); setActive("dashboard"); }

  if (!isAuthenticated) return <AuthScreen onAuth={setUser} />;

  return (
    <div className="app-shell">
      <Sidebar active={active} setActive={setActive} user={user} onLogout={logout} />
      <main className="content">
        <div className="topbar">
          <div><h1>{navItems.find((item) => item.id === active)?.label || "Dashboard"}</h1><p>Production-style enterprise AI document assistant.</p></div>
          <Badge tone="green">API: {api.baseUrl}</Badge>
        </div>
        {active === "dashboard" && <Dashboard user={user} />}
        {active === "upload" && <Documents />}
        {active === "chat" && <Chat />}
        {active === "history" && <History />}
        {active === "admin" && user?.is_admin && <Admin />}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
