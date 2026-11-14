import { useRef, useState } from "react";

import { type SingleResult, checkSingle } from "../api/single";
import { ChecksTable } from "../components/ChecksTable";
import { StatusBadge } from "../components/StatusBadge";

export function SingleCheck() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState<SingleResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const r = await checkSingle(email.trim());
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <h2 style={{ marginBottom: "1rem" }}>Single Email Check</h2>
      <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
        <input
          ref={inputRef}
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="user@example.com"
          required
          style={{
            flex: 1,
            minWidth: "16rem",
            padding: "0.6rem 1rem",
            borderRadius: "6px",
            border: "1px solid #333",
            background: "#1a1a1a",
            color: "#e8e8e8",
            fontSize: "1rem",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "0.6rem 1.5rem",
            borderRadius: "6px",
            border: "none",
            background: "#3b82f6",
            color: "#fff",
            fontWeight: 700,
            cursor: loading ? "wait" : "pointer",
            fontSize: "1rem",
          }}
        >
          {loading ? "Checking…" : "Check"}
        </button>
      </form>

      {error && (
        <p style={{ marginTop: "1rem", color: "#ef4444" }}>Error: {error}</p>
      )}

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <span style={{ fontSize: "0.9rem", color: "#aaa" }}>{result.address}</span>
            <StatusBadge status={result.status} />
          </div>
          <ChecksTable checks={result.checks} />
        </div>
      )}
    </section>
  );
}
