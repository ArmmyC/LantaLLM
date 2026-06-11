const baseURL = process.env.OPENAI_BASE_URL || "http://localhost:8000/v1";
const apiKey = process.env.OPENAI_API_KEY || "EMPTY";
const model =
  process.env.MODEL ||
  "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B";

const response = await fetch(`${baseURL}/chat/completions`, {
  method: "POST",
  headers: {
    "content-type": "application/json",
    authorization: `Bearer ${apiKey}`,
  },
  body: JSON.stringify({
    model,
    messages: [
      {
        role: "user",
        content: "Reply with one short sentence: SiliconCraft API is online.",
      },
    ],
    temperature: 0.6,
    top_p: 0.95,
    max_tokens: 64,
    chat_template_kwargs: { enable_thinking: false },
  }),
});

if (!response.ok) {
  console.error(await response.text());
  process.exit(1);
}

const data = await response.json();
console.log(data.choices?.[0]?.message?.content ?? data);
