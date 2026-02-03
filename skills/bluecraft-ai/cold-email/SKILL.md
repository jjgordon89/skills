---
name: cold-email
description: Generate hyper-personalized cold email sequences using AI. Turn lead data into high-converting outreach campaigns.
metadata:
  clawdbot:
    requires:
      env:
        - MACHFIVE_API_KEY
---

# MachFive - AI Cold Email Generator

Generate personalized cold email sequences from lead data. MachFive uses AI to research prospects and craft unique, relevant outreach - not templates.

## Setup

1. Get your API key at https://app.machfive.io/settings (Integrations → API Keys)
2. Set `MACHFIVE_API_KEY` in your environment

## Endpoints

### Single Lead (Sync)

Generate a sequence for one lead. Waits for completion, returns emails directly.
```
POST https://app.machfive.io/api/v1/campaigns/{campaign_id}/generate
Authorization: Bearer {MACHFIVE_API_KEY}
Content-Type: application/json
```

Or use `X-API-Key: {MACHFIVE_API_KEY}` header.
```json
{
  "lead": {
    "name": "John Smith",
    "title": "VP of Marketing",
    "company": "Acme Corp",
    "email": "john@acme.com",
    "company_website": "https://acme.com",
    "linkedin_url": "https://linkedin.com/in/johnsmith"
  },
  "options": {
    "email_count": 3,
    "email_signature": "Best,\nYour Name",
    "approved_ctas": ["Direct Meeting CTA", "Lead Magnet CTA"]
  }
}
```

**Response (200):**
```json
{
  "lead_id": "lead_xyz789",
  "sequence_id": "uuid",
  "sequence": [
    { "step": 1, "subject": "...", "body": "..." },
    { "step": 2, "subject": "...", "body": "..." },
    { "step": 3, "subject": "...", "body": "..." }
  ],
  "credits_remaining": 94
}
```

### Batch (Async)

Generate sequences for multiple leads. Returns immediately, processes in background.
```
POST https://app.machfive.io/api/v1/campaigns/{campaign_id}/generate-batch
Authorization: Bearer {MACHFIVE_API_KEY}
Content-Type: application/json
```

Or use `X-API-Key: {MACHFIVE_API_KEY}` header.
```json
{
  "leads": [
    { "name": "John Smith", "email": "john@acme.com", "company": "Acme Corp", "title": "VP Marketing" },
    { "name": "Jane Doe", "email": "jane@beta.com", "company": "Beta Inc", "title": "Director Sales" }
  ],
  "options": {
    "sequence_name": "Q1 Outreach Batch",
    "email_count": 3
  }
}
```

**Response (202):**
```json
{
  "sequence_id": "uuid",
  "status": "processing",
  "leads_count": 2,
  "message": "Batch accepted. Poll sequence status or view in MachFive UI."
}
```

## Lead Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Full name or first name |
| `email` | No | Lead's email address |
| `company` | Yes | Company name |
| `title` | No | Job title |
| `company_website` | No | Company URL for research |
| `linkedin_url` | No | LinkedIn profile for deeper personalization |

## Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sequence_name` | string | Auto | Display name in MachFive UI |
| `email_count` | number | 3 | Emails per sequence (1-5) |
| `email_signature` | string | None | Signature appended to emails |
| `campaign_angle` | string | None | Context for personalization |
| `approved_ctas` | array | From campaign | CTAs to use (omit to use campaign defaults) |

## Errors

| Code | Error | Description |
|------|-------|-------------|
| 401 | UNAUTHORIZED | Invalid or missing API key |
| 402 | INSUFFICIENT_CREDITS | Out of credits |
| 403 | FORBIDDEN | Campaign not in your workspace |
| 404 | NOT_FOUND | Campaign doesn't exist |

## Usage Examples

"Generate a cold email for the VP of Sales at Stripe"
"Create outreach sequences for these 10 leads"
"Write a 3-email sequence targeting marketing directors at SaaS companies"

## Pricing

- Free: 100 credits/month
- Starter: 2,000 credits/month
- Growth: 5,000 credits/month
- 1 credit = 1 lead processed

Get started: https://machfive.io
