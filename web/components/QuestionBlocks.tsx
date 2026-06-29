import { Question } from "@/lib/types";

// Renders a question stem from its structured blocks (text / image / table),
// falling back to plain text. Keeps PSLE figures + tables intact.
export default function QuestionBlocks({ q }: { q: Question }) {
  const blocks = q.stem_blocks && q.stem_blocks.length
    ? q.stem_blocks
    : [{ type: "text" as const, text: q.stem }];

  return (
    <div>
      {blocks.map((b, i) => {
        if (b.type === "image" && b.src) {
          return (
            <img key={i} src={b.src} alt={b.alt || ""}
                 style={{ maxWidth: "100%", borderRadius: 10, border: "3px solid var(--line)", margin: "8px 0" }} />
          );
        }
        if (b.type === "table" && b.rows?.length) {
          return (
            <table key={i} style={{ borderCollapse: "collapse", margin: "10px 0", width: "100%" }}>
              {b.header?.length ? (
                <thead><tr>{b.header.map((h, j) => (
                  <th key={j} style={cell(true)}>{h}</th>
                ))}</tr></thead>
              ) : null}
              <tbody>{b.rows.map((r, ri) => (
                <tr key={ri}>{r.map((c, ci) => <td key={ci} style={cell(false)}>{c}</td>)}</tr>
              ))}</tbody>
            </table>
          );
        }
        return <h2 key={i} style={{ margin: "6px 0" }}>{b.text}</h2>;
      })}
    </div>
  );
}

function cell(head: boolean): React.CSSProperties {
  return {
    border: "2px solid var(--line)", padding: "8px 12px", textAlign: "left",
    background: head ? "var(--gold)" : "#fff",
    fontFamily: head ? "ui-monospace, monospace" : "inherit", fontWeight: head ? 800 : 400,
  };
}
