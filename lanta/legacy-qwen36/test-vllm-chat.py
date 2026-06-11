import os

from openai import OpenAI


base_url = os.environ.get("OPENAI_BASE_URL", "http://localhost:8000/v1")
model = os.environ.get(
    "MODEL",
    "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B",
)

client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Reply in exactly five words: SiliconCraft API is online.",
        }
    ],
    max_tokens=32,
    temperature=0.2,
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)

print(response.choices[0].message.content)
