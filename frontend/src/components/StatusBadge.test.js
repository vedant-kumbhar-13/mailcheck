import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";
test("renders valid badge", () => {
    render(_jsx(StatusBadge, { status: "valid" }));
    expect(screen.getByText("valid")).toBeTruthy();
});
test("renders invalid badge", () => {
    render(_jsx(StatusBadge, { status: "invalid" }));
    expect(screen.getByText("invalid")).toBeTruthy();
});
