# Test Suite Summary - personality_profiles & archetypes

**Date:** February 13, 2026  
**Status:** ✅ All tests passing (93/93)

## Test Coverage

### test_personality_profiles.py (38 tests)

**Module-level components tested:**
- `DEFAULT_PROFILES` dictionary structure and validation
- `PersonalityManager` class full API
- Module functions: `get_profile()`, `list_profiles()`

**Test categories:**

1. **DEFAULT_PROFILES Validation (8 tests)**
   - All 14 built-in profiles exist
   - Consistent structure (description, emotions, amplifiers, modulator)
   - Emotion/amplifier key consistency
   - Value ranges (emotions: 0-1, amplifiers: ≥0, modulators: 0-1)

2. **Specific Profile Tests (5 tests)**
   - Guardian: High fear/care/trust
   - Chaos: High joy/surprise, low fear/sadness
   - Cold Logic: High curiosity, minimal emotions
   - Empath: All emotions at 1.0, all amplifiers ≥2.0
   - Stoic: Measured, low emotional responses

3. **Module Functions (4 tests)**
   - `get_profile()` - valid/invalid lookups
   - `list_profiles()` - returns all profile names

4. **PersonalityManager Class (10 tests)**
   - Initialization (default/custom storage)
   - Profile retrieval and switching
   - Custom profile creation
   - State persistence across instances
   - Thread safety

5. **Edge Cases (6 tests)**
   - Empty/corrupted state files
   - Case sensitivity
   - Profile overwriting
   - Unknown emotion handling
   - Reference behavior (direct refs, not deep copies)

6. **Integration Tests (2 tests)**
   - Full workflow: create → switch → persist → reload
   - All profiles switchable

### test_archetypes.py (55 tests)

**Module-level components tested:**
- `ARCHETYPES` dictionary (10 built-in archetypes)
- `AFFECT_MAP` constant (Panksepp 7-affect mapping)
- Functions: `get_archetype()`, `list_archetypes()`, `baseline_from_archetype()`, `baseline_from_description()`

**Test categories:**

1. **ARCHETYPES Dictionary (5 tests)**
   - All 10 archetypes present
   - Structure: baseline (7 floats), description
   - Value validation (0.0-1.0 range, 7 elements)

2. **AFFECT_MAP Validation (3 tests)**
   - All 7 Panksepp affects present
   - Correct order: SEEKING, RAGE, FEAR, LUST, CARE, PANIC, PLAY
   - Indices 0-6

3. **Specific Archetype Tests (9 tests)**
   - Guardian: High CARE, moderate FEAR
   - Explorer: High SEEKING
   - Trickster: High PLAY
   - Stoic: Low overall affects
   - Empath: Very high CARE
   - Warrior: Higher RAGE
   - Nurturer: Maximum CARE
   - Sentinel: High FEAR/PANIC

4. **get_archetype() (4 tests)**
   - Valid/invalid lookups
   - Case-insensitive
   - All archetypes retrievable

5. **list_archetypes() (3 tests)**
   - Returns list of all names
   - Contains expected archetypes

6. **baseline_from_archetype() (10 tests)**
   - Returns correct baseline vectors
   - With/without modifiers
   - Positive/negative modifiers
   - Clamping (0.0-1.0 range)
   - Multiple simultaneous modifiers
   - Case-insensitive modifier names
   - Unknown modifiers ignored

7. **baseline_from_description() (12 tests)**
   - Natural language parsing
   - Archetype keyword recognition (guardian, explorer, trickster, warrior, sage, empath)
   - Modifier keywords (playful, caring, anxious, calm)
   - Empty/unknown descriptions handled
   - Valid baselines returned

8. **Edge Cases (5 tests)**
   - Baseline immutability
   - Extreme modifiers (±10.0)
   - Zero modifiers
   - All affects as modifiers

9. **Integration Tests (4 tests)**
   - Full workflow: list → get → generate baseline → apply modifiers
   - Description parsing workflow
   - All archetypes produce valid baselines
   - AFFECT_MAP completeness

## Built-in Profiles Tested

**personality_profiles (14):**
baseline, chaos, guardian, cold_logic, rage, mystic, nihilist, empath, manic, stoic, trickster, berserker, poet, paranoid

**archetypes (10):**
guardian, explorer, trickster, stoic, empath, warrior, sage, nurturer, rebel, sentinel

## Run Command

```bash
cd /Users/lilu/.openclaw/workspace/nima-core
python3 -m pytest tests/test_personality_profiles.py tests/test_archetypes.py -v
```

## Notes

- **AffectVector** and **map_emotions_to_affects()** are located in other modules (`dynamic_affect.py` and `emotion_detection.py`), not in `personality_profiles.py` or `archetypes.py`
- PersonalityManager returns direct references to profiles, not deep copies (documented in tests)
- All tests use temporary directories for persistence testing (no side effects)
- Thread safety tested with basic concurrent switching
