import { createServer } from "node:http";

const listenHost = process.env.HOST || "127.0.0.1";
const listenPort = Number.parseInt(process.env.PORT || "3001", 10);
const upstreamBase = (process.env.OPENAI_BASE_URL || "http://127.0.0.1:8000/v1").replace(/\/+$/, "");
const upstreamKey = process.env.OPENAI_API_KEY || "EMPTY";
const corsOrigin = process.env.CORS_ORIGIN || "*";
const apiTokens = (process.env.API_TOKENS || process.env.API_TOKEN || "")
  .split(",")
  .map((token) => token.trim())
  .filter(Boolean);

const hopByHopHeaders = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function writeCors(res) {
  res.setHeader("Access-Control-Allow-Origin", corsOrigin);
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
}

function sendJson(res, statusCode, body) {
  writeCors(res);
  res.writeHead(statusCode, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

function checkToken(req) {
  if (apiTokens.length === 0) return false;
  const header = req.headers.authorization || "";
  if (!header.startsWith("Bearer ")) return false;
  return apiTokens.includes(header.slice("Bearer ".length).trim());
}

async function pipeWebStream(stream, res) {
  if (!stream) {
    res.end();
    return;
  }

  const reader = stream.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!res.write(Buffer.from(value))) {
        await new Promise((resolve) => res.once("drain", resolve));
      }
    }
  } finally {
    reader.releaseLock();
    res.end();
  }
}

const server = createServer(async (req, res) => {
  writeCors(res);

  if (req.method === "OPTIONS") {
    res.writeHead(204);
    res.end();
    return;
  }

  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

  if (url.pathname === "/healthz") {
    sendJson(res, 200, {
      ok: true,
      auth: "required",
      upstream: upstreamBase,
    });
    return;
  }

  if (!url.pathname.startsWith("/v1/")) {
    sendJson(res, 404, { error: "Only /v1/* routes are proxied." });
    return;
  }

  if (!checkToken(req)) {
    sendJson(res, 401, { error: "Missing or invalid bearer token." });
    return;
  }

  const upstreamUrl = `${upstreamBase}${url.pathname.slice("/v1".length)}${url.search}`;
  const headers = new Headers();

  for (const [name, value] of Object.entries(req.headers)) {
    const lower = name.toLowerCase();
    if (hopByHopHeaders.has(lower) || lower === "authorization" || lower === "host") {
      continue;
    }
    if (value !== undefined) {
      headers.set(name, Array.isArray(value) ? value.join(",") : value);
    }
  }

  headers.set("authorization", `Bearer ${upstreamKey}`);

  try {
    const upstream = await fetch(upstreamUrl, {
      method: req.method,
      headers,
      body: req.method === "GET" || req.method === "HEAD" ? undefined : req,
      duplex: "half",
    });

    for (const [name, value] of upstream.headers) {
      if (!hopByHopHeaders.has(name.toLowerCase())) {
        res.setHeader(name, value);
      }
    }

    writeCors(res);
    res.writeHead(upstream.status);
    await pipeWebStream(upstream.body, res);
  } catch (error) {
    sendJson(res, 502, {
      error: "Upstream vLLM request failed.",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
});

server.listen(listenPort, listenHost, () => {
  console.log(`Qwen gateway listening on http://${listenHost}:${listenPort}`);
  console.log(`Proxying OpenAI-compatible requests to ${upstreamBase}`);
  console.log(`Accepted API tokens: ${apiTokens.length}`);
});
