const DEFAULT_MODEL = "qwen36-27b";

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing environment variable: ${name}`);
  return value;
}

function isAuthorized(req) {
  const sitePassword = process.env.SITE_PASSWORD || "";
  if (!sitePassword) return true;

  const header = req.headers["x-site-password"] || req.headers.get?.("x-site-password");
  return header === sitePassword;
}

async function readJson(req) {
  if (typeof req.json === "function") return req.json();
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") return JSON.parse(req.body || "{}");

  let body = "";
  for await (const chunk of req) body += chunk;
  return JSON.parse(body || "{}");
}

function normalizeMessages(messages, fileContext) {
  const safeMessages = Array.isArray(messages) ? messages.slice(-30) : [];
  const normalized = safeMessages
    .filter((message) => message && ["system", "user", "assistant"].includes(message.role))
    .map((message) => ({
      role: message.role,
      content: String(message.content || "").slice(0, 120000),
    }));

  if (fileContext) {
    const attachment = String(fileContext).slice(0, 160000);
    const lastUserIndex = normalized.findLastIndex((message) => message.role === "user");
    const attachmentBlock = [
      "The user attached the following text file. Read it and use it to answer the request below.",
      "<attached_file>",
      attachment,
      "</attached_file>",
    ].join("\n");

    if (lastUserIndex >= 0) {
      normalized[lastUserIndex].content = `${attachmentBlock}\n\n<user_request>\n${normalized[lastUserIndex].content}\n</user_request>`;
    } else {
      normalized.push({ role: "user", content: attachmentBlock });
    }
  }

  return normalized;
}

export async function handleChatRequest(req) {
  if (req.method !== "POST") {
    return jsonResponse(405, { error: "Method not allowed" });
  }

  if (!isAuthorized(req)) {
    return jsonResponse(401, { error: "Invalid site password" });
  }

  let body;
  try {
    body = await readJson(req);
  } catch {
    return jsonResponse(400, { error: "Invalid JSON body" });
  }

  let upstreamBase;
  let upstreamKey;
  try {
    upstreamBase = requireEnv("QWEN_BASE_URL").replace(/\/+$/, "");
    upstreamKey = requireEnv("QWEN_API_KEY");
  } catch (error) {
    return jsonResponse(500, { error: error.message });
  }

  const model = String(body.model || process.env.QWEN_MODEL || DEFAULT_MODEL);
  const maxTokens = Math.min(Math.max(Number.parseInt(body.max_tokens || "1024", 10), 1), 32768);
  const temperature = Math.min(Math.max(Number.parseFloat(body.temperature ?? "0.7"), 0), 2);
  const thinking = Boolean(body.thinking);
  const stream = Boolean(body.stream);
  const messages = normalizeMessages(body.messages, body.file_context);

  if (messages.length === 0) {
    return jsonResponse(400, { error: "At least one message is required" });
  }

  const upstreamBody = {
    model,
    messages,
    max_tokens: maxTokens,
    temperature,
    stream,
    chat_template_kwargs: { enable_thinking: thinking },
  };

  try {
    const upstream = await fetch(`${upstreamBase}/chat/completions`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${upstreamKey}`,
      },
      body: JSON.stringify(upstreamBody),
    });

    if (!upstream.ok) {
      const text = await upstream.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        data = { raw: text };
      }
      return jsonResponse(upstream.status, {
        error: "Upstream model request failed",
        detail: data,
      });
    }

    if (stream && upstream.body) {
      return new Response(upstream.body, {
        status: 200,
        headers: {
          "content-type": upstream.headers.get("content-type") || "text/event-stream; charset=utf-8",
          "cache-control": "no-cache, no-transform",
          connection: "keep-alive",
          "x-accel-buffering": "no",
        },
      });
    }

    const text = await upstream.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }

    return jsonResponse(200, data);
  } catch (error) {
    return jsonResponse(502, {
      error: "Could not reach upstream model API",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
}

export default async function handler(req, res) {
  const response = await handleChatRequest(req);

  if (!res) return response;

  res.statusCode = response.status;
  for (const [name, value] of response.headers) {
    res.setHeader(name, value);
  }

  if (!response.body) {
    res.end();
    return;
  }

  const reader = response.body.getReader();
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      res.write(Buffer.from(value));
    }
  } finally {
    res.end();
    reader.releaseLock();
  }
}
