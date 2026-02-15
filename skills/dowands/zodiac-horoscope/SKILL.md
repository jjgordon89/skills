---
name: zodiac-horoscope
description: >
  Fetch personalized daily horoscope forecasts from zodiac-today.com API based on natal chart calculations.
  Use when a user wants: (1) daily guidance on what activities to pursue or avoid,
  (2) life planning help — best days for interviews, travel, romance, important decisions,
  (3) energy/focus/luck/romance forecasts to optimize their schedule,
  (4) lucky colors and numbers for the day,
  (5) future date analysis for planning events, trips, or milestones (paid tiers).
  Triggers: horoscope, zodiac, star sign forecast, daily guidance, lucky day, best day to, astrology advice,
  what should I do today, is today a good day for, plan my week astrology.
env:
  ZODIAC_API_KEY:
    description: "API key from zodiac-today.com (starts with hsk_)"
    required: true
  ZODIAC_PROFILE_ID:
    description: "Profile ID for the user's birth chart"
    required: true
---

# Zodiac Horoscope

Provide personalized, actionable daily guidance powered by planetary transit calculations against the user's natal chart.

## Privacy Notice

This skill collects **sensitive PII** (email, birth date, birth city) required for natal chart calculations. Handle with care:
- Never log or expose these values in public channels
- Store API keys and profile IDs in environment variables, not in plain text files
- Ask for explicit user consent before collecting birth information

## How This Helps People

- **Daily decision-making**: "Should I have that difficult conversation today?" → Check if confrontations are favorable or unfavorable
- **Schedule optimization**: Plan high-energy tasks on high-energy days, rest on low days
- **Life event planning**: Find the best window for job interviews, first dates, travel, or big purchases (paid tiers unlock future dates)
- **Relationship insights**: Romance metrics help users pick ideal date nights
- **Motivation & mindfulness**: Daily summaries provide a moment of reflection and intentional living

## Setup

Everything can be done via API — no browser needed.

### 1. Register & get API key

```bash
# Send verification code (creates account if new)
curl -s -X POST https://zodiac-today.com/api/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Verify code (check email inbox for 6-digit code)
curl -s -X POST https://zodiac-today.com/api/auth/verify \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"user@example.com","code":"123456"}'

# Create API key (use session cookie from verify step)
curl -s -X POST https://zodiac-today.com/api/keys \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"name":"My Agent"}'
# Response: {"id":"...","key":"hsk_...","name":"My Agent"}
```

Store the `hsk_` key as environment variable `ZODIAC_API_KEY`.

### 2. Create birth profile

```bash
curl -s -X POST https://zodiac-today.com/api/profiles \
  -H "Authorization: Bearer hsk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"name":"John","birthDate":"1990-05-15","birthCity":"London, UK"}'
```

Save the returned `id` as environment variable `ZODIAC_PROFILE_ID`.

## Workflow

### First-time setup for a user
1. Ask for their email, birth date, and birth city
2. Register via `/api/auth/send-code` → retrieve code from email → `/api/auth/verify`
3. Create API key via `POST /api/keys` (with session cookie)
4. Create profile via `POST /api/profiles` (with API key)
5. Save as env vars: `ZODIAC_API_KEY` and `ZODIAC_PROFILE_ID`

### Daily horoscope fetch
1. Call `GET /api/horoscope/daily?profileId=$ZODIAC_PROFILE_ID&startDate=YYYY-MM-DD&endDate=YYYY-MM-DD` with `Authorization: Bearer $ZODIAC_API_KEY`
2. Parse the response and present actionable insights

### Presenting results to users

Translate raw data into **practical advice**:

- **overallRating** (1-10): Frame as "Great day!" (8+), "Solid day" (6-8), "Take it easy" (<6)
- **favorable/unfavorable**: Present as "Good for:" and "Better to avoid:" lists
- **metrics**: Highlight the standout ones — "Your energy is HIGH today, perfect for tackling that project"
- **luckyColors**: Suggest outfit or decor choices
- **luckyNumbers**: Mention casually, fun touch
- **summary**: Use the astrological narrative to add color, but keep advice grounded and practical

### Planning ahead (paid tiers)

For users with Starter+ tiers, fetch date ranges to help:
- "What's the best day this month for my job interview?"
- "When should I plan our anniversary dinner?"
- Compare overallRating across dates and recommend the highest-rated windows

## API Details

See [references/api.md](references/api.md) for full endpoint docs, parameters, tiers, and response schemas.

## Example curl

```bash
curl "https://zodiac-today.com/api/horoscope/daily?profileId=PROFILE_ID&startDate=2026-02-15&endDate=2026-02-15" \
  -H "Authorization: Bearer hsk_your_api_key"
```
