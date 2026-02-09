#!/bin/bash
API_BASE="${EYEBOT_API:-http://93.186.255.184:8001}"
curl -s -X POST "${API_BASE}/api/walletbot" -H "Content-Type: application/json" -d "{\"request\": \"$*\", \"auto_pay\": true}"
