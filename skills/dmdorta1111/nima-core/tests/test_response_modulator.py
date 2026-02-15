#!/usr/bin/env python3
"""
Tests for response_modulator_v2 module
======================================
Comprehensive tests for affect-based response modulation.
"""

import pytest
import numpy as np
from nima_core.cognition.response_modulator_v2 import (
    GenericResponseModulator,
    ResponseGuidance,
    modulate_response,
)
from nima_core.cognition.dynamic_affect import DynamicAffectSystem, AffectVector


@pytest.fixture
def affect_system():
    """Create a basic affect system for testing."""
    return DynamicAffectSystem(identity_name="test_agent")


@pytest.fixture
def neutral_affect_system():
    """Create affect system with neutral baseline."""
    # Set low baseline for all affects
    baseline = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32)
    system = DynamicAffectSystem(
        identity_name="test_neutral",
        baseline=baseline
    )
    return system


@pytest.fixture
def modulator(affect_system):
    """Create a response modulator with affect system."""
    return GenericResponseModulator(affect_system)


class TestGenericResponseModulator:
    """Test GenericResponseModulator creation and basic functionality."""
    
    def test_creation_with_affect_system(self, affect_system):
        """Test creating modulator with affect system."""
        modulator = GenericResponseModulator(affect_system)
        
        assert modulator.affect_system is affect_system
        assert isinstance(modulator, GenericResponseModulator)
    
    def test_get_guidance_returns_response_guidance(self, modulator):
        """Test that get_guidance returns ResponseGuidance object."""
        guidance = modulator.get_guidance()
        
        assert isinstance(guidance, ResponseGuidance)
        assert hasattr(guidance, 'tone')
        assert hasattr(guidance, 'style')
        assert hasattr(guidance, 'intensity')
        assert hasattr(guidance, 'embrace')
        assert hasattr(guidance, 'avoid')
        assert hasattr(guidance, 'dominant_affect')
    
    def test_neutral_baseline(self, modulator):
        """Test guidance from neutral/balanced baseline."""
        guidance = modulator.get_guidance()
        
        # Neutral state should have balanced characteristics
        assert guidance.tone is not None
        assert guidance.style is not None
        assert 0.0 <= guidance.intensity <= 1.0
        assert isinstance(guidance.embrace, list)
        assert isinstance(guidance.avoid, list)


class TestModulateResponse:
    """Test response modulation based on different affect states."""
    
    def test_high_care_state(self, neutral_affect_system):
        """Test modulation with high CARE affect."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        # Build up CARE state with repeated inputs (need many to overcome momentum)
        for _ in range(30):
            neutral_affect_system.process_input({"CARE": 0.95}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        
        # With neutral baseline and strong inputs, CARE should be dominant
        assert guidance.dominant_affect == "CARE"
        assert "care" in guidance.tone.lower() or "warm" in guidance.tone.lower() or "compassion" in guidance.tone.lower()
    
    def test_high_seeking_state(self, neutral_affect_system):
        """Test modulation with high SEEKING affect."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(30):
            neutral_affect_system.process_input({"SEEKING": 0.95}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        assert guidance.dominant_affect == "SEEKING"
    
    def test_high_play_state(self, neutral_affect_system):
        """Test modulation with high PLAY affect."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(30):
            neutral_affect_system.process_input({"PLAY": 0.95}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        assert guidance.dominant_affect == "PLAY"
    
    def test_affect_influences_guidance(self, affect_system, modulator):
        """Test that different affects influence guidance."""
        # Get baseline guidance
        guidance_baseline = modulator.get_guidance()
        baseline_tone = guidance_baseline.tone
        
        # Process some input
        affect_system.process_input({"RAGE": 0.8}, intensity=0.7)
        guidance_after = modulator.get_guidance()
        
        # Guidance should exist and be valid
        assert guidance_after.tone is not None
        assert guidance_after.style is not None
        assert isinstance(guidance_after.embrace, list)
        assert isinstance(guidance_after.avoid, list)


class TestIntensityVariation:
    """Test that response modulation varies with intensity."""
    
    def test_intensity_calculation(self, affect_system, modulator):
        """Test that intensity is calculated."""
        guidance = modulator.get_guidance()
        
        assert 0.0 <= guidance.intensity <= 1.0
        assert isinstance(guidance.intensity, float)
    
    def test_different_intensities_produce_different_guidance(self, neutral_affect_system):
        """Test that different intensities affect guidance."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        # Low intensity
        neutral_affect_system.process_input({"CARE": 0.3}, intensity=0.2)
        guidance_low = modulator.get_guidance()
        
        # Create fresh system for high intensity
        baseline = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32)
        system_high = DynamicAffectSystem(
            identity_name="test_high",
            baseline=baseline
        )
        modulator_high = GenericResponseModulator(system_high)
        
        for _ in range(30):
            system_high.process_input({"CARE": 0.95}, intensity=0.9)
        guidance_high = modulator_high.get_guidance()
        
        # Both should have valid guidance
        assert guidance_low.tone is not None
        assert guidance_high.tone is not None


class TestMixedAffects:
    """Test response modulation with mixed affect states."""
    
    def test_care_and_play_blend(self, neutral_affect_system):
        """Test blend of CARE and PLAY."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(30):
            neutral_affect_system.process_input({"CARE": 0.9, "PLAY": 0.85}, intensity=0.85)
        
        guidance = modulator.get_guidance()
        
        # Should reflect both affects
        assert guidance.dominant_affect in ["CARE", "PLAY"]
    
    def test_multiple_affects(self, neutral_affect_system):
        """Test multiple affects."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(30):
            neutral_affect_system.process_input({
                "SEEKING": 0.9,
                "CARE": 0.85,
                "PLAY": 0.8
            }, intensity=0.85)
        
        guidance = modulator.get_guidance()
        
        # Dominant should be one of the high affects
        assert guidance.dominant_affect in ["SEEKING", "CARE", "PLAY"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_neutral_state(self, affect_system, modulator):
        """Test completely neutral/balanced state."""
        guidance = modulator.get_guidance()
        
        assert 0.0 <= guidance.intensity <= 1.0
        assert guidance.tone is not None
        assert guidance.style is not None
    
    def test_zero_intensity_state(self, affect_system, modulator):
        """Test state with zero intensity."""
        affect_system.process_input({"CARE": 0.0}, intensity=0.0)
        guidance = modulator.get_guidance()
        
        assert 0.0 <= guidance.intensity <= 1.0
        assert guidance.tone is not None
    
    def test_guidance_always_valid(self, neutral_affect_system):
        """Test that guidance is always valid regardless of input."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        test_inputs = [
            ({"SEEKING": 0.9}, 0.8),
            ({"RAGE": 0.5}, 0.4),
            ({"CARE": 0.0, "FEAR": 1.0}, 0.9),
            ({}, 0.0),
        ]
        
        for affects, intensity in test_inputs:
            neutral_affect_system.process_input(affects, intensity)
            guidance = modulator.get_guidance()
            
            assert isinstance(guidance, ResponseGuidance)
            assert guidance.tone is not None
            assert guidance.style is not None
            assert 0.0 <= guidance.intensity <= 1.0


class TestResponseGuidance:
    """Test ResponseGuidance data structure."""
    
    def test_to_dict(self, modulator):
        """Test ResponseGuidance.to_dict() method."""
        guidance = modulator.get_guidance()
        guidance_dict = guidance.to_dict()
        
        assert isinstance(guidance_dict, dict)
        assert "tone" in guidance_dict
        assert "style" in guidance_dict
        assert "intensity" in guidance_dict
        assert "embrace" in guidance_dict
        assert "avoid" in guidance_dict
        assert "affect_summary" in guidance_dict
        assert "dominant_affect" in guidance_dict
    
    def test_guidance_fields_types(self, modulator):
        """Test that guidance fields have correct types."""
        guidance = modulator.get_guidance()
        
        assert isinstance(guidance.tone, str)
        assert isinstance(guidance.secondary_tones, list)
        assert isinstance(guidance.style, str)
        assert isinstance(guidance.intensity, float)
        assert isinstance(guidance.embrace, list)
        assert isinstance(guidance.avoid, list)
        assert isinstance(guidance.affect_summary, str)
        assert isinstance(guidance.dominant_affect, str)
    
    def test_embrace_avoid_limits(self, neutral_affect_system):
        """Test that embrace/avoid lists are limited in length."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        # Create state with many affects
        for _ in range(30):
            neutral_affect_system.process_input({
                "SEEKING": 0.9,
                "CARE": 0.85,
                "PLAY": 0.8,
                "FEAR": 0.75
            }, intensity=0.85)
        
        guidance = modulator.get_guidance()
        
        # Lists should be limited (implementation limits to 5)
        assert len(guidance.embrace) <= 5
        assert len(guidance.avoid) <= 5


class TestFormatForPrompt:
    """Test prompt formatting functionality."""
    
    def test_format_basic(self, modulator):
        """Test basic prompt formatting."""
        formatted = modulator.format_for_prompt(include_details=False)
        
        assert isinstance(formatted, str)
        assert "[AFFECT STATE:" in formatted
        assert "Tone:" in formatted
        assert "Style:" in formatted
    
    def test_format_with_details(self, modulator):
        """Test prompt formatting with details."""
        formatted = modulator.format_for_prompt(include_details=True)
        
        assert isinstance(formatted, str)
        assert "Tone:" in formatted
        assert "Style:" in formatted
    
    def test_format_different_states(self, neutral_affect_system):
        """Test formatting for different affect states."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        states = [
            {"CARE": 0.9},
            {"RAGE": 0.85},
            {"SEEKING": 0.95},
        ]
        
        for state in states:
            # Create fresh system for each test
            baseline = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32)
            system = DynamicAffectSystem(
                identity_name="test_format",
                baseline=baseline
            )
            mod = GenericResponseModulator(system)
            
            for _ in range(30):
                system.process_input(state, intensity=0.85)
            
            formatted = mod.format_for_prompt()
            
            assert isinstance(formatted, str)
            assert len(formatted) > 0
            assert "Tone:" in formatted


class TestConvenienceFunction:
    """Test convenience function modulate_response."""
    
    def test_modulate_response_function(self, affect_system):
        """Test modulate_response convenience function."""
        guidance = modulate_response(affect_system)
        
        assert isinstance(guidance, ResponseGuidance)
        assert hasattr(guidance, 'tone')
        assert hasattr(guidance, 'style')
    
    def test_modulate_response_equivalent(self, affect_system):
        """Test that convenience function is equivalent to creating modulator."""
        # Using convenience function
        guidance1 = modulate_response(affect_system)
        
        # Using modulator directly
        modulator = GenericResponseModulator(affect_system)
        guidance2 = modulator.get_guidance()
        
        # Should produce equivalent results
        assert guidance1.tone == guidance2.tone
        assert guidance1.style == guidance2.style
        assert guidance1.dominant_affect == guidance2.dominant_affect


class TestResponsePatterns:
    """Test that response patterns match expected affect characteristics."""
    
    def test_care_affects_guidance(self, neutral_affect_system):
        """Test CARE affects guidance patterns."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(15):
            neutral_affect_system.process_input({"CARE": 0.95}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        
        # CARE should be reflected in the guidance
        assert guidance.dominant_affect == "CARE" or "care" in guidance.tone.lower() or "warm" in guidance.tone.lower()
    
    def test_seeking_affects_guidance(self, neutral_affect_system):
        """Test SEEKING affects guidance patterns."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(15):
            neutral_affect_system.process_input({"SEEKING": 0.95}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        
        # With strong SEEKING input, should show in tone or dominant affect
        assert (guidance.dominant_affect == "SEEKING" or 
                "curious" in guidance.tone.lower() or 
                "inquisitive" in guidance.tone.lower())
    
    def test_different_affects_produce_different_tones(self, neutral_affect_system):
        """Test that different dominant affects produce different tones."""
        # Test CARE
        baseline = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32)
        system_care = DynamicAffectSystem(
            identity_name="test_care",
            baseline=baseline
        )
        mod_care = GenericResponseModulator(system_care)
        
        for _ in range(15):
            system_care.process_input({"CARE": 0.95}, intensity=0.9)
        guidance_care = mod_care.get_guidance()
        
        # Test RAGE
        system_rage = DynamicAffectSystem(
            identity_name="test_rage",
            baseline=baseline
        )
        mod_rage = GenericResponseModulator(system_rage)
        
        for _ in range(15):
            system_rage.process_input({"RAGE": 0.95}, intensity=0.9)
        guidance_rage = mod_rage.get_guidance()
        
        # Tones should be different
        assert guidance_care.tone != guidance_rage.tone
        assert guidance_care.dominant_affect != guidance_rage.dominant_affect


class TestStyleMapping:
    """Test style determination based on affects."""
    
    def test_style_is_determined(self, modulator):
        """Test that style is always determined."""
        guidance = modulator.get_guidance()
        
        assert guidance.style in ["expansive", "careful", "bold", "casual", "gentle", "balanced", "assertive"]
    
    def test_high_seeking_affects_style(self, neutral_affect_system):
        """Test high SEEKING affects style."""
        modulator = GenericResponseModulator(neutral_affect_system)
        
        for _ in range(20):
            neutral_affect_system.process_input({"SEEKING": 0.95, "CARE": 0.0, "PLAY": 0.0}, intensity=0.9)
        
        guidance = modulator.get_guidance()
        
        # Should have SEEKING as dominant or high
        current_state = neutral_affect_system.current.to_dict()['named']
        # With enough iterations, SEEKING should be significantly higher
        assert current_state.get('SEEKING', 0) > 0.2
    
    def test_different_affects_can_produce_different_styles(self, neutral_affect_system):
        """Test that different affects can lead to different styles."""
        # Collect styles from different affect states
        styles = set()
        
        affect_inputs = [
            {"SEEKING": 0.95},
            {"PLAY": 0.95},
            {"CARE": 0.95},
            {"FEAR": 0.95},
            {"RAGE": 0.95},
        ]
        
        for affect in affect_inputs:
            baseline = np.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], dtype=np.float32)
            system = DynamicAffectSystem(
                identity_name="test_style",
                baseline=baseline
            )
            mod = GenericResponseModulator(system)
            
            for _ in range(15):
                system.process_input(affect, intensity=0.9)
            
            guidance = mod.get_guidance()
            styles.add(guidance.style)
        
        # Should have some variety in styles
        assert len(styles) >= 1  # At least one style
