import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PSLE Practice",
  description: "Gamified, syllabus-anchored PSLE MCQ practice with feedback.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <div className="row" style={{ marginBottom: 8 }}>
            <a href="/"><strong>🧠 PSLE Practice</strong></a>
            <span className="spacer" />
            <a href="/practice" className="badge">Practice</a>
            <a href="/dashboard" className="badge">Dashboard</a>
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
