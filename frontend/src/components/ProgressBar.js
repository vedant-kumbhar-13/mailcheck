import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function ProgressBar({ done, total }) {
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;
    return (_jsxs("div", { style: { marginTop: "1rem" }, children: [_jsxs("div", { style: {
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.85rem",
                    color: "#aaa",
                }, children: [_jsx("span", { children: "Processing\u2026" }), _jsxs("span", { children: [done, " / ", total, " (", pct, "%)"] })] }), _jsx("div", { style: {
                    background: "#1a1a1a",
                    borderRadius: "4px",
                    height: "8px",
                    marginTop: "0.4rem",
                    overflow: "hidden",
                }, children: _jsx("div", { style: {
                        width: `${pct}%`,
                        height: "100%",
                        background: "#3b82f6",
                        transition: "width 0.4s ease",
                    } }) })] }));
}
