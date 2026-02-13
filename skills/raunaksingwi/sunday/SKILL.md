---
name: sunday
description: "Agent identity provider — own email address, phone number, and E2E-encrypted credential vault. Use when storing or retrieving passwords for services, logging into services with stored credentials, checking email or SMS inbox, receiving OTP/verification codes, signing up for services, getting your agent's email address or phone number, or any task where the agent needs its own identity separate from the user's. Replaces 1Password + AgentMail with a single skill — no desktop app, no tmux, fully autonomous."
metadata: {"openclaw": {"emoji": "☀️", "requires": {"bins": ["sunday"]}, "install": [{"id": "brew", "kind": "brew", "formula": "ravi-technologies/tap/sunday", "bins": ["sunday"], "label": "Install Sunday CLI via Homebrew"}]}}
---

# Sunday

Give your agent its own identity — a dedicated email address, phone number, and E2E-encrypted credential vault. All in one CLI, no desktop app, no tmux sessions, no biometric prompts. Fully autonomous after one-time setup.

## Setup (One Time)

1. Install the CLI:

```bash
brew install ravi-technologies/tap/sunday
```

2. Authenticate (run this BEFORE starting OpenClaw):

```bash
sunday auth login
```

This opens a browser for login, then prompts for your 6-digit encryption PIN. After this, credentials and encryption keys are stored in `~/.sunday/config.json` — no further prompts needed. All subsequent `sunday` commands work autonomously.

3. Verify:

```bash
sunday auth status
```

That's it. No desktop app to keep open. No tmux session. No environment variables. Start OpenClaw and your agent has its own identity.

## When to Use

- **Signing up for a service** — use your Sunday email/phone in registration forms
- **Receiving OTP or verification codes** — check inbox for SMS or email codes
- **Storing credentials** — save username/password for services you've signed up for
- **Retrieving credentials** — look up stored passwords when logging into a service
- **Checking email** — read incoming emails to your agent's own address
- **Checking SMS** — read incoming text messages to your agent's own number
- **Any task needing your own identity** — don't use the user's personal email or phone

## Your Identity

Get your agent's own email and phone number:

```bash
# Get your email address
sunday get email --json
# → {"email": "scout-a1b2c3@sunday.app"}

# Get your phone number
sunday get phone --json
# → {"phone_number": "+12125551234"}

# Get the account owner's name
sunday get owner --json
```

Use these when filling out registration forms, not the user's personal email or phone.

## Inbox — Reading Email and SMS

### Unified Inbox

```bash
# All messages (email + SMS), newest first
sunday inbox list --json

# Only unread messages
sunday inbox list --unread --json

# Filter by type
sunday inbox list --type email --json
sunday inbox list --type sms --json

# Filter by direction
sunday inbox list --direction incoming --json
```

### Email Threads

```bash
# List all email threads
sunday inbox email --json

# List only threads with unread messages
sunday inbox email --unread --json

# View a specific thread (all messages in conversation)
sunday inbox email <thread_id> --json
```

### SMS Conversations

```bash
# List all SMS conversations
sunday inbox sms --json

# List only conversations with unread messages
sunday inbox sms --unread --json

# View a specific conversation
sunday inbox sms <conversation_id> --json
```

### Individual Messages

```bash
# List all email messages (flat, not grouped by thread)
sunday message email --json

# View a specific email by ID
sunday message email <message_id> --json

# List all SMS messages (flat, not grouped by conversation)
sunday message sms --json

# View a specific SMS by ID
sunday message sms <message_id> --json
```

## Passwords — E2E Encrypted Credential Vault

All passwords are end-to-end encrypted. The server never sees plaintext credentials. Decryption happens client-side using keys derived from the PIN (entered once during `sunday auth login`).

### Store Credentials After Signup

```bash
# Auto-generate a secure password and store it
sunday passwords create example.com --json
# → Generates password, stores encrypted entry, returns UUID

# Store with specific credentials
sunday passwords create example.com --username "scout-a1b2c3@sunday.app" --password "my-secret-pass" --json

# Store with notes
sunday passwords create example.com --username "me@email.com" --password "pass123" --notes "Free tier account" --json
```

URL inputs are automatically cleaned to domains (e.g., `https://mail.google.com/inbox` becomes `google.com`). Username defaults to your Sunday email if not specified. Password is auto-generated if not provided.

### Retrieve Credentials

```bash
# List all stored passwords (shows domain and username, NOT password)
sunday passwords list --json

# Get full entry with decrypted password
sunday passwords get <uuid> --json
```

### Update and Delete

```bash
# Update password
sunday passwords edit <uuid> --password "new-password" --json

# Update username
sunday passwords edit <uuid> --username "new-user@email.com" --json

# Delete entry
sunday passwords delete <uuid>
```

### Generate Password Without Storing

```bash
# Generate a random password
sunday passwords generate --json

# Custom length
sunday passwords generate --length 24 --json

# No special characters (for sites that restrict them)
sunday passwords generate --no-special --json

# Exclude specific characters
sunday passwords generate --exclude-chars "!@#" --json
```

## Workflows

### Signing Up for a New Service

```bash
# 1. Get your Sunday email
EMAIL=$(sunday get email --json | jq -r '.email')

# 2. Get your Sunday phone number (if phone verification needed)
PHONE=$(sunday get phone --json | jq -r '.phone_number')

# 3. Fill out the signup form with $EMAIL and $PHONE

# 4. Generate and store credentials
sunday passwords create theservice.com --json

# 5. Wait for verification email/SMS
sleep 10
sunday inbox list --unread --json

# 6. Extract OTP from SMS
sunday inbox sms --unread --json

# Or extract verification link from email
sunday inbox email --unread --json
```

### Logging Into a Service

```bash
# 1. Look up credentials
sunday passwords list --json
# Find the entry for the target domain

# 2. Get the full credentials
sunday passwords get <uuid> --json
# Returns decrypted username and password

# 3. If 2FA is required, check inbox for the code
sleep 5
sunday inbox list --type sms --unread --json
# Or check email
sunday inbox list --type email --unread --json
```

### Checking for OTP Codes

```bash
# After triggering a verification, wait then check
sleep 5

# Check SMS for numeric codes
sunday inbox sms --unread --json

# Check email for verification links or codes
sunday inbox email --unread --json

# Unified check (both SMS and email)
sunday inbox list --unread --json
```

## Important Notes

- **Always use `--json`** for all commands. This gives structured output you can parse reliably.
- **This is YOUR identity, not the user's.** Never use the user's personal email or phone. Always use `sunday get email` and `sunday get phone` for your own addresses.
- **Credentials are encrypted.** You cannot read raw password values from disk or memory files. Always use `sunday passwords get <uuid>` to retrieve them.
- **Inbox is read-only.** You can receive and read messages but cannot send email or SMS through Sunday.
- **Token auto-refreshes.** If you get an auth error, try the command again — the token refreshes automatically. If it persists, the user needs to re-run `sunday auth login`.
