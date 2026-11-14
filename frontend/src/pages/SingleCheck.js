import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useRef, useState } from "react";
import { checkSingle } from "../api/single";
import { ChecksTable } from "../components/ChecksTable";
import { StatusBadge } from "../components/StatusBadge";
export function SingleCheck() {
    const [email, setEmail] = useState("");
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const inputRef = useRef(null);
    async function handleSubmit(e) {
        e.preventDefault();
        setError(null);
        setResult(null);
        setLoading(true);
        try {
            const r = await checkSingle(email.trim());
            setResult(r);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
        }
        finally {
            setLoading(false);
        }
    }
    return (_jsxs("section", { children: [_jsx("h2", { style: { marginBottom: "1rem" }, children: "Single Email Check" }), _jsxs("form", { onSubmit: handleSubmit, style: { display: "flex", gap: "0.5rem", flexWrap: "wrap" }, children: [_jsx("input", { ref: inputRef, type: "text", value: email, onChange: (e) => setEmail(e.target.value), placeholder: "user@example.com", required: true, style: {
                            flex: 1,
                            minWidth: "16rem",
                            padding: "0.6rem 1rem",
                            borderRadius: "6px",
                            border: "1px solid #333",
                            background: "#1a1a1a",
                            color: "#e8e8e8",
                            fontSize: "1rem",
                        } }), _jsx("button", { type: "submit", disabled: loading, style: {
                            padding: "0.6rem 1.5rem",
                            borderRadius: "6px",
                            border: "none",
                            background: "#3b82f6",
                            color: "#fff",
                            fontWeight: 700,
                            cursor: loading ? "wait" : "pointer",
                            fontSize: "1rem",
                        }, children: loading ? "Checking…" : "Check" })] }), error && (_jsxs("p", { style: { marginTop: "1rem", color: "#ef4444" }, children: ["Error: ", error] })), result && (_jsxs("div", { style: { marginTop: "1.5rem" }, children: [_jsxs("div", { style: { display: "flex", alignItems: "center", gap: "1rem" }, children: [_jsx("span", { style: { fontSize: "0.9rem", color: "#aaa" }, children: result.address }), _jsx(StatusBadge, { status: result.status })] }), _jsx(ChecksTable, { checks: result.checks })] }))] }));
}
