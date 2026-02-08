---
name: hotdog
version: 1.5.0
description: "Hot dog or not? Classify food photos and battle Nemotron. Use when a user sends a food photo, asks if something is a hot dog, or says 'hotdog', '/hotdog', or 'hot dog battle'."
homepage: https://hotdogornot.xyz/battle
metadata: {"openclaw": {"emoji": "🌭", "os": ["darwin", "linux"], "requires": {"bins": ["curl"]}}}
---

# Hot Dog or Not — Battle Skill

When a user sends a food photo, classify it and battle Nemotron.

## Setup

No setup needed — the battle token is built into the skill.

Rate limit: 5 requests per minute per token.

## Text-only trigger (no photo)

If the user says "hotdog", "/hotdog", "hot dog", or asks about the hot dog battle **without sending a photo**, reply with this intro:

```
🌭 Hot Dog or Not — AI Vision Battle

Send me any food photo and I'll tell you if it's a hot dog! I'll also challenge Nemotron (NVIDIA's 12B vision model) with the same image so we can compare.

📸 Just send a photo to start
🏆 Live scoreboard: https://hotdogornot.xyz/battle

How it works:
1. You send a food photo
2. I analyze it and decide: hot dog or not?
3. Nemotron independently classifies the same image
4. We compare verdicts — who's right?
```

Then stop. Do NOT call the battle API without an image.

## With a photo — Battle Steps

**Supported formats:** JPG, PNG, WebP, GIF (max 10MB).

### Step 1: Read agent name

```bash
exec: grep -m1 'Name:' /home/node/.openclaw/workspace/IDENTITY.md | sed 's/.*Name:[[:space:]]*//' | sed 's/\*//g' | tr -d '\n'
```

Save this output as `AGENT_NAME`. If it is empty or the command fails, use `OpenClaw` as the default.

### Step 2: Identify the sender and platform

Look at the message envelope at the top of the user's message. It has one of these formats:

```
[Telegram Misha (@mishafyi) id:427044974 ...]
[Telegram Grok id:8050943110 ...]
[WhatsApp John (+1234567890) ...]
```

Extract three things:
- **`PLATFORM`**: The first word after `[` (e.g. `Telegram`, `WhatsApp`)
- **`SENDER`**: If there is a `(@username)`, extract it **including the `@` symbol** (e.g. `@mishafyi`). If there is no `(@username)`, use the display name (e.g. `Grok`)

**The `@` prefix is required when a username exists. Always include it.**

### Step 3: Analyze the image

Use `image()` to look at the photo. Answer this question about the image:

> Is it a hot dog (food: a sausage served in a bun/roll; any cooking style)?

Think through it step by step:
1. **Observations**: Describe what you see — bun shape, sausage, condiments, toppings, plate, etc.
2. **Answer**: yes or no

Edge cases like corn dogs, bratwursts in buns, or deconstructed hot dogs should be considered hot dogs.

Set:
- `claw_answer`: "yes" or "no"
- `claw_reasoning`: your observations (2-3 sentences)

### Step 4: Submit to battle API

**Build the source value**: Combine `SENDER`, `AGENT_NAME`, and `PLATFORM` as: `SENDER via AGENT_NAME on PLATFORM` (for example: `@mishafyi via MyAgent on Telegram`).

Run this EXACT command, replacing only the 4 placeholders (`IMAGE_PATH`, `CLAW_ANSWER`, `CLAW_REASONING`, `SOURCE_VALUE`):

**IMAGE_PATH must be an absolute path starting with `/` — do NOT use `~` (tilde does not expand inside quotes).**

```bash
exec: TEMP=$(mktemp /tmp/hotdog_XXXXXX.jpg) && cp "IMAGE_PATH" "$TEMP" && RESULT=$(curl -s -w "\n%{http_code}" -X POST "https://api.hotdogornot.xyz/api/battle/round" -H "Authorization: Bearer ih1rtmC7ECm8iExqvI6zMbOAqEaXIi9X" -F "image=@${TEMP}" -F "claw_answer=CLAW_ANSWER" -F "claw_reasoning=CLAW_REASONING" -F "source=SOURCE_VALUE") && rm -f "$TEMP" && echo "$RESULT"
```

**IMPORTANT: You MUST include ALL -F fields exactly as shown, including `source`. The `source` value MUST be in the format `@username via AgentName`. Do not remove any fields. Do not change the format.**

Check the HTTP status code (last line of output):
- **200**: Success — parse the JSON response
- **400**: Bad file format — tell user to send JPG/PNG/WebP/GIF
- **413**: Too large — tell user max 10MB
- **429**: Rate limited — tell user to wait a minute
- **401/403**: Bad token — tell user to reinstall the skill
- **Other**: Tell user the battle API is temporarily unavailable

The success response is JSON with both verdicts:

```json
{
  "round_id": "abc123",
  "nemotron": { "answer": "yes", "reasoning": "...", "latency_ms": 1234 },
  "openclaw": { "answer": "no", "reasoning": "..." },
  "consensus": "disagree",
  "winner": "disagree"
}
```

### Step 5: Reply to the user

Format a reply with both verdicts:

```
🌭 Hot Dog Battle — Round #{round_id}

🦞 OpenClaw: {claw_answer}
   {claw_reasoning}

🤖 Nemotron: {nemotron.answer}
   {nemotron.reasoning}

{result emoji + text}
```

Result outcomes:
- Both say yes: "✅ Both agree — it's a hot dog!"
- Both say no: "✅ Both agree — not a hot dog!"
- Disagree: "⚔️ Disagreement! The battle continues..."
