import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function ChecksTable({ checks }) {
    const ICON = { pass: "✅", fail: "❌", error: "⚠️", skip: "–" };
    return (_jsxs("table", { style: { width: "100%", borderCollapse: "collapse", marginTop: "1rem" }, children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { style: { textAlign: "left", padding: "0.4rem 0.8rem", borderBottom: "1px solid #333" }, children: "Check" }), _jsx("th", { style: { textAlign: "left", padding: "0.4rem 0.8rem", borderBottom: "1px solid #333" }, children: "Result" })] }) }), _jsx("tbody", { children: Object.entries(checks).map(([k, v]) => (_jsxs("tr", { children: [_jsx("td", { style: { padding: "0.4rem 0.8rem", textTransform: "capitalize" }, children: k }), _jsxs("td", { style: { padding: "0.4rem 0.8rem" }, children: [ICON[v] ?? v, " ", v] })] }, k))) })] }));
}
