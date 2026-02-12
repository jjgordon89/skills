---
name: expert-finder
description: "Find domain experts, thought leaders, and subject-matter authorities on any topic. Searches Twitter and Reddit for people who demonstrate deep knowledge, frequent discussion, and above-average expertise in a specific field. Expert discovery, talent sourcing, researcher identification, and KOL (Key Opinion Leader) mapping."
homepage: https://xpoz.ai
metadata:
  {
    "openclaw":
      {
        "requires":
          {
            "bins": ["mcporter"],
            "skills": ["xpoz-setup"],
            "tools": ["web_search", "web_fetch"],
            "network": ["mcp.xpoz.ai"],
            "credentials": "Xpoz account (free tier) — auth via xpoz-setup skill (OAuth 2.1)",
          },
      },
  }
tags:
  - expert-finder
  - domain-expert
  - thought-leader
  - talent-sourcing
  - researcher
  - KOL
  - twitter
  - reddit
  - social-media
  - knowledge
  - authority
  - subject-matter-expert
  - people-search
  - intelligence
  - mcp
  - xpoz
---

# Expert Finder

Find domain experts, thought leaders, and subject-matter authorities on any topic by analyzing social media activity across Twitter and Reddit.

**What it does:** Given a domain, topic, or set of keywords, this skill expands them into comprehensive search terms, searches social media for people who frequently discuss the subject with above-average knowledge, classifies them by type (deep expert vs thought leader vs practitioner), ranks them, and produces a detailed report.

---

## Phase 1: Domain Research & Query Expansion

### Step 1: Understand the Domain

The user provides one of:
- A **topic/domain** (e.g., "quantum computing", "kubernetes security", "regenerative agriculture")
- **Keywords** (e.g., "LLM fine-tuning, RLHF, preference optimization")
- A **URL** to a paper, project, or product that defines the domain

If a URL is provided, research it:
```
web_fetch url="<provided URL>"
```

If only keywords/topic, expand understanding:
```
web_search query="<topic> overview key concepts terminology"
web_search query="<topic> leading researchers practitioners"
```

### Step 2: Build Domain Profile

Create a domain profile with:

```json
{
  "domain": "Short domain name",
  "description": "One-paragraph description of the field",
  "core_terms": ["term1", "term2", "term3"],
  "technical_terms": ["jargon1", "jargon2"],
  "adjacent_fields": ["related1", "related2"],
  "key_conferences": ["conf1", "conf2"],
  "known_authorities": ["person1", "person2"],
  "subreddits": ["r/relevant1", "r/relevant2"]
}
```

### Step 3: Generate Search Queries

Expand the domain into tiered search queries:

| Tier | Purpose | Example (for "RLHF") |
|------|---------|----------------------|
| **Tier 1: Core** | Exact domain terms | `"RLHF"`, `"reinforcement learning from human feedback"` |
| **Tier 2: Technical** | Deep jargon only experts use | `"reward model overfitting"`, `"KL divergence penalty"`, `"PPO vs DPO"` |
| **Tier 3: Adjacent** | Related expertise signals | `"preference optimization"`, `"constitutional AI"`, `"alignment research"` |
| **Tier 4: Discussion** | Opinion/debate markers | `"RLHF vs" OR "the problem with RLHF"`, `"hot take" AND "alignment"` |

**Generate 10-20 queries** covering all tiers. Tier 2 (technical jargon) is the most valuable — people using niche terminology are more likely genuine experts.

### Step 4: Run Autonomously

Do NOT stop to ask the user for validation. Proceed directly to Phase 2 with the generated queries. Send brief progress updates only (one line per phase, e.g., "🔍 Searching Twitter for 16 queries..." or "📊 Analyzing 24 candidates...").

---

## Phase 2: Social Media Search

### Step 5: Search Twitter

Run each query group through Xpoz:

```bash
mcporter call xpoz.getTwitterPostsByKeywords \
  query='"RLHF" OR "reinforcement learning from human feedback"' \
  startDate="<6 months ago>" \
  fields='["id","text","authorUsername","likeCount","retweetCount","replyCount","impressionCount","createdAtDate"]'
```

**CRITICAL: Always use the full CSV dataset, never just the first 100 paginated results.**

Every Xpoz search automatically generates a `dataDumpExportOperationId` in the response. You MUST:

1. Note the `dataDumpExportOperationId` from each search result
2. Poll it with `checkOperationStatus` until complete
3. Download the CSV from the returned S3 URL
4. Analyze ALL rows with Python/pandas — not just the paginated first page

```bash
# Step 1: Run search (returns first 100 + dataDumpExportOperationId)
mcporter call xpoz.getTwitterPostsByKeywords \
  query='"RLHF" OR "reinforcement learning from human feedback"' \
  startDate="<6 months ago>" \
  fields='["id","text","authorUsername","likeCount","retweetCount","replyCount","impressionCount","createdAtDate"]'

# Step 2: Poll the datadump operation (NOT the search operation)
mcporter call xpoz.checkOperationStatus operationId="op_datadump_XXXXX"
# Repeat every 5 seconds until status=completed → get S3 download URL

# Step 3: Download full CSV
curl -o /tmp/expert-search-q1.csv "<S3_URL>"

# Step 4: Analyze with Python/pandas
python3 analyze_experts.py /tmp/expert-search-q1.csv
```

**Why this matters:** A search returning 2,000 posts only shows 100 in the paginated response. The other 1,900 contain additional experts you'll completely miss. The CSV has the full dataset (up to 64K rows per query).

### Step 6: Search Reddit

```bash
mcporter call xpoz.getRedditPostsByKeywords \
  query='"RLHF" OR "reinforcement learning from human feedback"' \
  fields='["id","title","text","authorUsername","subredditName","score","numComments","createdAtDate"]'
```

Also search for prolific commenters (often the deepest experts comment rather than post):
```bash
mcporter call xpoz.getRedditCommentsByKeywords \
  query='"reward hacking" OR "KL penalty" OR "PPO training"' \
  fields='["id","text","authorUsername","subredditName","score","createdAtDate"]'
```

### Step 7: Extract Candidate Authors (Code Analysis)

**Download all CSV files first** (from Step 5 & 6 datadump operations), then run Python/pandas to build the author frequency table from the FULL dataset:

```python
import pandas as pd
from collections import defaultdict

# Load all CSVs
dfs = []
for f, tier in [("q1-core.csv", 1), ("q2-technical.csv", 2), ("q3-adjacent.csv", 3), ("q4-discussion.csv", 4)]:
    df = pd.read_csv(f"/tmp/expert-{f}")
    df["tier"] = tier
    dfs.append(df)

all_posts = pd.concat(dfs, ignore_index=True)

# Aggregate by author
authors = all_posts.groupby("author_username").agg(
    post_count=("id", "count"),
    total_likes=("like_count", "sum"),
    avg_likes=("like_count", "mean"),
    total_impressions=("impression_count", "sum"),
    avg_impressions=("impression_count", "mean"),
    tiers_hit=("tier", lambda x: len(set(x))),
    tier_list=("tier", lambda x: sorted(set(x))),
).sort_values("post_count", ascending=False)

# Filter: minimum 3 posts, at least 2 tiers
candidates = authors[(authors["post_count"] >= 3) & (authors["tiers_hit"] >= 2)]
print(f"Found {len(candidates)} candidates from {len(all_posts)} total posts")
print(candidates.head(30).to_string())
```

**Key signal: authors who appear across MULTIPLE query tiers, especially Tier 2 (technical jargon), are more likely genuine experts.**

Additional filters:
- **Minimum 3 posts** on-topic in the timeframe
- **Hit at least 2 query tiers** (breadth of domain coverage)
- Remove obvious bots (`isInauthentic` check on Twitter)
- Weight Tier 2 matches higher — using niche jargon naturally is the strongest expertise signal

---

## Phase 3: Expert Analysis & Classification

### Step 8: Deep-Dive Top Candidates

For top 20-30 candidates by frequency + engagement, fetch full profiles:

**Twitter:**
```bash
mcporter call xpoz.getTwitterUser \
  identifier="USERNAME" \
  identifierType="username" \
  fields='["username","name","description","followersCount","followingCount","tweetCount","verified","verifiedType","avgTweetsPerDayLastMonth","isInauthentic","isInauthenticProbScore"]'
```

**Reddit:**
```bash
mcporter call xpoz.getRedditUser \
  username="USERNAME" \
  fields='["username","totalKarma","linkKarma","commentKarma","profileDescription","isMod","createdAt"]'
```

⚠️ **Rate Limit:** Space API requests at least 1 second apart.

### Step 9: Analyze Content Depth

Fetch recent posts for each candidate:

**Twitter:**
```bash
mcporter call xpoz.getTwitterPostsByAuthor \
  identifier="USERNAME" \
  identifierType="username" \
  startDate="<6 months ago>" \
  fields='["id","text","likeCount","retweetCount","replyCount","impressionCount","createdAtDate"]'
```

**Reddit:**
```bash
mcporter call xpoz.getRedditPostsByAuthor \
  username="USERNAME" \
  fields='["id","title","text","subredditName","score","numComments","createdAtDate"]'
```

### Step 10: Classify Expert Type

Analyze each candidate's content to classify them into one of these types:

| Type | Signals | Example |
|------|---------|---------|
| **🔬 Deep Expert** | Uses advanced jargon naturally, shares original research/findings, explains complex concepts, references papers/data, corrects others' misconceptions | PhD researcher, core contributor |
| **💡 Thought Leader** | High-level strategic takes, predicts trends, large audience, quoted by others, speaks at conferences | Industry analyst, CEO/CTO |
| **🛠️ Practitioner** | Shares hands-on experience, tutorials, "I built this", troubleshooting tips, real-world use cases | Senior engineer, consultant |
| **📣 Evangelist/Curator** | Aggregates and shares others' work, summarizes developments, high posting frequency, good at distilling | Newsletter author, community manager |
| **🎓 Educator** | Explains concepts clearly, creates learning content, threads/guides, answers beginner questions | Professor, course creator, tech writer |

**Classification heuristics:**

**Deep Expert signals:**
- Uses Tier 2 (technical jargon) terms naturally, not just quoting
- Posts contain original analysis, numbers, or data
- Other experts engage with their posts (reply quality > reply quantity)
- Bio mentions research, PhD, specific technical role
- Reddit: high comment karma relative to link karma (explains more than links)
- Posts corrections or nuanced takes ("actually, the issue is...")

**Thought Leader signals:**
- High follower count relative to posting frequency
- Posts get high impressions/engagement with non-technical language
- Makes predictions, shares opinions on industry direction
- Bio mentions advisory roles, speaking, investing
- Engages with broad themes, not just technical details

**Practitioner signals:**
- "I built", "we shipped", "in production", "at scale"
- Shares code, configs, architecture decisions
- Discusses tradeoffs and real-world limitations
- Bio mentions specific company/product/project

**Evangelist/Curator signals:**
- High posting frequency
- Mostly shares/retweets others' content with commentary
- "Thread 🧵", "roundup", "this week in..."
- Links to many different sources

**Educator signals:**
- "Explained simply", "beginner's guide", "ELI5"
- Step-by-step breakdowns
- Creates visual explanations
- Active in help/question threads on Reddit

A person can be multiple types (e.g., Deep Expert + Educator). Assign primary and optional secondary type.

### Step 11: Score & Rank

**Expertise Score (0-100):**

| Factor | Weight | How to Measure |
|--------|--------|----------------|
| **Domain depth** | 30 | Tier 2 query matches, jargon usage, original analysis |
| **Consistency** | 20 | How regularly they post about the domain (not just one viral post) |
| **Peer recognition** | 20 | Engagement FROM other experts (replies, quotes), not just raw likes |
| **Breadth** | 15 | Number of query tiers hit, adjacent topics covered |
| **Credentials** | 15 | Bio signals (title, company, education, verified status) |

**Scoring guidelines:**

| Score | Meaning |
|-------|---------|
| 80-100 | Definitive authority — one of the top voices in this domain |
| 60-79 | Strong expert — deeply knowledgeable, regularly contributes |
| 40-59 | Solid practitioner — good knowledge, some influence |
| 20-39 | Engaged participant — discusses the topic but limited depth |

**Engagement quality matters more than quantity:**
- 10 replies from domain experts > 1000 likes from general audience
- Consistent posting about the topic > one viral thread
- Original insights > resharing others' work

---

## Phase 4: Report

### Step 12: Generate Expert Report

Present results grouped by expert type, ranked by score within each group.

```markdown
## Expert Report: [Domain]
**Date:** YYYY-MM-DD
**Sources:** Twitter, Reddit
**Timeframe:** Last 6 months
**Posts analyzed:** X,XXX across Y queries

---

### Summary
Found **N experts** across X candidates analyzed.
- 🔬 Deep Experts: N
- 💡 Thought Leaders: N
- 🛠️ Practitioners: N
- 📣 Evangelists/Curators: N
- 🎓 Educators: N

### Top Experts

#### 🥇 1. @username — 🔬 Deep Expert (Score: 92)
**Platform:** Twitter | **Followers:** 12.4K
**Bio:** [their bio]
**Why expert:** [specific evidence — e.g., "Published 23 posts about reward model optimization, uses advanced terminology naturally, cited by 3 other experts in our results"]
**Key post:** "[quote of their most insightful post]" — ❤️ 342 🔁 89
**Domain coverage:** Core ✅ Technical ✅ Adjacent ✅ Discussion ✅
**Posting frequency:** ~4 posts/week on this topic

---

#### 🥈 2. u/username — 🛠️ Practitioner + 🎓 Educator (Score: 85)
**Platform:** Reddit | **Karma:** 45.2K (32K comment)
**Active in:** r/MachineLearning, r/LocalLLaMA
**Why expert:** [specific evidence]
**Key post:** "[quote]" — ⬆️ 234, 67 comments
...
```

### Email Format (if requested)

Use himalaya MML format with card-based layout:

```
From: Expert Finder <net-service@xpoz.ai>
To: recipient@example.com
Subject: Expert Report: [Domain] — Top N Experts Found

<#multipart type=alternative>
Expert Report: [Domain]
Found N experts across Twitter and Reddit.
[plain text summary]

<#part type=text/html>
<html>
<head>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
  .container { max-width: 680px; margin: 0 auto; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 24px; margin-bottom: 16px; }
  .expert-type { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
  .type-deep { background: #dbeafe; color: #1e40af; }
  .type-leader { background: #fef3c7; color: #92400e; }
  .type-practitioner { background: #d1fae5; color: #065f46; }
  .type-evangelist { background: #ede9fe; color: #5b21b6; }
  .type-educator { background: #fce7f3; color: #9d174d; }
  .score { font-size: 24px; font-weight: 700; color: #111; }
  .quote { border-left: 3px solid #e5e7eb; padding-left: 12px; color: #6b7280; font-style: italic; margin: 12px 0; }
</style>
</head>
<body>
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;margin:0 auto;">
<tr><td>
  <h1 style="font-size:22px;">Expert Report: [Domain]</h1>
  <p style="color:#6b7280;">Found N experts · Twitter + Reddit · Last 6 months</p>

  <!-- Repeat per expert -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);padding:24px;margin-bottom:16px;">
  <tr><td style="padding:24px;">
    <table width="100%"><tr>
      <td><strong style="font-size:18px;">#1 @username</strong><br/>
        <span style="background:#dbeafe;color:#1e40af;padding:2px 10px;border-radius:12px;font-size:12px;">🔬 Deep Expert</span>
      </td>
      <td align="right"><span style="font-size:28px;font-weight:700;">92</span><br/><span style="color:#6b7280;font-size:12px;">score</span></td>
    </tr></table>
    <p style="color:#6b7280;margin:8px 0;">Twitter · 12.4K followers · 4 posts/week on topic</p>
    <p><strong>Why:</strong> Published 23 posts about reward model optimization...</p>
    <div style="border-left:3px solid #e5e7eb;padding-left:12px;color:#6b7280;font-style:italic;margin:12px 0;">
      "Their most insightful post quoted here" — ❤️ 342 🔁 89
    </div>
  </td></tr>
  </table>
  <!-- End repeat -->

</td></tr>
</table>
</body>
</html>
<#/multipart>
```

---

## Tips for Best Results

1. **Narrow beats broad** — "kubernetes network policy debugging" finds deeper experts than just "kubernetes"
2. **Technical jargon is gold** — Tier 2 queries are the best expert signal
3. **Reddit comments > Reddit posts** — The deepest experts often comment rather than post
4. **6-month window is ideal** — Long enough for consistency, recent enough for relevance
5. **Cross-platform presence** — Someone active on both Twitter AND Reddit in the same domain is a strong signal
6. **Check who experts engage with** — If expert A replies to person B's technical posts, person B is likely also an expert
