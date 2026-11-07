// app/api/explicar/route.ts (Next.js, App Router)
// Copie `explicar.mjs` e este arquivo para `app/api/explicar/` do app.
// Requer `"allowJs": true` no tsconfig (padrão do create-next-app).
import { tratar } from "./explicar.mjs";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "local";
  const r = await tratar({
    body,
    ip,
    env: { GEMINI_API_KEY: process.env.GEMINI_API_KEY, GEMINI_MODEL: process.env.GEMINI_MODEL },
  });
  return Response.json(r.json, { status: r.status, headers: { "cache-control": "no-store" } });
}
