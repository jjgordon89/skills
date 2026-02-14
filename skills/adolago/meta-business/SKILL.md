---
name: meta-business
description: Meta Business CLI for WhatsApp, Instagram, Facebook Pages, and Messenger automation.
metadata:
  {
    "openclaw":
      {
        "emoji": "📱",
        "requires": { "bins": ["meta"] },
        "install":
          [
            {
              "id": "bun",
              "kind": "command",
              "command": "bun install -g meta-business-cli",
              "bins": ["meta"],
              "label": "Install meta CLI (bun)",
            },
          ],
      },
  }
---

# Meta Business CLI

Use `meta` for WhatsApp, Instagram, Facebook Pages, and Messenger automation via the Graph API.

Setup (once)

- `meta config set app.id YOUR_APP_ID`
- `meta config set app.secret YOUR_APP_SECRET`
- `meta auth login` (OAuth PKCE flow, opens browser)
- `meta doctor` (verify connectivity and permissions)
- Or use `--token YOUR_TOKEN` with any command to skip OAuth

Surface config

- WhatsApp: `meta config set whatsapp.phoneNumberId ID` and `meta config set whatsapp.businessAccountId ID`
- Instagram: `meta config set instagram.accountId ID`
- Pages/Messenger: `meta config set pages.pageId ID`
- Show all: `meta config list`

WhatsApp commands

- Send text: `meta wa send "+1234567890" --text "Hello" --json`
- Send image: `meta wa send "+1234567890" --image "https://example.com/photo.jpg" --caption "Look" --json`
- Send template: `meta wa send "+1234567890" --template "hello_world" --template-lang en_US --json`
- Send document: `meta wa send "+1234567890" --document "https://example.com/file.pdf" --json`
- List templates: `meta wa template list --json`
- Get template: `meta wa template get TEMPLATE_NAME --json`
- Delete template: `meta wa template delete TEMPLATE_NAME --json`
- Upload media: `meta wa media upload ./photo.jpg --json`
- Get media URL: `meta wa media url MEDIA_ID --json`
- Download media: `meta wa media download MEDIA_ID ./output.jpg`
- View analytics: `meta wa analytics --days 30 --granularity DAY --json`

Instagram commands

- Publish image: `meta ig publish --image "https://example.com/photo.jpg" --caption "My post" --json`
- Publish video: `meta ig publish --video "https://example.com/video.mp4" --caption "Watch this" --json`
- Publish Reel: `meta ig publish --video "https://example.com/reel.mp4" --reel --caption "New reel" --json`
- View account insights: `meta ig insights --period day --days 30 --json`
- View media insights: `meta ig insights --media-id MEDIA_ID --json`
- List comments: `meta ig comments list MEDIA_ID --json`
- Reply to comment: `meta ig comments reply COMMENT_ID "Thanks!" --json`
- Hide comment: `meta ig comments hide COMMENT_ID --json`
- Delete comment: `meta ig comments delete COMMENT_ID --json`

Facebook Pages commands

- Create post: `meta fb post --message "Hello from the CLI" --json`
- Create link post: `meta fb post --message "Check this out" --link "https://example.com" --json`
- List posts: `meta fb list --limit 10 --json`
- View insights: `meta fb insights --period day --days 30 --json`

Messenger commands

- Send text: `meta messenger send PSID --text "Hello" --json`
- Send image: `meta messenger send PSID --image "https://example.com/photo.jpg" --json`
- Send with tag: `meta messenger send PSID --text "Update" --type MESSAGE_TAG --tag HUMAN_AGENT --json`
- List conversations: `meta messenger receive --json`
- View conversation: `meta messenger receive --conversation-id CONV_ID --json`

Webhook commands

- Start listener: `meta webhook listen --port 3000 --verify-token TOKEN --app-secret SECRET`
- Test verification: `meta webhook verify --verify-token TOKEN --json`
- Subscribe to events: `meta webhook subscribe --object whatsapp_business_account --fields messages --callback-url "https://example.com/webhook" --json`

Diagnostics

- `meta doctor --json` checks config, credentials, token validity, Graph API connectivity, permissions, and surface-specific asset access.

Notes

- Always use `--json` for structured output when automating.
- All commands work non-interactively when required args are passed as flags.
- Use `--token TOKEN` to override stored credentials for any command.
- Use `--api-version v22.0` to pin a specific Graph API version.
- WhatsApp requires phone number ID and business account ID to be configured.
- Instagram publish requires a public URL for images/videos (not local files).
- Messenger messaging outside the 24h window requires a message tag.
- Run `meta doctor` before first use to verify setup.
