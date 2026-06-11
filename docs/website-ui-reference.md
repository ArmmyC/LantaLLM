# Lanta LLM Hosting Website UI Reference

This document describes the current chat frontend implemented in `website/public`. The interface is a private web gateway for the Lanta-hosted Qwen/vLLM model, designed as a compact operational chat console rather than a marketing page.

## Overall Layout

The app uses a two-panel shell:

- A fixed-width left sidebar for identity, connection state, model settings, file attachment, and session actions.
- A main chat workspace on the right for the active model session, conversation history, and message composer.

On desktop, the sidebar is `328px` wide and the chat panel takes the remaining screen width. The entire app is full height with no landing page or decorative hero section. The first screen is the usable model interface.

On tablet and mobile widths, the layout collapses into a single column. The chat workspace is ordered first so users can immediately read and send messages, while the configuration sidebar follows below.

## Visual Style

The UI has a calm, utilitarian product feel. It uses a light neutral background with restrained green accents:

- Page background: pale gray-green.
- Panels and inputs: white or near-white.
- Primary accent: deep green.
- Text: near-black for primary copy, muted gray-green for secondary labels.
- Borders: soft gray-green lines.
- Error/offline state: muted red.
- Warning/checking state: muted amber.

The design avoids large marketing visuals and keeps the interface focused on repeated use. Corners are mostly `8px`, matching a practical SaaS/control-panel style. Buttons, cards, inputs, and message bubbles use consistent border radii and spacing.

## Left Sidebar

The sidebar is the control surface for the model session.

### Brand Block

At the top is a compact brand identity:

- A dark square `SC` mark.
- The product name `LLM Test`.
- The subtitle `Private Lanta model gateway`.

This makes the app identity visible without taking excessive space.

### Connection Card

Below the brand is a connection status card. It contains:

- A colored status dot.
- A status label such as `Checking gateway`, `Gateway online`, `Gateway offline`, or `Gateway error`.
- A refresh icon button that manually checks the model gateway.

The status dot changes class depending on state:

- Amber/default while checking.
- Green when online.
- Red when offline or errored.

The manual check sends a small request to the backend asking the model to reply exactly `online`.

### Model Controls

The model control area contains the main settings sent to the backend API:

- `Site password`: password field used as the `x-site-password` request header.
- `Served model`: text input, defaulting to `qwen36-27b`.
- `System prompt`: textarea, defaulting to `You are a helpful assistant.`
- `Max tokens`: numeric input with a maximum of `32768`, defaulting to `1024`.
- `Temperature`: numeric input from `0` to `2`, defaulting to `0.7`.
- `Thinking mode`: custom toggle that enables Qwen's reasoning chat-template mode.

The current model name is also mirrored in the chat panel header as the active session title.

User preferences are persisted in `localStorage`:

- Site password.
- Model name.
- System prompt.
- Max tokens.
- Temperature.
- Thinking toggle state.

This means the interface remembers common settings between page refreshes.

### Thinking Mode Toggle

The thinking mode control is a custom switch styled like a small horizontal toggle. It has:

- A 40px track.
- A circular thumb.
- Deep green active state.
- Label: `Thinking mode`.
- Helper text: `Qwen reasoning template`.

When enabled, the frontend sends `thinking: true` to `/api/chat`. The backend then passes this through as `chat_template_kwargs.enable_thinking`.

### File Context Panel

The file panel provides a single file attachment control:

- The visible control is a dashed drop-style button labeled `Attach file context`.
- The actual file input is hidden.
- Once a file is selected, the UI reads it as text and stores it as temporary file context.

The file status line shows:

- `No file attached` by default.
- `Attached <filename> (<size> KB)` after a valid file is added.
- `File too large. Limit: 220 KB` if the file exceeds the limit.

Attached file content is sent as `file_context` in the API request. The current size limit is `220000` bytes.

### Sidebar Actions

At the bottom of the sidebar are two secondary buttons:

- `Clear chat`: resets the in-memory chat history and shows a system message.
- `Export`: downloads the current conversation as a plain text file.

The exported filename format is:

```text
siliconcraft-chat-YYYY-MM-DDTHH-MM-SS.txt
```

## Main Chat Panel

The chat panel contains the active model session.

### Top Bar

The top bar contains:

- Eyeline label: `Active session`.
- Session title: current model name, defaulting to `qwen36-27b`.
- Message count pill.
- Thinking state pill.

The pills show compact live state:

- `0 messages`, `1 message`, or `<n> messages`.
- `Thinking on` or `Thinking off`.

The top bar uses a translucent white background and subtle blur so it feels like a persistent workspace header.

### Message Area

The message area is a scrollable conversation region. On first load, it renders a system message:

```text
Ready. Ask me something, attach a file, or enable thinking mode.
```

Each message is rendered with:

- A role label: `system`, `user`, or `assistant`.
- A bordered content block.
- A `Copy` button.

Desktop message rows use a three-column grid:

- Role column.
- Content column.
- Copy button column.

On smaller screens, the message row collapses into a single column and the copy button remains visible.

Message content supports basic fenced code formatting. Text wrapped in triple backticks is rendered as a dark code block. HTML is escaped before rendering to prevent injected markup from being interpreted.

Message styles vary slightly by role:

- System messages use a muted green-gray content block.
- User messages use a pale cool-gray block.
- Assistant messages use a very light green-white block.

### Composer

The composer is pinned at the bottom of the chat panel. It contains:

- A textarea with placeholder `Ask Qwen something...`.
- A character counter.
- A keyboard hint: `Ctrl+Enter to send`.
- A primary green `Send` button with a paper-plane icon.

The send button changes its label to `Sending` while the request is in flight and is disabled during that time.

On mobile, the composer stacks into one column. The keyboard shortcut hint is hidden at narrow widths to prevent crowding.

## Chat Behavior

When the user submits a prompt:

1. Empty prompts are ignored.
2. The user's message is immediately rendered in the conversation.
3. The frontend builds the outbound message list:
   - Optional system prompt first.
   - The last 24 stored conversation messages.
   - The new user message.
4. The request is sent to `/api/chat`.
5. The site password is sent in the `x-site-password` header.
6. Model settings, thinking mode, and file context are sent in the JSON body.
7. The assistant response is rendered.
8. The user and assistant messages are appended to in-memory history.
9. The connection state is updated.

Only successful user/assistant pairs are stored in the chat history. Error messages are rendered visibly but are not added to the stored history.

The outbound request body includes:

```json
{
  "model": "qwen36-27b",
  "messages": [],
  "max_tokens": 1024,
  "temperature": 0.7,
  "thinking": false,
  "file_context": ""
}
```

## Error States

If the backend responds with an error or the upstream model API cannot be reached, the UI renders an assistant-style error message such as:

```text
Error: Could not reach upstream model API: "fetch failed"
```

The connection card then changes to:

```text
Gateway error
```

If the manual connection check fails, it shows:

```text
Gateway offline
```

A common cause is that the local SSH tunnel to Lanta is not running, meaning `http://127.0.0.1:8000/v1` cannot be reached by the local web server.

## Responsive Behavior

The UI has two main breakpoints.

At widths below `920px`:

- The app becomes a single-column layout.
- The chat panel appears before the sidebar.
- Message rows collapse from three columns into one column.
- Copy buttons are always visible.

At widths below `640px`:

- Sidebar, top bar, message area, and composer use `16px` side padding.
- Field rows stack vertically.
- Sidebar action buttons stack vertically.
- The composer stacks vertically.
- The shortcut hint is hidden.
- Core controls are constrained to the viewport width to avoid horizontal overflow.

## Accessibility Notes

The current UI includes several accessibility-friendly structures:

- Semantic `main`, `aside`, `section`, `header`, `form`, and `article` elements.
- `aria-label` attributes for major regions.
- `aria-live="polite"` on the message area.
- Button titles and labels for the connection refresh control.
- Native input, textarea, button, and file input semantics.

The custom thinking toggle remains a native checkbox input, so it is still keyboard and screen-reader accessible.

## Current Implementation Files

The UI is implemented across these files:

- `website/public/index.html`: page structure and controls.
- `website/public/styles.css`: layout, color system, responsive behavior, and component styling.
- `website/public/app.js`: state management, chat submission, connection checks, file context, local storage, rendering, copy, clear, and export behavior.
- `website/api/chat.js`: backend API proxy that talks to the OpenAI-compatible vLLM endpoint.
- `website/server.mjs`: local static server and API bridge for development.

## Current User Experience Summary

The current LLM Test UI feels like a private model operations console. It puts the chat workflow front and center while keeping model controls close at hand. It is intended for practical daily use: choose a served model, adjust generation settings, optionally enable thinking mode, attach a small file as context, and chat through a protected backend API without exposing the upstream vLLM endpoint directly in frontend code.
