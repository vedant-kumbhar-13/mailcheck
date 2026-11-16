import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { getResults } from "../api/bulk";
import { StatusBadge } from "./StatusBadge";
const STATUS_FILTER = ["all", "valid", "risky", "invalid", "unknown"];
const PAGE_SIZE = 100;
export function ResultsTable({ jobId, jobKey, total, }) {
    const [page, setPage] = useState(1);
    const [rows, setRows] = useState([]);
    const [loaded, setLoaded] = useState(false);
    const [filter, setFilter] = useState("all");
    async function load(p) {
        const data = await getResults(jobId, jobKey, p, PAGE_SIZE);
        setRows(data.results);
        setPage(p);
        setLoaded(true);
    }
    if (!loaded) {
        return (_jsx("button", { onClick: () => load(1), style: {
                marginTop: "1rem",
                padding: "0.5rem 1rem",
                borderRadius: "6px",
                border: "none",
                background: "#3b82f6",
                color: "#fff",
                cursor: "pointer",
            }, children: "Load Results" }));
    }
    const displayed = filter === "all" ? rows : rows.filter((r) => r.status === filter);
    const totalPages = Math.ceil(total / PAGE_SIZE);
    return (_jsxs("div", { style: { marginTop: "1.5rem" }, children: [_jsx("div", { style: { display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }, children: STATUS_FILTER.map((s) => (_jsx("button", { onClick: () => setFilter(s), style: {
                        padding: "0.25rem 0.75rem",
                        borderRadius: "9999px",
                        border: "1px solid #333",
                        background: filter === s ? "#3b82f6" : "#1a1a1a",
                        color: "#e8e8e8",
                        cursor: "pointer",
                        fontSize: "0.8rem",
                        textTransform: "capitalize",
                    }, children: s }, s))) }), _jsx("div", { style: { overflowX: "auto" }, children: _jsxs("table", { style: { width: "100%", borderCollapse: "collapse", fontSize: "0.875rem" }, children: [_jsx("thead", { children: _jsx("tr", { style: { borderBottom: "1px solid #333" }, children: ["Address", "Status", "Disposable", "Role", "Domain"].map((h) => (_jsx("th", { style: { padding: "0.5rem 0.75rem", textAlign: "left", color: "#aaa" }, children: h }, h))) }) }), _jsx("tbody", { children: displayed.map((row, i) => (_jsxs("tr", { style: { borderBottom: "1px solid #222" }, children: [_jsx("td", { style: { padding: "0.4rem 0.75rem" }, children: row.address }), _jsx("td", { style: { padding: "0.4rem 0.75rem" }, children: _jsx(StatusBadge, { status: row.status }) }), _jsx("td", { style: { padding: "0.4rem 0.75rem" }, children: row.is_disposable ? "Yes" : "No" }), _jsx("td", { style: { padding: "0.4rem 0.75rem" }, children: row.is_role ? "Yes" : "No" }), _jsx("td", { style: { padding: "0.4rem 0.75rem", color: "#888" }, children: row.domain })] }, i))) })] }) }), _jsxs("div", { style: { display: "flex", gap: "0.5rem", marginTop: "1rem", alignItems: "center" }, children: [_jsx("button", { disabled: page <= 1, onClick: () => load(page - 1), style: { padding: "0.3rem 0.75rem", cursor: page > 1 ? "pointer" : "not-allowed" }, children: "\u2190 Prev" }), _jsxs("span", { style: { fontSize: "0.85rem", color: "#aaa" }, children: ["Page ", page, " of ", totalPages] }), _jsx("button", { disabled: page >= totalPages, onClick: () => load(page + 1), style: {
                            padding: "0.3rem 0.75rem",
                            cursor: page < totalPages ? "pointer" : "not-allowed",
                        }, children: "Next \u2192" })] })] }));
}
