import "./globals.css";
import type { Metadata } from "next";
import Hud from "@/components/Hud";

export const metadata: Metadata = {
  title: "PSLE Quest — practice & master",
  description: "Gamified, syllabus-anchored PSLE MCQ practice with feedback.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="wrap">
          <div className="row" style={{ marginBottom: 10 }}>
            <a href="/" className="pixel" style={{ fontSize: 16 }}>
              🍄 PSLE&nbsp;Quest
            </a>
            <span className="spacer" />
            <a href="/" className="badge">Town</a>
            <a href="/practice" className="badge">Quest</a>
            <a href="/dashboard" className="badge">Stats</a>
          </div>
          <Hud />
          {children}
        </div>
      </body>
    </html>
  );
}
