"""
Tests for personality_profiles module.

Tests PersonalityManager, DEFAULT_PROFILES, and profile management.
"""

import pytest
import json
import tempfile
from pathlib import Path

from nima_core.cognition.personality_profiles import (
    PersonalityManager,
    DEFAULT_PROFILES,
    get_profile,
    list_profiles,
)


# ==============================================================================
# DEFAULT_PROFILES Tests
# ==============================================================================

class TestDefaultProfiles:
    """Test the built-in personality profiles."""
    
    def test_all_builtin_profiles_exist(self):
        """Verify all expected built-in profiles are present."""
        expected = [
            "baseline", "chaos", "guardian", "cold_logic", "rage",
            "mystic", "nihilist", "empath", "manic", "stoic",
            "trickster", "berserker", "poet", "paranoid"
        ]
        for name in expected:
            assert name in DEFAULT_PROFILES, f"Missing profile: {name}"
    
    def test_profile_structure(self):
        """Each profile should have description, emotions, amplifiers, modulator."""
        for name, profile in DEFAULT_PROFILES.items():
            assert "description" in profile, f"{name} missing description"
            assert "emotions" in profile, f"{name} missing emotions"
            assert "amplifiers" in profile, f"{name} missing amplifiers"
            assert "modulator" in profile, f"{name} missing modulator"
            assert isinstance(profile["description"], str)
            assert isinstance(profile["emotions"], dict)
            assert isinstance(profile["amplifiers"], dict)
            assert isinstance(profile["modulator"], dict)
    
    def test_emotion_keys_consistency(self):
        """All profiles should have the same emotion keys."""
        baseline_emotions = set(DEFAULT_PROFILES["baseline"]["emotions"].keys())
        
        for name, profile in DEFAULT_PROFILES.items():
            emotions = set(profile["emotions"].keys())
            assert emotions == baseline_emotions, (
                f"{name} has different emotion keys: {emotions ^ baseline_emotions}"
            )
    
    def test_amplifier_keys_match_emotions(self):
        """Amplifier keys should match emotion keys."""
        for name, profile in DEFAULT_PROFILES.items():
            emotion_keys = set(profile["emotions"].keys())
            amplifier_keys = set(profile["amplifiers"].keys())
            assert emotion_keys == amplifier_keys, (
                f"{name}: emotion keys != amplifier keys"
            )
    
    def test_emotion_values_in_range(self):
        """All emotion values should be between 0.0 and 1.0."""
        for name, profile in DEFAULT_PROFILES.items():
            for emotion, value in profile["emotions"].items():
                assert 0.0 <= value <= 1.0, (
                    f"{name}.emotions.{emotion} = {value}, expected [0.0, 1.0]"
                )
    
    def test_amplifier_values_positive(self):
        """All amplifier values should be positive (0.1x to 5.0x typical range)."""
        for name, profile in DEFAULT_PROFILES.items():
            for emotion, value in profile["amplifiers"].items():
                assert value >= 0.0, (
                    f"{name}.amplifiers.{emotion} = {value}, expected >= 0.0"
                )
                # Most should be in reasonable range, but not enforced strictly
    
    def test_modulator_keys_present(self):
        """Each profile should have expected modulator threshold keys."""
        expected_keys = {
            "daring_threshold",
            "courage_threshold",
            "nurturing_threshold",
            "mastery_threshold",
            "activation_threshold"
        }
        
        for name, profile in DEFAULT_PROFILES.items():
            modulator_keys = set(profile["modulator"].keys())
            assert expected_keys == modulator_keys, (
                f"{name} modulator missing/extra keys: {expected_keys ^ modulator_keys}"
            )
    
    def test_modulator_values_in_range(self):
        """Modulator threshold values should be between 0.0 and 1.0."""
        for name, profile in DEFAULT_PROFILES.items():
            for key, value in profile["modulator"].items():
                assert 0.0 <= value <= 1.0, (
                    f"{name}.modulator.{key} = {value}, expected [0.0, 1.0]"
                )


class TestSpecificProfiles:
    """Test specific profile characteristics."""
    
    def test_guardian_profile(self):
        """Guardian should be protective with high fear/care."""
        guardian = DEFAULT_PROFILES["guardian"]
        assert guardian["emotions"]["fear"] >= 0.8
        assert guardian["emotions"]["love"] >= 0.8
        assert guardian["emotions"]["trust"] >= 0.8
        assert guardian["amplifiers"]["fear"] >= 2.0
    
    def test_chaos_profile(self):
        """Chaos should have high joy/surprise, low fear/trust."""
        chaos = DEFAULT_PROFILES["chaos"]
        assert chaos["emotions"]["joy"] >= 0.9
        assert chaos["emotions"]["surprise"] >= 0.9
        assert chaos["emotions"]["fear"] <= 0.1
        assert chaos["emotions"]["sadness"] <= 0.1
    
    def test_cold_logic_profile(self):
        """Cold logic should minimize emotions, maximize curiosity."""
        logic = DEFAULT_PROFILES["cold_logic"]
        assert logic["emotions"]["curiosity"] >= 0.5
        assert logic["emotions"]["joy"] <= 0.1
        assert logic["emotions"]["love"] <= 0.1
        assert logic["emotions"]["anger"] <= 0.1
    
    def test_empath_profile(self):
        """Empath should have high sensitivity to all emotions."""
        empath = DEFAULT_PROFILES["empath"]
        # All emotions should be at maximum sensitivity
        for value in empath["emotions"].values():
            assert value == 1.0
        # All amplifiers should be high
        for value in empath["amplifiers"].values():
            assert value >= 2.0
    
    def test_stoic_profile(self):
        """Stoic should have measured, low emotional responses."""
        stoic = DEFAULT_PROFILES["stoic"]
        assert stoic["emotions"]["pride"] >= 0.5
        assert stoic["emotions"]["joy"] <= 0.3
        assert stoic["emotions"]["anger"] <= 0.2
        assert stoic["emotions"]["fear"] <= 0.2


# ==============================================================================
# Module-level Functions Tests
# ==============================================================================

class TestModuleFunctions:
    """Test get_profile() and list_profiles() functions."""
    
    def test_get_profile_valid(self):
        """get_profile() should return correct profile dict."""
        guardian = get_profile("guardian")
        assert guardian is not None
        assert guardian["description"] == "Hyper-protective - anxious, mothering, boundary-focused"
        assert "emotions" in guardian
    
    def test_get_profile_invalid(self):
        """get_profile() should return None for unknown profile."""
        result = get_profile("nonexistent_profile_xyz")
        assert result is None
    
    def test_list_profiles_returns_all(self):
        """list_profiles() should return all DEFAULT_PROFILES keys."""
        profiles = list_profiles()
        expected = list(DEFAULT_PROFILES.keys())
        assert set(profiles) == set(expected)
    
    def test_list_profiles_returns_list(self):
        """list_profiles() should return a list."""
        profiles = list_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) > 0


# ==============================================================================
# PersonalityManager Tests
# ==============================================================================

class TestPersonalityManager:
    """Test PersonalityManager class."""
    
    def test_initialization_default_storage(self):
        """Manager should initialize with default storage location."""
        mgr = PersonalityManager()
        assert mgr.storage_dir == Path.home() / ".nima" / "personality"
        assert mgr.current_profile_name == "baseline"
        assert len(mgr.profiles) >= len(DEFAULT_PROFILES)
    
    def test_initialization_custom_storage(self, tmp_path):
        """Manager should accept custom storage directory."""
        storage = tmp_path / "custom_profiles"
        mgr = PersonalityManager(storage_dir=storage)
        assert mgr.storage_dir == storage
        assert storage.exists()
    
    def test_get_current_profile_default(self, tmp_path):
        """Should return baseline profile by default."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        profile = mgr.get_current_profile()
        assert profile == DEFAULT_PROFILES["baseline"]
    
    def test_get_profile_valid(self, tmp_path):
        """get_profile() should return requested profile."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        guardian = mgr.get_profile("guardian")
        assert guardian is not None
        assert guardian == DEFAULT_PROFILES["guardian"]
    
    def test_get_profile_invalid(self, tmp_path):
        """get_profile() should return None for unknown profile."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        result = mgr.get_profile("nonexistent_xyz")
        assert result is None
    
    def test_set_profile_valid(self, tmp_path):
        """set_profile() should switch active profile."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        result = mgr.set_profile("chaos")
        assert result is True
        assert mgr.current_profile_name == "chaos"
        assert mgr.get_current_profile() == DEFAULT_PROFILES["chaos"]
    
    def test_set_profile_invalid(self, tmp_path):
        """set_profile() should fail gracefully for unknown profile."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        result = mgr.set_profile("nonexistent_xyz")
        assert result is False
        assert mgr.current_profile_name == "baseline"  # Should not change
    
    def test_list_profiles(self, tmp_path):
        """list_profiles() should return name -> description mapping."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        profiles = mgr.list_profiles()
        assert isinstance(profiles, dict)
        assert "guardian" in profiles
        assert "chaos" in profiles
        assert profiles["guardian"] == "Hyper-protective - anxious, mothering, boundary-focused"
    
    def test_create_profile(self, tmp_path):
        """create_profile() should add new custom profile."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        custom_emotions = {
            "joy": 0.8,
            "trust": 0.7,
            "fear": 0.2
        }
        
        mgr.create_profile("custom_test", custom_emotions, "Test profile")
        
        assert "custom_test" in mgr.profiles
        profile = mgr.get_profile("custom_test")
        assert profile is not None
        assert profile["description"] == "Test profile"
        assert profile["emotions"]["joy"] == 0.8
        assert profile["emotions"]["trust"] == 0.7
        # Should inherit baseline structure for other fields
        assert "amplifiers" in profile
        assert "modulator" in profile
    
    def test_persistence_save_and_load(self, tmp_path):
        """State should persist across instances."""
        storage = tmp_path / "persist_test"
        
        # Create and configure
        mgr1 = PersonalityManager(storage_dir=storage)
        mgr1.set_profile("trickster")
        mgr1.create_profile("test_persist", {"joy": 0.5}, "Persistence test")
        
        # Reload from same directory
        mgr2 = PersonalityManager(storage_dir=storage)
        assert mgr2.current_profile_name == "trickster"
        assert "test_persist" in mgr2.profiles
        assert mgr2.get_profile("test_persist")["description"] == "Persistence test"
    
    def test_state_file_json_structure(self, tmp_path):
        """Saved state file should have expected JSON structure."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        mgr.set_profile("mystic")
        mgr.create_profile("custom", {"joy": 0.9}, "Custom")
        
        state_file = tmp_path / "current_personality.json"
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            data = json.load(f)
        
        assert "current" in data
        assert data["current"] == "mystic"
        assert "custom_profiles" in data
        assert "custom" in data["custom_profiles"]
    
    def test_thread_safety_set_profile(self, tmp_path):
        """set_profile should be thread-safe (basic check)."""
        import threading
        
        mgr = PersonalityManager(storage_dir=tmp_path)
        profiles_to_set = ["chaos", "guardian", "mystic", "stoic"]
        
        def switch_profile(profile_name):
            for _ in range(10):
                mgr.set_profile(profile_name)
        
        threads = [
            threading.Thread(target=switch_profile, args=(p,))
            for p in profiles_to_set
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should end in a valid state (one of the profiles)
        assert mgr.current_profile_name in profiles_to_set


# ==============================================================================
# Edge Cases Tests
# ==============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_storage_directory(self, tmp_path):
        """Should handle empty storage directory gracefully."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        assert mgr.current_profile_name == "baseline"
        assert len(mgr.profiles) >= len(DEFAULT_PROFILES)
    
    def test_corrupted_state_file(self, tmp_path):
        """Should handle corrupted state file gracefully."""
        state_file = tmp_path / "current_personality.json"
        tmp_path.mkdir(parents=True, exist_ok=True)
        
        # Write invalid JSON
        with open(state_file, "w") as f:
            f.write("{ invalid json }")
        
        # Should fall back to defaults
        mgr = PersonalityManager(storage_dir=tmp_path)
        assert mgr.current_profile_name == "baseline"
    
    def test_profile_name_case_sensitivity(self, tmp_path):
        """Profile names should be case-sensitive."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        
        # Lowercase exists
        assert mgr.set_profile("guardian") is True
        
        # Uppercase should fail
        assert mgr.set_profile("Guardian") is False
        assert mgr.set_profile("GUARDIAN") is False
    
    def test_create_profile_overwrites_existing(self, tmp_path):
        """Creating a profile with existing name should overwrite."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        
        mgr.create_profile("test", {"joy": 0.5}, "First")
        first = mgr.get_profile("test")
        
        mgr.create_profile("test", {"joy": 0.9}, "Second")
        second = mgr.get_profile("test")
        
        assert first != second
        assert second["description"] == "Second"
        assert second["emotions"]["joy"] == 0.9
    
    def test_create_profile_ignores_unknown_emotions(self, tmp_path):
        """create_profile should ignore unknown emotion keys."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        
        emotions_with_unknown = {
            "joy": 0.8,
            "unknown_emotion_xyz": 0.5,  # Should be ignored
            "trust": 0.7
        }
        
        mgr.create_profile("test_unknown", emotions_with_unknown, "Test")
        profile = mgr.get_profile("test_unknown")
        
        assert profile["emotions"]["joy"] == 0.8
        assert profile["emotions"]["trust"] == 0.7
        assert "unknown_emotion_xyz" not in profile["emotions"]
    
    def test_profile_reference_behavior(self, tmp_path):
        """get_profile() returns direct reference, not a copy."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        
        profile1 = mgr.get_profile("baseline")
        original_joy = profile1["emotions"]["joy"]
        
        # Modify returned dict
        profile1["emotions"]["joy"] = 0.999
        
        # Get same reference again
        profile2 = mgr.get_profile("baseline")
        
        # Modifications affect stored profile (direct reference)
        assert profile2["emotions"]["joy"] == 0.999
        assert profile2 is profile1  # Same object
        
        # Reset for other tests
        profile1["emotions"]["joy"] = original_joy


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests combining multiple features."""
    
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: create, switch, persist, reload."""
        storage = tmp_path / "workflow"
        
        # Step 1: Create manager and custom profile
        mgr1 = PersonalityManager(storage_dir=storage)
        mgr1.create_profile("workflow_test", {"joy": 0.95}, "Workflow test profile")
        mgr1.set_profile("workflow_test")
        
        # Step 2: Verify state
        assert mgr1.current_profile_name == "workflow_test"
        assert mgr1.get_current_profile()["emotions"]["joy"] == 0.95
        
        # Step 3: Reload and verify persistence
        mgr2 = PersonalityManager(storage_dir=storage)
        assert mgr2.current_profile_name == "workflow_test"
        assert "workflow_test" in mgr2.profiles
        
        # Step 4: Switch to built-in profile
        mgr2.set_profile("guardian")
        assert mgr2.get_current_profile() == DEFAULT_PROFILES["guardian"]
        
        # Step 5: Verify persistence again
        mgr3 = PersonalityManager(storage_dir=storage)
        assert mgr3.current_profile_name == "guardian"
        assert "workflow_test" in mgr3.profiles  # Custom profile still there
    
    def test_all_profiles_switchable(self, tmp_path):
        """All built-in profiles should be switchable."""
        mgr = PersonalityManager(storage_dir=tmp_path)
        
        for profile_name in DEFAULT_PROFILES.keys():
            result = mgr.set_profile(profile_name)
            assert result is True, f"Failed to switch to {profile_name}"
            assert mgr.current_profile_name == profile_name
            assert mgr.get_current_profile() == DEFAULT_PROFILES[profile_name]
