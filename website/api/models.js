function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function isAuthorized(req) {
  const sitePassword = process.env.SITE_PASSWORD || "";
  if (!sitePassword) return true;

  const header = req.headers["x-site-password"] || req.headers.get?.("x-site-password");
  return header === sitePassword;
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value) throw new Error(`Missing environment variable: ${name}`);
  return value;
}

export async function handleModelsRequest(req) {
  if (req.method !== "GET") {
    return jsonResponse(405, { error: "Method not allowed" });
  }

  if (!isAuthorized(req)) {
    return jsonResponse(401, { error: "Invalid site password" });
  }

  let upstreamBase;
  let upstreamKey;
  try {
    upstreamBase = requireEnv("QWEN_BASE_URL").replace(/\/+$/, "");
    upstreamKey = requireEnv("QWEN_API_KEY");
  } catch (error) {
    return jsonResponse(500, { error: error.message });
  }

  try {
    const upstream = await fetch(`${upstreamBase}/models`, {
      headers: { authorization: `Bearer ${upstreamKey}` },
    });
    const text = await upstream.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { raw: text };
    }
    return jsonResponse(upstream.status, data);
  } catch (error) {
    return jsonResponse(502, {
      error: "Could not reach upstream model API",
      detail: error instanceof Error ? error.message : String(error),
    });
  }
}
