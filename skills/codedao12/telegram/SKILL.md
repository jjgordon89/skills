---
name: telegram
description: Guidance for basic Telegram Bot integrations: webhook/polling setup, messaging, security, and operations.
---

# Telegram Bot Guide

## Goal
Provide a practical baseline for Telegram Bot integrations: bot creation, webhook/polling setup, message handling, and safe operations.

## Use when
- You need a Telegram bot for notifications or ops.
- You need to describe webhook flow and event handling.
- You want a security/rate-limit checklist.

## Do not use when
- The request involves policy violations or spam.

## Core topics
- Bot token handling: secure storage and rotation.
- Webhook vs polling: trade-offs and use cases.
- Message handling: commands, callbacks, files.
- Ops: rate limits, retries, logging, admin controls.

## Required inputs
- Bot purpose (notify/ops/support).
- Deployment model (serverless/server).
- Security posture and access control.

## Expected output
- A clear integration plan with a technical checklist.

## Notes
- Never commit tokens to a repo.
- Avoid sending sensitive data over chat.
