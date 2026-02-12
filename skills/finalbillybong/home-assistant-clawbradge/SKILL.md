---
name: home-assistant
description: Control Home Assistant devices via ClawBridge API. Use when James asks to turn lights on/off, check device states, or interact with any exposed Home Assistant entities. Handles entity discovery, state checks, and service calls with human approval flow.
---

# Home Assistant Skill

Control Home Assistant devices through ClawBridge (air-gapped API).

## Configuration

- **Base URL:** `http://192.168.0.238:8100`
- **API Key:** `cb_Z2_Kcoc5Efrztj58lk7SlpZISkwbYlkAkxYjLc_U6lY`
- **Discord Webhook:** `https://discord.com/api/webhooks/1471253559323656194/bGAVuOBcC66p7pyuUFN465lXOHdeScffN1ZyclDj1jb8kmgvocgBwd6J-F5W6qmNQymf`

## Real-Time Notifications (Primary Method)

**Python → Discord Direct** — zero AI cost, instant delivery.

### Start Monitoring
```bash
python3 /root/.openclaw/workspace/skills/home-assistant/scripts/ha-discord.py &
```

### Stop Monitoring
```bash
process kill sessionId={session_id}
```

### Filter Entities

Edit `scripts/ha-discord.py`:
```python
# Watch only these (empty = all)
WATCH_ENTITIES = ["light.office", "binary_sensor.front_door"]

# Ignore these
IGNORE_ENTITIES = ["sensor.cpu_temp"]
```

### When James Asks to Monitor a New Device

1. **Ask:** What's the entity_id? What state to watch for?
2. **Update** `WATCH_ENTITIES` or `IGNORE_ENTITIES` in the script
3. **Restart** the monitor

## Device Control

### Check Exposed Entities
```bash
curl -s "http://192.168.0.238:8100/api/states" \
  -H "Authorization: Bearer cb_Z2_Kcoc5Efrztj58lk7SlpZISkwbYlkAkxYjLc_U6lY" \
  | grep -o '"entity_id": "[^"]*"' | cut -d'"' -f4
```

### Check Entity State
```bash
curl -s "http://192.168.0.238:8100/api/states/{entity_id}" \
  -H "Authorization: Bearer cb_Z2_Kcoc5Efrztj58lk7SlpZISkwbYlkAkxYjLc_U6lY"
```

### Control a Device
```bash
curl -s -X POST "http://192.168.0.238:8100/api/services/{domain}/{service}" \
  -H "Authorization: Bearer cb_Z2_Kcoc5Efrztj58lk7SlpZISkwbYlkAkxYjLc_U6lY" \
  -H "Content-Type: application/json" \
  -d '{"entity_id": "{entity_id}"}'
```

**Note:** Service calls require human approval via ClawBridge UI.

### Quick Script
```bash
./skills/home-assistant/scripts/ha-control.sh state light.office
./skills/home-assistant/scripts/ha-control.sh on light.office
./skills/home-assistant/scripts/ha-control.sh off light.office
```

## Notification Formats

| Domain | Message |
|--------|---------|
| light | 💡 **{name}** turned **on/off** |
| switch | 🔌 **{name}** turned **on/off** |
| binary_sensor (door) | 🚪 **{name}** **opened/closed** |
| binary_sensor (motion) | 📡 **{name}** **motion detected** |
| person | 👤 **{name}** is now **{state}** |
| lock | 🔒 **{name}** **locked/unlocked** |
| other | 🔔 **{name}** `old` → `new` |

## Scripts

| Script | Purpose |
|--------|---------|
| `ha-discord.py` | **Primary** — WebSocket → Discord direct (zero cost) |
| `ha-monitor.py` | WebSocket → file (for cron-based delivery) |
| `ha-control.sh` | Quick CLI for on/off/state |

## API Reference

See [references/clawbridge-api.md](references/clawbridge-api.md)
