import "./globals.css";
import type { Metadata } from "next";
import { GameProvider } from "@/components/GameProvider";
import TopBar from "@/components/TopBar";
import Hud from "@/components/Hud";

export const metadata: Metadata = {
  title: "PSLE Quest — practice & master",
  description: "Gamified, syllabus-anchored PSLE MCQ practice with feedback.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <GameProvider>
          <div className="wrap">
            <TopBar />
            <Hud />
            {children}
          </div>
        </GameProvider>
      </body>
    </html>
  );
}
