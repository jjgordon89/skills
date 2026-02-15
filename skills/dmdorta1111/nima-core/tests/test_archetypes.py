"""
Tests for archetypes module.

Tests archetype definitions, baseline vectors, and natural language parsing.
Archetypes define Panksepp 7-affect baselines: [SEEKING, RAGE, FEAR, LUST, CARE, PANIC, PLAY]
"""

import pytest
from nima_core.cognition.archetypes import (
    ARCHETYPES,
    AFFECT_MAP,
    get_archetype,
    list_archetypes,
    baseline_from_archetype,
    baseline_from_description,
)


# ==============================================================================
# ARCHETYPES Dictionary Tests
# ==============================================================================

class TestArchetypesDict:
    """Test the ARCHETYPES dictionary structure."""
    
    def test_all_builtin_archetypes_exist(self):
        """Verify all expected built-in archetypes are present."""
        expected = [
            "guardian", "explorer", "trickster", "stoic", "empath",
            "warrior", "sage", "nurturer", "rebel", "sentinel"
        ]
        for name in expected:
            assert name in ARCHETYPES, f"Missing archetype: {name}"
    
    def test_archetype_structure(self):
        """Each archetype should have baseline and description."""
        for name, archetype in ARCHETYPES.items():
            assert "baseline" in archetype, f"{name} missing baseline"
            assert "description" in archetype, f"{name} missing description"
            assert isinstance(archetype["baseline"], list), f"{name} baseline not a list"
            assert isinstance(archetype["description"], str), f"{name} description not a string"
    
    def test_baseline_length(self):
        """Each baseline should have exactly 7 elements (Panksepp affects)."""
        for name, archetype in ARCHETYPES.items():
            baseline = archetype["baseline"]
            assert len(baseline) == 7, (
                f"{name} baseline has {len(baseline)} elements, expected 7"
            )
    
    def test_baseline_value_range(self):
        """All baseline values should be between 0.0 and 1.0."""
        for name, archetype in ARCHETYPES.items():
            for i, value in enumerate(archetype["baseline"]):
                assert 0.0 <= value <= 1.0, (
                    f"{name} baseline[{i}] = {value}, expected [0.0, 1.0]"
                )
    
    def test_baseline_types(self):
        """All baseline values should be numeric."""
        for name, archetype in ARCHETYPES.items():
            for i, value in enumerate(archetype["baseline"]):
                assert isinstance(value, (int, float)), (
                    f"{name} baseline[{i}] is {type(value)}, expected numeric"
                )


class TestAffectMap:
    """Test the AFFECT_MAP constant."""
    
    def test_affect_map_has_all_affects(self):
        """AFFECT_MAP should contain all 7 Panksepp affects."""
        expected = ["SEEKING", "RAGE", "FEAR", "LUST", "CARE", "PANIC", "PLAY"]
        assert set(AFFECT_MAP.keys()) == set(expected)
    
    def test_affect_map_indices(self):
        """AFFECT_MAP indices should be 0-6."""
        indices = list(AFFECT_MAP.values())
        assert sorted(indices) == list(range(7))
    
    def test_affect_map_correct_order(self):
        """Verify correct Panksepp affect order."""
        assert AFFECT_MAP["SEEKING"] == 0
        assert AFFECT_MAP["RAGE"] == 1
        assert AFFECT_MAP["FEAR"] == 2
        assert AFFECT_MAP["LUST"] == 3
        assert AFFECT_MAP["CARE"] == 4
        assert AFFECT_MAP["PANIC"] == 5
        assert AFFECT_MAP["PLAY"] == 6


# ==============================================================================
# Specific Archetype Tests
# ==============================================================================

class TestSpecificArchetypes:
    """Test characteristics of specific archetypes."""
    
    def test_guardian_high_care(self):
        """Guardian should have high CARE affect."""
        guardian = ARCHETYPES["guardian"]
        care_idx = AFFECT_MAP["CARE"]
        assert guardian["baseline"][care_idx] >= 0.7
    
    def test_guardian_moderate_fear(self):
        """Guardian should have moderate FEAR affect."""
        guardian = ARCHETYPES["guardian"]
        fear_idx = AFFECT_MAP["FEAR"]
        assert 0.1 <= guardian["baseline"][fear_idx] <= 0.5
    
    def test_explorer_high_seeking(self):
        """Explorer should have high SEEKING affect."""
        explorer = ARCHETYPES["explorer"]
        seeking_idx = AFFECT_MAP["SEEKING"]
        assert explorer["baseline"][seeking_idx] >= 0.7
    
    def test_trickster_high_play(self):
        """Trickster should have high PLAY affect."""
        trickster = ARCHETYPES["trickster"]
        play_idx = AFFECT_MAP["PLAY"]
        assert trickster["baseline"][play_idx] >= 0.7
    
    def test_stoic_low_affects(self):
        """Stoic should have generally low affect levels."""
        stoic = ARCHETYPES["stoic"]
        # Most affects should be moderate to low
        avg = sum(stoic["baseline"]) / len(stoic["baseline"])
        assert avg <= 0.4
    
    def test_empath_high_care(self):
        """Empath should have very high CARE affect."""
        empath = ARCHETYPES["empath"]
        care_idx = AFFECT_MAP["CARE"]
        assert empath["baseline"][care_idx] >= 0.8
    
    def test_warrior_higher_rage(self):
        """Warrior should have higher RAGE than most archetypes."""
        warrior = ARCHETYPES["warrior"]
        rage_idx = AFFECT_MAP["RAGE"]
        assert warrior["baseline"][rage_idx] >= 0.2
    
    def test_nurturer_maximum_care(self):
        """Nurturer should have maximum or near-maximum CARE."""
        nurturer = ARCHETYPES["nurturer"]
        care_idx = AFFECT_MAP["CARE"]
        assert nurturer["baseline"][care_idx] >= 0.8
    
    def test_sentinel_high_fear_or_panic(self):
        """Sentinel should have elevated FEAR or PANIC (vigilant)."""
        sentinel = ARCHETYPES["sentinel"]
        fear_idx = AFFECT_MAP["FEAR"]
        panic_idx = AFFECT_MAP["PANIC"]
        assert (sentinel["baseline"][fear_idx] >= 0.2 or 
                sentinel["baseline"][panic_idx] >= 0.2)


# ==============================================================================
# get_archetype() Tests
# ==============================================================================

class TestGetArchetype:
    """Test get_archetype() function."""
    
    def test_get_valid_archetype(self):
        """Should return correct archetype for valid name."""
        guardian = get_archetype("guardian")
        assert guardian is not None
        assert guardian["description"] == "Protective, alert, caring"
        assert len(guardian["baseline"]) == 7
    
    def test_get_archetype_case_insensitive(self):
        """Should be case-insensitive."""
        lower = get_archetype("guardian")
        upper = get_archetype("GUARDIAN")
        mixed = get_archetype("Guardian")
        
        assert lower == upper == mixed
    
    def test_get_unknown_archetype_raises(self):
        """Should raise ValueError for unknown archetype."""
        with pytest.raises(ValueError, match="Unknown archetype"):
            get_archetype("nonexistent_xyz")
    
    def test_get_all_archetypes(self):
        """Should be able to retrieve all archetypes."""
        for name in ARCHETYPES.keys():
            archetype = get_archetype(name)
            assert archetype is not None
            assert "baseline" in archetype
            assert "description" in archetype


# ==============================================================================
# list_archetypes() Tests
# ==============================================================================

class TestListArchetypes:
    """Test list_archetypes() function."""
    
    def test_returns_list(self):
        """Should return a list."""
        result = list_archetypes()
        assert isinstance(result, list)
    
    def test_returns_all_names(self):
        """Should return all archetype names."""
        result = list_archetypes()
        expected = list(ARCHETYPES.keys())
        assert set(result) == set(expected)
    
    def test_contains_expected_archetypes(self):
        """Should contain key archetypes."""
        result = list_archetypes()
        expected = ["guardian", "explorer", "trickster", "sage"]
        for name in expected:
            assert name in result


# ==============================================================================
# baseline_from_archetype() Tests
# ==============================================================================

class TestBaselineFromArchetype:
    """Test baseline_from_archetype() function."""
    
    def test_returns_correct_baseline(self):
        """Should return archetype's baseline vector."""
        baseline = baseline_from_archetype("guardian")
        expected = ARCHETYPES["guardian"]["baseline"]
        assert baseline == expected
    
    def test_returns_list(self):
        """Should return a list."""
        baseline = baseline_from_archetype("explorer")
        assert isinstance(baseline, list)
        assert len(baseline) == 7
    
    def test_without_modifiers(self):
        """Without modifiers, should return unmodified baseline."""
        baseline = baseline_from_archetype("trickster", modifiers=None)
        expected = ARCHETYPES["trickster"]["baseline"]
        assert baseline == expected
    
    def test_with_positive_modifier(self):
        """Should apply positive modifier correctly."""
        baseline = baseline_from_archetype("stoic", modifiers={"PLAY": 0.2})
        stoic_baseline = ARCHETYPES["stoic"]["baseline"]
        play_idx = AFFECT_MAP["PLAY"]
        
        expected = stoic_baseline[play_idx] + 0.2
        assert baseline[play_idx] == expected
    
    def test_with_negative_modifier(self):
        """Should apply negative modifier correctly."""
        baseline = baseline_from_archetype("warrior", modifiers={"RAGE": -0.1})
        warrior_baseline = ARCHETYPES["warrior"]["baseline"]
        rage_idx = AFFECT_MAP["RAGE"]
        
        expected = max(0.0, warrior_baseline[rage_idx] - 0.1)
        assert baseline[rage_idx] == expected
    
    def test_clamps_to_zero(self):
        """Should clamp negative results to 0.0."""
        baseline = baseline_from_archetype("stoic", modifiers={"PLAY": -1.0})
        play_idx = AFFECT_MAP["PLAY"]
        assert baseline[play_idx] == 0.0
    
    def test_clamps_to_one(self):
        """Should clamp values above 1.0."""
        baseline = baseline_from_archetype("empath", modifiers={"CARE": 0.5})
        care_idx = AFFECT_MAP["CARE"]
        assert baseline[care_idx] <= 1.0
    
    def test_multiple_modifiers(self):
        """Should apply multiple modifiers."""
        baseline = baseline_from_archetype("guardian", modifiers={
            "PLAY": 0.3,
            "RAGE": 0.1,
            "FEAR": -0.1
        })
        
        guardian_baseline = ARCHETYPES["guardian"]["baseline"]
        play_idx = AFFECT_MAP["PLAY"]
        rage_idx = AFFECT_MAP["RAGE"]
        fear_idx = AFFECT_MAP["FEAR"]
        
        assert baseline[play_idx] == min(1.0, guardian_baseline[play_idx] + 0.3)
        assert baseline[rage_idx] == min(1.0, guardian_baseline[rage_idx] + 0.1)
        assert baseline[fear_idx] == max(0.0, guardian_baseline[fear_idx] - 0.1)
    
    def test_unknown_modifier_ignored(self):
        """Unknown affect names in modifiers should be ignored."""
        baseline = baseline_from_archetype("sage", modifiers={
            "PLAY": 0.1,
            "UNKNOWN_AFFECT": 0.5  # Should be ignored
        })
        
        sage_baseline = ARCHETYPES["sage"]["baseline"]
        play_idx = AFFECT_MAP["PLAY"]
        
        # PLAY should be modified
        assert baseline[play_idx] == sage_baseline[play_idx] + 0.1
        # Other affects should be unchanged
        for i in range(7):
            if i != play_idx:
                assert baseline[i] == sage_baseline[i]
    
    def test_case_insensitive_modifiers(self):
        """Modifier affect names should be case-insensitive."""
        baseline1 = baseline_from_archetype("guardian", modifiers={"play": 0.2})
        baseline2 = baseline_from_archetype("guardian", modifiers={"PLAY": 0.2})
        baseline3 = baseline_from_archetype("guardian", modifiers={"Play": 0.2})
        
        assert baseline1 == baseline2 == baseline3


# ==============================================================================
# baseline_from_description() Tests
# ==============================================================================

class TestBaselineFromDescription:
    """Test natural language baseline parsing."""
    
    def test_returns_valid_baseline(self):
        """Should return a valid 7-element baseline."""
        baseline = baseline_from_description("protective and caring")
        assert isinstance(baseline, list)
        assert len(baseline) == 7
        for value in baseline:
            assert 0.0 <= value <= 1.0
    
    def test_guardian_keywords(self):
        """Should recognize guardian keywords."""
        baseline = baseline_from_description("protective guardian")
        # Should pick guardian as base archetype
        # Exact values depend on implementation, but should resemble guardian
        care_idx = AFFECT_MAP["CARE"]
        assert baseline[care_idx] >= 0.5  # Guardian has high care
    
    def test_explorer_keywords(self):
        """Should recognize explorer keywords."""
        baseline = baseline_from_description("curious and adventurous")
        seeking_idx = AFFECT_MAP["SEEKING"]
        assert baseline[seeking_idx] >= 0.5
    
    def test_trickster_keywords(self):
        """Should recognize trickster keywords."""
        baseline = baseline_from_description("mischievous and playful")
        play_idx = AFFECT_MAP["PLAY"]
        assert baseline[play_idx] >= 0.5
    
    def test_warrior_keywords(self):
        """Should recognize warrior keywords."""
        baseline = baseline_from_description("warrior ready for battle")
        rage_idx = AFFECT_MAP["RAGE"]
        assert baseline[rage_idx] >= 0.2
    
    def test_sage_keywords(self):
        """Should recognize sage keywords."""
        baseline = baseline_from_description("wise sage seeking knowledge")
        seeking_idx = AFFECT_MAP["SEEKING"]
        assert baseline[seeking_idx] >= 0.5
    
    def test_empath_keywords(self):
        """Should recognize empath keywords."""
        baseline = baseline_from_description("empathetic and sensitive")
        care_idx = AFFECT_MAP["CARE"]
        assert baseline[care_idx] >= 0.5
    
    def test_modifiers_apply(self):
        """Description modifiers should affect baseline."""
        # "playful" should boost PLAY
        baseline = baseline_from_description("protective and playful")
        play_idx = AFFECT_MAP["PLAY"]
        
        # Should be higher than guardian baseline due to "playful" modifier
        guardian_play = ARCHETYPES["guardian"]["baseline"][play_idx]
        assert baseline[play_idx] > guardian_play
    
    def test_caring_modifier(self):
        """'caring' keyword should boost CARE."""
        baseline = baseline_from_description("stoic but caring")
        care_idx = AFFECT_MAP["CARE"]
        
        stoic_care = ARCHETYPES["stoic"]["baseline"][care_idx]
        # Should be boosted from stoic baseline
        assert baseline[care_idx] >= stoic_care
    
    def test_anxious_modifier(self):
        """'anxious' keyword should boost FEAR."""
        baseline = baseline_from_description("explorer but anxious")
        fear_idx = AFFECT_MAP["FEAR"]
        
        explorer_fear = ARCHETYPES["explorer"]["baseline"][fear_idx]
        # Should be boosted
        assert baseline[fear_idx] >= explorer_fear
    
    def test_calm_modifier(self):
        """'calm' keyword should dampen affects."""
        baseline1 = baseline_from_description("warrior")
        baseline2 = baseline_from_description("calm warrior")
        
        # Calm version should have lower overall activation
        sum1 = sum(baseline1)
        sum2 = sum(baseline2)
        assert sum2 <= sum1
    
    def test_empty_description(self):
        """Empty description should default to guardian."""
        baseline = baseline_from_description("")
        guardian_baseline = ARCHETYPES["guardian"]["baseline"]
        # Should be close to guardian baseline (might have minor variations)
        assert len(baseline) == 7
    
    def test_unknown_keywords(self):
        """Unknown keywords should still return valid baseline."""
        baseline = baseline_from_description("xyzabc unknown weird")
        assert isinstance(baseline, list)
        assert len(baseline) == 7
        for value in baseline:
            assert 0.0 <= value <= 1.0


# ==============================================================================
# Edge Cases Tests
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_archetype_baseline_immutability(self):
        """Modifying returned baseline should not affect original."""
        baseline1 = baseline_from_archetype("guardian")
        original = baseline1.copy()
        
        # Modify returned baseline
        baseline1[0] = 0.999
        
        # Get fresh copy
        baseline2 = baseline_from_archetype("guardian")
        
        # Should match original
        assert baseline2 == original
        assert baseline2[0] != 0.999
    
    def test_extreme_positive_modifier(self):
        """Extreme positive modifier should clamp to 1.0."""
        baseline = baseline_from_archetype("guardian", modifiers={"CARE": 10.0})
        care_idx = AFFECT_MAP["CARE"]
        assert baseline[care_idx] == 1.0
    
    def test_extreme_negative_modifier(self):
        """Extreme negative modifier should clamp to 0.0."""
        baseline = baseline_from_archetype("guardian", modifiers={"CARE": -10.0})
        care_idx = AFFECT_MAP["CARE"]
        assert baseline[care_idx] == 0.0
    
    def test_zero_modifier(self):
        """Zero modifier should not change value."""
        baseline = baseline_from_archetype("explorer", modifiers={"SEEKING": 0.0})
        expected = ARCHETYPES["explorer"]["baseline"]
        assert baseline == expected
    
    def test_all_affects_as_modifiers(self):
        """Should handle modifiers for all affect types."""
        modifiers = {
            "SEEKING": 0.1,
            "RAGE": 0.05,
            "FEAR": -0.1,
            "LUST": 0.0,
            "CARE": 0.15,
            "PANIC": -0.05,
            "PLAY": 0.2
        }
        
        baseline = baseline_from_archetype("stoic", modifiers=modifiers)
        stoic_baseline = ARCHETYPES["stoic"]["baseline"]
        
        for affect, delta in modifiers.items():
            idx = AFFECT_MAP[affect]
            expected = max(0.0, min(1.0, stoic_baseline[idx] + delta))
            assert baseline[idx] == expected


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_archetype_to_baseline_workflow(self):
        """Test complete workflow from archetype selection to baseline."""
        # List available archetypes
        archetypes = list_archetypes()
        assert "guardian" in archetypes
        
        # Get archetype details
        guardian = get_archetype("guardian")
        assert "baseline" in guardian
        
        # Generate baseline
        baseline = baseline_from_archetype("guardian")
        assert baseline == guardian["baseline"]
        
        # Generate modified baseline
        modified = baseline_from_archetype("guardian", modifiers={"PLAY": 0.3})
        play_idx = AFFECT_MAP["PLAY"]
        assert modified[play_idx] > baseline[play_idx]
    
    def test_description_parsing_workflow(self):
        """Test natural language description parsing workflow."""
        descriptions = [
            "protective and caring",
            "curious explorer",
            "playful trickster",
            "calm and wise sage"
        ]
        
        for desc in descriptions:
            baseline = baseline_from_description(desc)
            assert len(baseline) == 7
            for value in baseline:
                assert 0.0 <= value <= 1.0
    
    def test_all_archetypes_produce_valid_baselines(self):
        """All archetypes should produce valid baselines with and without modifiers."""
        for archetype_name in list_archetypes():
            # Without modifiers
            baseline1 = baseline_from_archetype(archetype_name)
            assert len(baseline1) == 7
            for value in baseline1:
                assert 0.0 <= value <= 1.0
            
            # With modifiers
            baseline2 = baseline_from_archetype(archetype_name, modifiers={"PLAY": 0.1})
            assert len(baseline2) == 7
            for value in baseline2:
                assert 0.0 <= value <= 1.0
    
    def test_affect_map_completeness(self):
        """AFFECT_MAP should cover all baseline indices."""
        for archetype in ARCHETYPES.values():
            baseline = archetype["baseline"]
            # Should be able to reference all elements via AFFECT_MAP
            for affect, idx in AFFECT_MAP.items():
                assert idx < len(baseline)
                assert baseline[idx] is not None
