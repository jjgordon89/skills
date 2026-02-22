---
name: publora-mastodon
description: >
  Post or schedule content to Mastodon using the Publora API. Use this skill
  when the user wants to publish or schedule Mastodon toots via Publora.
---

# Publora — Mastodon

Post and schedule Mastodon content via the Publora API.

> **Prerequisite:** Install the `publora` core skill for auth setup and getting platform IDs.

## Get Your Mastodon Platform ID

```bash
GET https://api.publora.com/api/v1/platform-connections
# Look for entries like "mastodon-instance_social"
```

## Post to Mastodon Immediately

```javascript
await fetch('https://api.publora.com/api/v1/create-post', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'x-publora-key': 'sk_YOUR_KEY' },
  body: JSON.stringify({
    content: 'Just launched something new on the open web 🎉 #fediverse #opensource',
    platforms: ['mastodon-instance_social']
  })
});
```

## Schedule a Mastodon Post

```javascript
await fetch('https://api.publora.com/api/v1/create-post', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'x-publora-key': 'sk_YOUR_KEY' },
  body: JSON.stringify({
    content: 'Weekly update: here\'s what the team shipped #buildinpublic #indiedev',
    platforms: ['mastodon-instance_social'],
    scheduledTime: '2026-03-16T10:00:00.000Z'
  })
});
```

## Tips for Mastodon

- **500 character limit** (varies by instance, but 500 is standard)
- **Decentralized** — your account lives on one instance, but federated across the network
- **Hashtags matter** here — Mastodon uses hashtags for discoverability since there's no algorithm
- **Content warnings (CW)** are cultural norm for sensitive topics
- **Tech-forward community** — developers, privacy advocates, open source enthusiasts
- **Best hashtags:** `#fediverse`, `#opensource`, `#indiedev`, `#buildinpublic`
- **No link suppression** — sharing URLs works great
