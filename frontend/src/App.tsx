import { SingleCheck } from "./pages/SingleCheck";

export default function App() {
  return (
    <main className="app">
      <header style={{ marginBottom: "2rem" }}>
        <h1>MailCheck</h1>
        <p style={{ color: "#888", marginTop: "0.25rem" }}>Privacy-first email validation</p>
      </header>
      <SingleCheck />
    </main>
  );
}
