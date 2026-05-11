import React, { useState, useEffect } from 'react';
import PipelineControl from './components/PipelineControl';

function App() {
  const [ingestionStatus, setIngestionStatus] = useState("Checking backend connection...");
  const [isConnected, setIsConnected] = useState(false);

  // Use 127.0.0.1 which is often more reliable than localhost on Windows
  const API_BASE = "http://127.0.0.1:8000";

  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        setIsConnected(true);
        setIngestionStatus("Connected to Backend");
      } else {
        setIngestionStatus("Backend Connected (Status: " + res.status + ")");
      }
    } catch (e) {
      console.error("Health check failed:", e);
      setIngestionStatus("Error: Backend not reachable");
      setIsConnected(false);
    }
  };

  const ingestData = async () => {
    try {
      setIngestionStatus("Ingesting...");
      const res = await fetch(`${API_BASE}/ingest`, { method: "POST" });
      const data = await res.json();
      setIngestionStatus(`Done. Ingested: ${data.tables.length} tables.`);
    } catch (e) {
      console.error("Ingest failed:", e);
      setIngestionStatus("Error connecting to backend");
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Agentic SQL-RAG</h1>
        <div className="actions" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span className="status" style={{
            color: ingestionStatus.includes("Error") ? '#da3633' : '#238636',
            borderColor: ingestionStatus.includes("Error") ? '#da3633' : '#238636',
            background: 'transparent'
          }}>
            {ingestionStatus}
          </span>
          <button className="ingest-btn" onClick={ingestData} disabled={!isConnected}>Ingest Data</button>
        </div>
      </header>

      <main>
        <PipelineControl apiBase={API_BASE} />
      </main>
    </div>
  );
}

export default App;
