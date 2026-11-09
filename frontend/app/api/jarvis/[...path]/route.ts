import { NextRequest } from "next/server";
export const runtime = "nodejs";
async function proxy(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const path = (await params).path.join("/");
  if (
    !/^(status|catalog|diagnostics|analysis|chat|investigations|audit|conversations(?:\/[a-f0-9-]{36})?|memories(?:\/[a-f0-9-]{36}(?:\/revisions)?)?)$/.test(
      path,
    )
  )
    return Response.json({ detail: "Rota inválida" }, { status: 404 });
  if (process.env.JARVIS_WEB_PREVIEW === "true") {
    const { webPreview } = await import("../../../../lib/web-preview");
    return webPreview(req, path);
  }
  const root = process.env.JARVIS_API_URL || (process.env.JARVIS_API_HOST ? `https://${process.env.JARVIS_API_HOST}` : "http://127.0.0.1:8010");
  const url = new URL(root);
  if (process.env.NODE_ENV === "production" && url.protocol !== "https:")
    return Response.json(
      { detail: "Configure JARVIS_API_URL com HTTPS." },
      { status: 503 },
    );
  const auth = req.headers.get("authorization") || "";
  if (!auth.startsWith("Bearer ") || auth.length < 39 || auth.length > 263)
    return Response.json(
      { detail: "Autenticação necessária." },
      { status: 401 },
    );
  let body: Uint8Array | undefined;
  if (req.method !== "GET") {
    const chunks: Uint8Array[] = [];
    let length = 0;
    const reader = req.body?.getReader();
    if (reader) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        length += value.length;
        if (length > 64000) {
          await reader.cancel();
          return Response.json(
            { detail: "Requisição muito grande." },
            { status: 413 },
          );
        }
        chunks.push(value);
      }
    }
    body = new Uint8Array(length);
    let offset = 0;
    for (const c of chunks) {
      body.set(c, offset);
      offset += c.length;
    }
  }
  try {
    const response = await fetch(
      root.replace(/\/$/, "") + "/api/" + path + req.nextUrl.search,
      {
        method: req.method,
        headers: { Authorization: auth, "Content-Type": "application/json", ...(process.env.JARVIS_BRIDGE_TOKEN ? { "X-Bridge-Token": process.env.JARVIS_BRIDGE_TOKEN } : {}) },
        body: body as BodyInit | undefined,
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(100000),
      },
    );
    if (!response.headers.get("content-type")?.includes("application/json"))
      throw new Error("Formato inválido");
    return new Response(await response.text(), {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        detail:
          "JARVIS indisponível. Confira o backend e a conexão com o Predator.",
      },
      { status: 503 },
    );
  }
}
export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
