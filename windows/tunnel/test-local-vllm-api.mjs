const baseURL = (process.env.OPENAI_BASE_URL || "http://localhost:8000/v1").replace(/\/+$/, "");
const apiKey = process.env.OPENAI_API_KEY || "EMPTY";
const model =
  process.env.MODEL ||
  "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B";

async function request(path, options = {}) {
  const response = await fetch(`${baseURL}${path}`, {
    ...options,
    headers: {
      authorization: `Bearer ${apiKey}`,
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }

  return data;
}

console.log(`Testing Qwen API at: ${baseURL}`);
console.log("");

console.log("1. Checking /v1/models...");
const models = await request("/models");
console.log(JSON.stringify(models, null, 2));

console.log("");
console.log("2. Sending chat completion...");
const completion = await request("/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model,
    messages: [
      {
        role: "user",
        content: "Reply in exactly five words: Lanta LLM API is online.",
      },
    ],
    max_tokens: 32,
    temperature: 0.2,
    chat_template_kwargs: { enable_thinking: false },
  }),
});

console.log(completion.choices?.[0]?.message?.content ?? completion);
console.log("");
console.log("OK: local Qwen API test passed.");
