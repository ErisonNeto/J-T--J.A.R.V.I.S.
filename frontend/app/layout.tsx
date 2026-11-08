import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "JARVIS | J&T Express",
  description: "Inteligência operacional da regional Orlean",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  );
}
