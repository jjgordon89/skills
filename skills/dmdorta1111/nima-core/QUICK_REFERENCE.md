# NIMA Core Quick Reference

## Panksepp Affects (Index Order)
0. **SEEKING** (Curiosity, Exploration)
1. **RAGE** (Anger, Frustration)
2. **FEAR** (Anxiety, Threat)
3. **LUST** (Desire, Passion)
4. **CARE** (Nurturing, Love)
5. **PANIC** (Grief, Separation)
6. **PLAY** (Joy, Humor)

## Python API

```python
from nima_core import DynamicAffectSystem, baseline_from_description

# Init
affect = DynamicAffectSystem(
    identity_name="bot", 
    baseline="guardian" # or [0.5, ...] or {"archetype": "x", "modifiers": {}}
)

# Usage
affect.process_input({"CARE": 0.8}, intensity=1.0)
current = affect.current.dominant() # ('CARE', 0.85)
vector = affect.get_panksepp_vector() # np.array([...])

# Modulator
from nima_core import modulate_response
guidance = modulate_response(affect)
print(guidance.tone, guidance.style)
```

## OpenClaw Plugin Config

```json
"nima-affect": {
  "identity_name": "MyBot",
  "baseline": "guardian", 
  "skipSubagents": true
}
```

## CLI Tools

```bash
# Check current state
python3 -m nima_core.cognition.dynamic_affect status --name MyBot

# Reset to baseline
python3 -m nima_core.cognition.dynamic_affect reset --name MyBot

# Test decay
python3 -m nima_core.cognition.dynamic_affect decay --name MyBot
```

## File Locations

- **State:** `~/.nima/affect/affect_state_{name}.json`
- **Env Var:** `NIMA_HOME` (overrides `~/.nima`)
