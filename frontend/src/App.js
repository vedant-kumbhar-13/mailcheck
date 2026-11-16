import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { BulkCheck } from "./pages/BulkCheck";
import { SingleCheck } from "./pages/SingleCheck";
const TABS = ["single", "bulk"];
export default function App() {
    const [tab, setTab] = useState("single");
    return (_jsxs("main", { className: "app", children: [_jsxs("header", { style: { marginBottom: "2rem" }, children: [_jsx("h1", { children: "MailCheck" }), _jsx("p", { style: { color: "#888", marginTop: "0.25rem" }, children: "Privacy-first email validation" })] }), _jsx("nav", { style: { display: "flex", gap: "0.5rem", marginBottom: "2rem" }, children: TABS.map((t) => (_jsx("button", { onClick: () => setTab(t), style: {
                        padding: "0.5rem 1.25rem",
                        borderRadius: "6px",
                        border: "none",
                        background: tab === t ? "#3b82f6" : "#1a1a1a",
                        color: tab === t ? "#fff" : "#aaa",
                        cursor: "pointer",
                        fontWeight: tab === t ? 700 : 400,
                        textTransform: "capitalize",
                    }, children: t === "single" ? "Single Check" : "Bulk Check (CSV)" }, t))) }), tab === "single" && _jsx(SingleCheck, {}), tab === "bulk" && _jsx(BulkCheck, {})] }));
}
