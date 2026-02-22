---
name: comms-md-reader
description: "Read and adapt to someone's comms.md before contacting them. Use when: (1) drafting a message, email, or outreach to someone who has a comms.md, (2) scheduling or proposing a call with someone who has a comms.md, (3) the user asks you to check someone's communication preferences, (4) you need to calibrate tone, channel, or timing for a message to a specific person."
metadata:
  openclaw:
    version: "1.0.0"
    author: "stedman"
    related:
      - comms-md
---

# comms.md Reader

Adapt outreach and messaging based on a recipient's published communication preferences.

## Related Skills

- **comms-md** — the companion skill for creating a comms.md through guided interview

## When This Triggers

Before sending a message, email, or scheduling a call on behalf of the user — check whether the recipient has a comms.md. Common locations:

- Their personal website (e.g. `example.com/comms.md`, `example.com/.well-known/comms.md`)
- Linked from their bio or contact page
- Shared directly in prior correspondence
- In a local contacts directory or vault

If no comms.md is found, skip this skill and draft normally.

## How to Read It

A comms.md has up to seven sections. Not all will be present. Extract what's relevant to the current task:

| Section | Use it for |
| --- | --- |
| **Style & Strengths** | Understanding their communication personality; avoiding their failure modes |
| **Collaboration Model** | Structuring a working relationship or partnership ask |
| **Weekly Rhythm** | Timing your message or proposing meeting slots |
| **Sync Philosophy** | Deciding whether to propose a call vs. async; framing a call agenda |
| **Channel Preferences** | Choosing the right channel and timing for your message |
| **Async Voice** | Calibrating tone, length, formality, and mechanics of your message |
| **Interaction Protocols** | Escalation paths, urgency signals, preferred formats |

## How to Apply It

### Channel Selection

1. Classify the message: urgent/not, complex/simple, professional/casual, high-leverage/low-leverage
2. Match against their **Channel Preferences > Decision Model** table
3. If the user is asking you to use a specific channel that contradicts the recipient's preferences, flag it: "Their comms.md suggests email for this kind of ask — want me to draft it there instead?"

### Timing

1. Check **Weekly Rhythm** for the current day — avoid protected time, low-energy windows, or unavailable blocks
2. Check **Notification & Response Behavior** — if they don't check messages before 3 PM, a morning message is fine but don't expect a fast reply
3. For meeting proposals, only suggest slots that align with their available windows

### Tone Calibration

This is the highest-value adaptation. Read **Async Voice** carefully:

1. **Match their closeness tier.** Determine the relationship: close friend, professional contact, new outreach, re-engagement after a gap. Use the conventions from their matching tier.
2. **Mirror their mechanics.** If they prefer lowercase casual, don't send proper-capped formal prose. If they hate exclamation points, don't use them.
3. **Apply their warm competence signals.** For new/professional contacts: use their name once, reference something specific, close warm not transactional.
4. **Avoid their anti-patterns.** If they list "don't apologize for reaching out" — don't open with "Sorry to bother you." If they say no corporate speak — no "just circling back."

### Call Framing

If proposing a sync:

1. Check **Sync Philosophy** — frame the call around what they use calls for (alignment, routing, decisions), not what they don't (problem-solving, deliberation)
2. Keep the ask tight: proposed agenda, estimated duration, and what you need from them
3. If async could work instead, say so — many comms.md authors explicitly prefer async

## Output Behavior

- **Don't quote the comms.md back to them.** Just adapt silently. Nobody wants to feel like they're being processed.
- **Do flag conflicts to the user.** If the user's instructions contradict the recipient's stated preferences, surface it as a choice, not a blocker.
- **Do note missing sections.** If you needed timing info but their comms.md doesn't have a weekly rhythm, tell the user: "Their comms.md doesn't cover availability — you may want to ask."

## Example

User asks: "Draft an email to Alex about collaborating on the fitness content series."

1. Fetch Alex's comms.md
2. It's a professional/outreach context → check Async Voice > Outreach/Asks tier
3. Alex's anti-patterns say no "Hope you're doing well" openers
4. Alex's warm competence signals say: use name once, reference something specific, close warm
5. Alex's channel preferences confirm email is right for professional intros
6. Weekly rhythm shows Wednesday is meeting-heavy — good day to send since they're already in comms mode

Draft adapts accordingly: direct opener referencing Alex's recent work, concise ask, warm close, no filler.
