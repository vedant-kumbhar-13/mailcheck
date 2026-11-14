import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

test("renders valid badge", () => {
  render(<StatusBadge status="valid" />);
  expect(screen.getByText("valid")).toBeTruthy();
});

test("renders invalid badge", () => {
  render(<StatusBadge status="invalid" />);
  expect(screen.getByText("invalid")).toBeTruthy();
});
