import { useState } from "react";

import { BulkCheck } from "./pages/BulkCheck";
import { SingleCheck } from "./pages/SingleCheck";

const TABS = ["single", "bulk"] as const;
type Tab = (typeof TABS)[number];

export default function App() {
  const [tab, setTab] = useState<Tab>("single");

  return (
    <main className="app">
      <header style={{ marginBottom: "2rem" }}>
        <h1>MailCheck</h1>
        <p style={{ color: "#888", marginTop: "0.25rem" }}>Privacy-first email validation</p>
      </header>

      <nav style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "0.5rem 1.25rem",
              borderRadius: "6px",
              border: "none",
              background: tab === t ? "#3b82f6" : "#1a1a1a",
              color: tab === t ? "#fff" : "#aaa",
              cursor: "pointer",
              fontWeight: tab === t ? 700 : 400,
              textTransform: "capitalize",
            }}
          >
            {t === "single" ? "Single Check" : "Bulk Check (CSV)"}
          </button>
        ))}
      </nav>

      {tab === "single" && <SingleCheck />}
      {tab === "bulk" && <BulkCheck />}
    </main>
  );
}
