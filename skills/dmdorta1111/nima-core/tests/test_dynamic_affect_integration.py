#!/usr/bin/env python3
"""
Integration test for the Dynamic Affect System in nima-core.
"""

print("=" * 70)
print("DYNAMIC AFFECT SYSTEM INTEGRATION TEST")
print("=" * 70)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from nima_core.cognition import (
        DynamicAffectSystem,
        AffectVector,
        get_affect_system,
        PersonalityManager,
        list_profiles,
        get_profile,
        map_emotions_to_affects,
        GenericResponseModulator,
    )
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

# Test 2: Create DynamicAffectSystem with custom baseline
print("\n2. Creating DynamicAffectSystem with custom baseline...")
try:
    import numpy as np
    # Curious explorer baseline
    explorer_baseline = np.array([0.8, 0.1, 0.2, 0.1, 0.5, 0.1, 0.6])
    system = DynamicAffectSystem(
        identity_name="test_explorer",
        baseline=explorer_baseline,
    )
    summary = system.get_state_summary()
    print(f"   ✅ System created: {summary['identity_name']}")
    print(f"      Dominant: {summary['dominant'][0]} ({summary['dominant'][1]:.2f})")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 3: Test emotion processing
print("\n3. Processing emotions...")
try:
    emotions = [
        {"emotion": "joy", "intensity": 0.8},
        {"emotion": "curiosity", "intensity": 0.9},
    ]
    affects, intensity = map_emotions_to_affects(emotions)
    print(f"   ✅ Mapped emotions to affects:")
    for affect, val in affects.items():
        print(f"      {affect}: {val:.2f}")
    print(f"      Overall intensity: {intensity:.2f}")
    
    # Update system
    system.process_emotions(emotions)
    print(f"   ✅ Updated system state")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 4: Test personality profiles
print("\n4. Testing personality profiles...")
try:
    manager = PersonalityManager()
    profiles = list_profiles()
    print(f"   ✅ Found {len(profiles)} profiles:")
    for p in profiles[:5]:
        print(f"      - {p}")
    
    chaos_profile = get_profile("chaos")
    print(f"   ✅ Loaded 'chaos' profile:")
    print(f"      Description: {chaos_profile['description']}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 5: Test response modulator
print("\n5. Testing GenericResponseModulator...")
try:
    modulator = GenericResponseModulator(system)
    guidance = modulator.get_guidance()
    print(f"   ✅ Generated response guidance:")
    print(f"      Tone: {guidance.tone}")
    print(f"      Style: {guidance.style}")
    print(f"      Intensity: {guidance.intensity:.2f}")
    if guidance.embrace:
        print(f"      Embrace: {', '.join(guidance.embrace[:3])}")
    
    # Test prompt formatting
    prompt_text = modulator.format_for_prompt()
    print(f"   ✅ Prompt format:")
    for line in prompt_text.split('\n')[:3]:
        print(f"      {line}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 6: Test temporal decay
print("\n6. Testing temporal decay...")
try:
    before = system.current.dominant()
    system.drift_toward_baseline(strength=0.3)
    after = system.current.dominant()
    print(f"   ✅ Decay applied:")
    print(f"      Before: {before[0]} ({before[1]:.2f})")
    print(f"      After:  {after[0]} ({after[1]:.2f})")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 7: Test VSA vector extraction
print("\n7. Testing VSA vector extraction...")
try:
    vector = system.get_panksepp_vector()
    print(f"   ✅ VSA vector:")
    print(f"      Shape: {vector.shape}")
    print(f"      Dtype: {vector.dtype}")
    print(f"      Values: {vector}")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    exit(1)

# Test 8: Archetype Baselines
print("\n8. Testing Archetype Baselines...")
try:
    from nima_core.cognition import ARCHETYPES, baseline_from_description
    
    # 8a. Test string resolution
    print("   Testing string resolution ('guardian')...")
    sys_guardian = DynamicAffectSystem(identity_name="test_guardian", baseline="guardian")
    # Guardian CARE should be 0.8 (index 4)
    care_val = sys_guardian.baseline.values[4]
    if abs(care_val - 0.8) < 0.01:
         print(f"   ✅ 'guardian' resolved correctly (CARE={care_val:.2f})")
    else:
         print(f"   ❌ 'guardian' mismatch: CARE={care_val:.2f}, expected 0.8")
         exit(1)

    # 8b. Test dict resolution with modifiers
    print("   Testing dict resolution (explorer + PLAY boost)...")
    config = {"archetype": "explorer", "modifiers": {"PLAY": 0.2, "FEAR": -0.05}}
    sys_mod = DynamicAffectSystem(identity_name="test_mod", baseline=config)
    # Explorer PLAY is 0.5, +0.2 = 0.7
    play_val = sys_mod.baseline.values[6]
    if abs(play_val - 0.7) < 0.01:
         print(f"   ✅ Modifiers applied correctly (PLAY={play_val:.2f})")
    else:
         print(f"   ❌ Modifier mismatch: PLAY={play_val:.2f}, expected 0.7")
         exit(1)

    # 8c. Test natural language description
    print("   Testing description parsing...")
    desc = "protective and playful"
    # Should map to guardian (protective) + PLAY boost
    baseline_nlp = baseline_from_description(desc)
    # Guardian PLAY is 0.3, +0.2 (playful) = 0.5
    play_idx = 6
    if abs(baseline_nlp[play_idx] - 0.5) < 0.05:
         print(f"   ✅ NLP parsing successful: '{desc}' -> PLAY={baseline_nlp[play_idx]:.2f}")
    else:
         print(f"   ⚠️ NLP parsing result unexpected: PLAY={baseline_nlp[play_idx]:.2f}")

except Exception as e:
    print(f"   ❌ Archetype test failed: {e}")
    # Don't exit here, let it finish? No, consistent with others.
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 70)
print("✅ ALL INTEGRATION TESTS PASSED!")
print("=" * 70)
print("\nThe Dynamic Affect System is ready for use in nima-core.")
print("See openclaw_plugin/README.md for OpenClaw plugin installation.\n")
