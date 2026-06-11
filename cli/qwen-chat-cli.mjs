#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { createInterface } from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

const DEFAULT_MODEL =
  "/project/zz992000-zdevb/zz992005/ub127/SiliconCraft/models/Qwen3.6-35B-A3B";

function parseArgs(argv) {
  const options = {
    baseURL: process.env.OPENAI_BASE_URL || "http://127.0.0.1:8000/v1",
    apiKey: process.env.OPENAI_API_KEY || "EMPTY",
    model: process.env.MODEL || DEFAULT_MODEL,
    system: process.env.SYSTEM_PROMPT || "You are a helpful assistant.",
    temperature: Number.parseFloat(process.env.TEMPERATURE || "0.7"),
    maxTokens: Number.parseInt(process.env.MAX_TOKENS || "1024", 10),
    thinking: process.env.QWEN_THINKING === "1",
    stream: process.env.STREAM !== "0",
    files: [],
    prompt: [],
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];

    if (arg === "--base-url") options.baseURL = next();
    else if (arg === "--api-key") options.apiKey = next();
    else if (arg === "--model") options.model = next();
    else if (arg === "--system") options.system = next();
    else if (arg === "--temperature") options.temperature = Number.parseFloat(next());
    else if (arg === "--max-tokens") options.maxTokens = Number.parseInt(next(), 10);
    else if (arg === "--file" || arg === "-f") options.files.push(next());
    else if (arg === "--thinking") options.thinking = true;
    else if (arg === "--no-stream") options.stream = false;
    else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else {
      options.prompt.push(arg);
    }
  }

  options.baseURL = options.baseURL.replace(/\/+$/, "");
  options.prompt = options.prompt.join(" ").trim();
  return options;
}

function printHelp() {
  console.log(`Qwen3.6 local CLI

Usage:
  node cli/qwen-chat-cli.mjs "your question"
  node cli/qwen-chat-cli.mjs

Options:
  --base-url URL        OpenAI-compatible base URL, default OPENAI_BASE_URL or http://127.0.0.1:8000/v1
  --api-key KEY         Bearer token/API key, default OPENAI_API_KEY or EMPTY
  --model MODEL         Model id/path
  --system TEXT         System prompt
  --temperature N       Sampling temperature, default 0.7
  --max-tokens N        Max output tokens, default 1024
  --file PATH, -f PATH  Attach a local text file to the prompt. Can be repeated.
  --thinking            Enable Qwen thinking mode
  --no-stream           Print only after the response finishes

Interactive commands:
  /read PATH            Attach a local text file to the conversation
  /files                Show attached files
  /thinking             Toggle Qwen thinking mode
  /thinking on|off      Set Qwen thinking mode
  /clear                Reset chat and attached file context
  /exit                 Quit
`);
}

async function loadTextFile(filePath) {
  const absolutePath = resolve(process.cwd(), filePath);
  const maxBytes = Number.parseInt(process.env.MAX_FILE_BYTES || "200000", 10);
  const text = await readFile(absolutePath, "utf8");

  if (Buffer.byteLength(text, "utf8") > maxBytes) {
    throw new Error(`File is too large: ${absolutePath}. Limit is ${maxBytes} bytes.`);
  }

  return {
    requestedPath: filePath,
    absolutePath,
    text,
  };
}

async function loadFiles(filePaths) {
  const loaded = [];
  for (const filePath of filePaths) {
    loaded.push(await loadTextFile(filePath));
  }
  return loaded;
}

function filesToMessage(files) {
  if (files.length === 0) return null;

  const body = files
    .map((file) => {
      return [
        `File: ${file.requestedPath}`,
        `Absolute path: ${file.absolutePath}`,
        "```",
        file.text,
        "```",
      ].join("\n");
    })
    .join("\n\n");

  return {
    role: "user",
    content: `Use the following local file contents as context. Do not claim you read any other files.\n\n${body}`,
  };
}

async function chat(options, messages) {
  const response = await fetch(`${options.baseURL}/chat/completions`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${options.apiKey}`,
    },
    body: JSON.stringify({
      model: options.model,
      messages,
      temperature: options.temperature,
      max_tokens: options.maxTokens,
      stream: options.stream,
      chat_template_kwargs: { enable_thinking: options.thinking },
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }

  if (!options.stream) {
    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "";
    process.stdout.write(`${content}\n`);
    return content;
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let fullText = "";

  for await (const chunk of response.body) {
    buffer += decoder.decode(chunk, { stream: true });
    const lines = buffer.split(/\r?\n/);
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice("data: ".length).trim();
      if (!payload || payload === "[DONE]") continue;

      const data = JSON.parse(payload);
      const delta = data.choices?.[0]?.delta?.content || "";
      if (delta) {
        process.stdout.write(delta);
        fullText += delta;
      }
    }
  }

  process.stdout.write("\n");
  return fullText;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const messages = [{ role: "system", content: options.system }];
  const attachedFiles = [];

  if (options.files.length > 0) {
    const loaded = await loadFiles(options.files);
    attachedFiles.push(...loaded);
    const fileMessage = filesToMessage(loaded);
    if (fileMessage) messages.push(fileMessage);
  }

  if (options.prompt) {
    messages.push({ role: "user", content: options.prompt });
    await chat(options, messages);
    return;
  }

  console.log(`Qwen3.6 CLI connected to ${options.baseURL}`);
  console.log("Type /exit to quit, /clear to reset chat, /read PATH to attach a file.");
  console.log(`Thinking mode: ${options.thinking ? "on" : "off"}. Use /thinking to toggle.`);

  const rl = createInterface({ input, output });
  try {
    while (true) {
      const line = await rl.question("\nYou> ");
      const userInput = line.trim();
      if (!userInput) continue;
      if (userInput === "/exit" || userInput === "/quit") break;
      if (userInput === "/clear") {
        messages.splice(1);
        attachedFiles.splice(0);
        console.log("Chat cleared.");
        continue;
      }
      if (userInput === "/files") {
        if (attachedFiles.length === 0) {
          console.log("No files attached.");
        } else {
          for (const file of attachedFiles) console.log(file.absolutePath);
        }
        continue;
      }
      if (userInput === "/thinking" || userInput.startsWith("/thinking ")) {
        const value = userInput.slice("/thinking".length).trim().toLowerCase();
        if (!value) {
          options.thinking = !options.thinking;
        } else if (["on", "true", "1", "yes"].includes(value)) {
          options.thinking = true;
        } else if (["off", "false", "0", "no"].includes(value)) {
          options.thinking = false;
        } else {
          console.log("Usage: /thinking, /thinking on, or /thinking off");
          continue;
        }
        console.log(`Thinking mode: ${options.thinking ? "on" : "off"}`);
        continue;
      }
      if (userInput.startsWith("/read ")) {
        const filePath = userInput.slice("/read ".length).trim();
        if (!filePath) {
          console.log("Usage: /read PATH");
          continue;
        }

        try {
          const file = await loadTextFile(filePath);
          attachedFiles.push(file);
          const fileMessage = filesToMessage([file]);
          if (fileMessage) messages.push(fileMessage);
          console.log(`Attached ${file.absolutePath}`);
        } catch (error) {
          console.log(`Could not read file: ${error.message}`);
        }
        continue;
      }

      messages.push({ role: "user", content: userInput });
      process.stdout.write("\nQwen> ");
      const answer = await chat(options, messages);
      messages.push({ role: "assistant", content: answer });
    }
  } finally {
    rl.close();
  }
}

main().catch((error) => {
  console.error(`\nError: ${error.message}`);
  process.exit(1);
});
