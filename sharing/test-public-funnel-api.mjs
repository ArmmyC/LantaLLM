const baseURL = (process.env.OPENAI_BASE_URL || "").replace(/\/+$/, "");
const apiKey = process.env.OPENAI_API_KEY || "";
const model =
  process.env.MODEL ||
  "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B";

if (!baseURL || !apiKey) {
  console.error("Set OPENAI_BASE_URL and OPENAI_API_KEY first.");
  console.error("Example:");
  console.error("  $env:OPENAI_BASE_URL='https://YOUR-DEVICE.YOUR-TAILNET.ts.net/v1'");
  console.error("  $env:OPENAI_API_KEY='TOKEN_FROM_SHARE_SCRIPT'");
  process.exit(1);
}

const response = await fetch(`${baseURL}/chat/completions`, {
  method: "POST",
  headers: {
    "content-type": "application/json",
    authorization: `Bearer ${apiKey}`,
  },
  body: JSON.stringify({
    model,
    messages: [{ role: "user", content: "Say hello to my friend in one sentence." }],
    max_tokens: 128,
    temperature: 0.6,
    chat_template_kwargs: { enable_thinking: false },
  }),
});

const data = await response.json();
if (!response.ok) {
  console.error(JSON.stringify(data, null, 2));
  process.exit(1);
}

console.log(data.choices?.[0]?.message?.content ?? data);
