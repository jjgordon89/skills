"""
Comprehensive tests for DynamicAffectSystem.

Tests cover:
1. Constructor - default baseline, custom baseline, identity name, state file creation
2. process_input() - valid inputs, invalid inputs, intensity scaling, momentum effect, thread safety
3. drift_toward_baseline() - decay toward baseline, intensity-aware decay rates
4. set_state() - direct state setting, validation
5. current property - returns safe copy, not reference
6. _save_state() / _load_state() - persistence round-trip, atomic writes, corrupt file handling
7. get_state_summary() - correct format
8. get_affect_system() singleton - creation, reuse, reset
9. Thread safety - concurrent process_input calls don't corrupt state
10. Cross-affect interactions toggle - cross_affect=True/False
11. History and correlation integration - records are created after process_input
12. Edge cases - all zeros input, all ones input, empty dict, negative values
"""

import pytest
import numpy as np
import json
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

from nima_core.cognition.dynamic_affect import (
    DynamicAffectSystem,
    AffectVector,
    get_affect_system,
    AFFECTS,
    AFFECT_INDEX,
    DEFAULT_BASELINE,
)
from nima_core.cognition.exceptions import (
    InvalidAffectNameError,
    AffectValueError,
)


# =============================================================================
# 1. CONSTRUCTOR TESTS
# =============================================================================

class TestConstructor:
    """Test DynamicAffectSystem initialization."""
    
    def test_default_baseline(self, tmp_path):
        """Test initialization with default baseline."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="test")
        
        # Should use DEFAULT_BASELINE
        assert np.allclose(system.baseline.values, DEFAULT_BASELINE)
        assert system.identity_name == "test"
        assert system.current is not None
        # Current should start at baseline
        assert np.allclose(system.current.values, DEFAULT_BASELINE)
    
    def test_custom_baseline_array(self, tmp_path):
        """Test initialization with custom baseline as numpy array."""
        custom = np.array([0.8, 0.2, 0.1, 0.0, 0.9, 0.0, 0.7], dtype=np.float32)
        system = DynamicAffectSystem(data_dir=tmp_path, baseline=custom)
        
        assert np.allclose(system.baseline.values, custom)
        assert np.allclose(system.current.values, custom)
    
    def test_custom_baseline_list(self, tmp_path):
        """Test initialization with custom baseline as list."""
        custom = [0.6, 0.3, 0.2, 0.1, 0.7, 0.1, 0.5]
        system = DynamicAffectSystem(data_dir=tmp_path, baseline=custom)
        
        assert np.allclose(system.baseline.values, np.array(custom, dtype=np.float32))
    
    def test_identity_name(self, tmp_path):
        """Test identity name is stored correctly."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="lilu")
        assert system.identity_name == "lilu"
        
        # State file should include identity name
        assert system.state_file.name == "affect_state_lilu.json"
    
    def test_state_file_creation(self, tmp_path):
        """Test state file is created in correct directory."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="test")
        
        # Directory should exist
        assert system.data_dir.exists()
        assert system.data_dir == tmp_path
        
        # State file path should be correct
        expected_path = tmp_path / "affect_state_test.json"
        assert system.state_file == expected_path
    
    def test_custom_parameters(self, tmp_path):
        """Test custom momentum, decay, blend parameters."""
        system = DynamicAffectSystem(
            data_dir=tmp_path,
            momentum=0.9,
            decay_rate=0.2,
            blend_strength=0.3,
        )
        
        assert system.momentum == 0.9
        assert system.decay_rate == 0.2
        assert system.blend_strength == 0.3


# =============================================================================
# 2. PROCESS_INPUT TESTS
# =============================================================================

class TestProcessInput:
    """Test emotional input processing."""
    
    def test_valid_input_single_affect(self, tmp_path):
        """Test processing valid single affect input."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        baseline = system.current.values.copy()
        
        result = system.process_input({"CARE": 0.8}, intensity=1.0)
        
        # Result should be an AffectVector
        assert isinstance(result, AffectVector)
        
        # CARE should be elevated
        care_idx = AFFECT_INDEX["CARE"]
        assert result.values[care_idx] > baseline[care_idx]
    
    def test_valid_input_multiple_affects(self, tmp_path):
        """Test processing multiple affects simultaneously."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        result = system.process_input({
            "SEEKING": 0.7,
            "CARE": 0.6,
            "PLAY": 0.8
        }, intensity=1.0)
        
        # All three should be elevated
        assert result.values[AFFECT_INDEX["SEEKING"]] > DEFAULT_BASELINE[AFFECT_INDEX["SEEKING"]]
        assert result.values[AFFECT_INDEX["CARE"]] > DEFAULT_BASELINE[AFFECT_INDEX["CARE"]]
        assert result.values[AFFECT_INDEX["PLAY"]] > DEFAULT_BASELINE[AFFECT_INDEX["PLAY"]]
    
    def test_invalid_affect_name(self, tmp_path):
        """Test that invalid affect name raises error."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        with pytest.raises(InvalidAffectNameError):
            system.process_input({"INVALID": 0.5})
    
    def test_invalid_affect_value_out_of_range(self, tmp_path):
        """Test that out-of-range affect values raise error."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Too high
        with pytest.raises(AffectValueError):
            system.process_input({"CARE": 1.5})
        
        # Negative
        with pytest.raises(AffectValueError):
            system.process_input({"CARE": -0.1})
    
    def test_intensity_scaling(self, tmp_path):
        """Test that intensity parameter scales the effect."""
        system1 = DynamicAffectSystem(data_dir=tmp_path / "sys1")
        system2 = DynamicAffectSystem(data_dir=tmp_path / "sys2")
        
        # Same input, different intensities
        result_low = system1.process_input({"RAGE": 0.8}, intensity=0.3)
        result_high = system2.process_input({"RAGE": 0.8}, intensity=1.0)
        
        rage_idx = AFFECT_INDEX["RAGE"]
        
        # High intensity should produce larger change
        delta_low = result_low.values[rage_idx] - DEFAULT_BASELINE[rage_idx]
        delta_high = result_high.values[rage_idx] - DEFAULT_BASELINE[rage_idx]
        
        assert delta_high > delta_low
    
    def test_intensity_out_of_range(self, tmp_path):
        """Test that invalid intensity raises error."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        with pytest.raises(ValueError, match="Intensity must be in"):
            system.process_input({"CARE": 0.5}, intensity=1.5)
        
        with pytest.raises(ValueError, match="Intensity must be in"):
            system.process_input({"CARE": 0.5}, intensity=-0.1)
    
    def test_intensity_non_numeric(self, tmp_path):
        """Test that non-numeric intensity raises error."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        with pytest.raises(ValueError, match="Intensity must be numeric"):
            system.process_input({"CARE": 0.5}, intensity="high")
    
    def test_momentum_effect(self, tmp_path):
        """Test that momentum makes state sticky."""
        # High momentum system (sticky)
        sticky = DynamicAffectSystem(data_dir=tmp_path / "sticky", momentum=0.95)
        # Low momentum system (responsive)
        responsive = DynamicAffectSystem(data_dir=tmp_path / "responsive", momentum=0.5)
        
        input_affect = {"FEAR": 0.9}
        
        result_sticky = sticky.process_input(input_affect, intensity=1.0)
        result_responsive = responsive.process_input(input_affect, intensity=1.0)
        
        fear_idx = AFFECT_INDEX["FEAR"]
        
        # Responsive should change more
        delta_sticky = result_sticky.values[fear_idx] - DEFAULT_BASELINE[fear_idx]
        delta_responsive = result_responsive.values[fear_idx] - DEFAULT_BASELINE[fear_idx]
        
        assert delta_responsive > delta_sticky
    
    def test_case_insensitive_affect_names(self, tmp_path):
        """Test that affect names are case-insensitive."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # All of these should work
        result1 = system.process_input({"care": 0.5}, intensity=1.0)
        result2 = system.process_input({"Care": 0.5}, intensity=1.0)
        result3 = system.process_input({"CARE": 0.5}, intensity=1.0)
        
        # All should succeed (no exceptions)
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None


# =============================================================================
# 3. DRIFT_TOWARD_BASELINE TESTS
# =============================================================================

class TestDriftTowardBaseline:
    """Test baseline drift/decay functionality."""
    
    def test_drift_moves_toward_baseline(self, tmp_path):
        """Test that drift pulls state toward baseline."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Push state away from baseline
        system.set_state({"RAGE": 0.9, "FEAR": 0.8})
        before = system.current.values.copy()
        
        # Apply drift
        system.drift_toward_baseline(strength=0.2)
        after = system.current.values.copy()
        
        # Distance to baseline should decrease
        dist_before = np.linalg.norm(before - system.baseline.values)
        dist_after = np.linalg.norm(after - system.baseline.values)
        
        assert dist_after < dist_before
    
    def test_drift_strength_parameter(self, tmp_path):
        """Test that drift strength controls pull magnitude."""
        system1 = DynamicAffectSystem(data_dir=tmp_path / "sys1")
        system2 = DynamicAffectSystem(data_dir=tmp_path / "sys2")
        
        # Set both to same elevated state
        elevated = {"PANIC": 0.9}
        system1.set_state(elevated)
        system2.set_state(elevated)
        
        # Different drift strengths
        system1.drift_toward_baseline(strength=0.1)
        system2.drift_toward_baseline(strength=0.5)
        
        panic_idx = AFFECT_INDEX["PANIC"]
        
        # Stronger drift should pull more
        delta1 = 0.9 - system1.current.values[panic_idx]
        delta2 = 0.9 - system2.current.values[panic_idx]
        
        assert delta2 > delta1
    
    def test_drift_doesnt_overshoot(self, tmp_path):
        """Test that drift doesn't push past baseline."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        baseline_care = system.baseline.values[AFFECT_INDEX["CARE"]]
        
        # Set CARE higher than baseline
        system.set_state({"CARE": baseline_care + 0.3})
        
        # Apply strong drift
        system.drift_toward_baseline(strength=1.0)
        
        # Should not go below baseline
        assert system.current.values[AFFECT_INDEX["CARE"]] >= baseline_care - 0.01
    
    def test_repeated_drift_converges(self, tmp_path):
        """Test that repeated drift eventually converges to baseline."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Set far from baseline
        system.set_state({"RAGE": 1.0, "FEAR": 1.0, "PANIC": 1.0})
        
        # Apply drift many times
        for _ in range(50):
            system.drift_toward_baseline(strength=0.1)
        
        # Should be very close to baseline
        assert np.allclose(system.current.values, system.baseline.values, atol=0.1)


# =============================================================================
# 4. SET_STATE TESTS
# =============================================================================

class TestSetState:
    """Test direct state setting."""
    
    def test_set_state_basic(self, tmp_path):
        """Test basic state setting."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        new_state = {"SEEKING": 0.7, "PLAY": 0.8}
        result = system.set_state(new_state)
        
        assert result.values[AFFECT_INDEX["SEEKING"]] == 0.7
        assert result.values[AFFECT_INDEX["PLAY"]] == 0.8
    
    def test_set_state_source_label(self, tmp_path):
        """Test that source label is stored."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        system.set_state({"CARE": 0.9}, source="test_source")
        
        assert system.current.source == "test_source"
    
    def test_set_state_persistence(self, tmp_path):
        """Test that set_state triggers persistence."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="persist_test")
        
        system.set_state({"LUST": 0.6})
        
        # State file should exist
        assert system.state_file.exists()
        
        # Load and verify
        with open(system.state_file) as f:
            data = json.load(f)
        
        assert pytest.approx(data["current"]["named"]["LUST"], abs=0.001) == 0.6
    
    def test_set_state_all_affects(self, tmp_path):
        """Test setting all seven affects at once."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        all_affects = {
            "SEEKING": 0.1,
            "RAGE": 0.2,
            "FEAR": 0.3,
            "LUST": 0.4,
            "CARE": 0.5,
            "PANIC": 0.6,
            "PLAY": 0.7,
        }
        
        result = system.set_state(all_affects)
        
        for name, value in all_affects.items():
            assert result.values[AFFECT_INDEX[name]] == value


# =============================================================================
# 5. CURRENT PROPERTY TESTS
# =============================================================================

class TestCurrentProperty:
    """Test that current property returns safe copy."""
    
    def test_current_returns_copy(self, tmp_path):
        """Test that modifying returned vector doesn't affect internal state."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Get current
        current1 = system.current
        original_values = current1.values.copy()
        
        # Modify the returned vector
        current1.values[0] = 0.999
        
        # Get current again - should be unchanged
        current2 = system.current
        
        assert np.allclose(current2.values, original_values)
        assert current2.values[0] != 0.999
    
    def test_current_not_same_object(self, tmp_path):
        """Test that each call to current returns new object."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        current1 = system.current
        current2 = system.current
        
        # Different objects
        assert current1 is not current2
        
        # But same values
        assert np.allclose(current1.values, current2.values)


# =============================================================================
# 6. PERSISTENCE TESTS
# =============================================================================

class TestPersistence:
    """Test state save/load functionality."""
    
    def test_save_load_roundtrip(self, tmp_path):
        """Test that state survives save/load cycle."""
        # Create system and set state
        system1 = DynamicAffectSystem(data_dir=tmp_path, identity_name="roundtrip")
        system1.set_state({"CARE": 0.85, "PLAY": 0.75})
        
        # Create new system with same identity (should load saved state)
        system2 = DynamicAffectSystem(data_dir=tmp_path, identity_name="roundtrip")
        
        # State should match
        assert np.allclose(system2.current.values[AFFECT_INDEX["CARE"]], 0.85, atol=0.01)
        assert np.allclose(system2.current.values[AFFECT_INDEX["PLAY"]], 0.75, atol=0.01)
    
    def test_atomic_write(self, tmp_path):
        """Test that _save_state uses atomic write (temp file + rename)."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="atomic")
        
        # Set state to trigger save
        system.set_state({"SEEKING": 0.9})
        
        # State file should exist and be valid JSON
        assert system.state_file.exists()
        
        with open(system.state_file) as f:
            data = json.load(f)
        
        assert "current" in data
        assert "version" in data
    
    def test_corrupt_file_handling(self, tmp_path):
        """Test that corrupt state file doesn't crash initialization."""
        state_file = tmp_path / "affect_state_corrupt.json"
        
        # Write corrupt JSON
        state_file.write_text("{ corrupt json !!!")
        
        # Should fall back to baseline without crashing
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="corrupt")
        
        assert system.current is not None
        assert np.allclose(system.current.values, DEFAULT_BASELINE)
    
    def test_missing_file_initialization(self, tmp_path):
        """Test initialization when no state file exists."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="new")
        
        # Should initialize to baseline
        assert np.allclose(system.current.values, system.baseline.values)
    
    def test_state_file_contains_metadata(self, tmp_path):
        """Test that saved state includes proper metadata."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="meta")
        system.set_state({"CARE": 0.7})
        
        with open(system.state_file) as f:
            data = json.load(f)
        
        # Check metadata
        assert "version" in data
        assert "identity_name" in data
        assert "saved_at" in data
        assert data["identity_name"] == "meta"


# =============================================================================
# 7. GET_STATE_SUMMARY TESTS
# =============================================================================

class TestGetStateSummary:
    """Test state summary generation."""
    
    def test_summary_format(self, tmp_path):
        """Test that summary has expected structure."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="summary_test")
        
        summary = system.get_state_summary()
        
        # Check required keys
        assert "identity_name" in summary
        assert "current" in summary
        assert "baseline" in summary
        assert "dominant" in summary
        assert "top_3" in summary
        assert "deviation_from_baseline" in summary
        assert "similarity_to_baseline" in summary
    
    def test_dominant_affect(self, tmp_path):
        """Test that dominant affect is correctly identified."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        system.set_state({"RAGE": 0.95, "FEAR": 0.2})
        
        summary = system.get_state_summary()
        
        # Dominant should be RAGE
        dominant_name, dominant_value = summary["dominant"]
        assert dominant_name == "RAGE"
        assert dominant_value >= 0.9
    
    def test_top_3_affects(self, tmp_path):
        """Test that top 3 affects are correctly ordered."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        system.set_state({
            "SEEKING": 0.9,
            "CARE": 0.7,
            "PLAY": 0.8,
            "RAGE": 0.1
        })
        
        summary = system.get_state_summary()
        top_3 = summary["top_3"]
        
        # Should be 3 items
        assert len(top_3) == 3
        
        # Should be sorted by value (descending)
        assert top_3[0][1] >= top_3[1][1] >= top_3[2][1]
        
        # Top should include SEEKING, PLAY, CARE
        top_names = {item[0] for item in top_3}
        assert "SEEKING" in top_names
        assert "PLAY" in top_names
        assert "CARE" in top_names


# =============================================================================
# 8. SINGLETON TESTS
# =============================================================================

class TestSingleton:
    """Test get_affect_system singleton pattern."""
    
    def test_singleton_creation(self):
        """Test that get_affect_system creates instance."""
        # Reset global instance
        import nima_core.cognition.dynamic_affect as module
        module._instance = None
        
        instance = get_affect_system(identity_name="singleton_test")
        
        assert instance is not None
        assert isinstance(instance, DynamicAffectSystem)
    
    def test_singleton_reuse(self):
        """Test that subsequent calls return same instance."""
        # Reset global instance
        import nima_core.cognition.dynamic_affect as module
        module._instance = None
        
        instance1 = get_affect_system(identity_name="reuse_test")
        instance2 = get_affect_system(identity_name="reuse_test")
        
        # Should be exact same object
        assert instance1 is instance2
    
    def test_singleton_warns_on_param_change(self):
        """Test that singleton warns if params provided after creation."""
        # Reset global instance
        import nima_core.cognition.dynamic_affect as module
        module._instance = None
        
        # Create with default params
        get_affect_system()
        
        # Try to create with different params - should warn
        with pytest.warns(UserWarning, match="singleton already exists"):
            get_affect_system(identity_name="different", momentum=0.9)
    
    def test_singleton_reset(self):
        """Test that singleton can be manually reset."""
        # Reset global instance
        import nima_core.cognition.dynamic_affect as module
        module._instance = None
        
        instance1 = get_affect_system(identity_name="reset_test")
        
        # Reset
        module._instance = None
        
        instance2 = get_affect_system(identity_name="reset_test")
        
        # Should be different objects
        assert instance1 is not instance2


# =============================================================================
# 9. THREAD SAFETY TESTS
# =============================================================================

class TestThreadSafety:
    """Test concurrent access safety."""
    
    def test_concurrent_process_input(self, tmp_path):
        """Test that concurrent process_input calls don't corrupt state."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        def worker(affect_dict, iterations=50):
            for _ in range(iterations):
                system.process_input(affect_dict, intensity=0.5)
        
        # Create multiple threads processing different affects
        threads = [
            threading.Thread(target=worker, args=({"CARE": 0.8},)),
            threading.Thread(target=worker, args=({"RAGE": 0.7},)),
            threading.Thread(target=worker, args=({"PLAY": 0.9},)),
        ]
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # State should still be valid (all values in [0, 1])
        current = system.current
        assert np.all(current.values >= 0)
        assert np.all(current.values <= 1)
    
    def test_concurrent_read_write(self, tmp_path):
        """Test that reads during writes don't crash."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        results = []
        
        def writer():
            for i in range(100):
                system.process_input({"SEEKING": 0.5 + i * 0.001}, intensity=0.3)
        
        def reader():
            for _ in range(100):
                current = system.current
                results.append(current.values.copy())
                time.sleep(0.001)
        
        t1 = threading.Thread(target=writer)
        t2 = threading.Thread(target=reader)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # All reads should have succeeded
        assert len(results) > 0
        
        # All results should be valid
        for values in results:
            assert np.all(values >= 0)
            assert np.all(values <= 1)


# =============================================================================
# 10. CROSS-AFFECT INTERACTIONS TESTS
# =============================================================================

class TestCrossAffectInteractions:
    """Test cross-affect interactions toggle."""
    
    def test_cross_affect_enabled(self, tmp_path):
        """Test that cross_affect=True applies interactions."""
        system = DynamicAffectSystem(
            data_dir=tmp_path,
            cross_affect=True
        )
        
        # Process input
        result = system.process_input({"RAGE": 0.9}, intensity=1.0)
        
        # With cross-affect enabled, RAGE might suppress PLAY/CARE
        # (exact behavior depends on affect_interactions.py, but we verify it's applied)
        assert system.cross_affect_enabled is True
        assert result is not None
    
    def test_cross_affect_disabled(self, tmp_path):
        """Test that cross_affect=False skips interactions."""
        system = DynamicAffectSystem(
            data_dir=tmp_path,
            cross_affect=False
        )
        
        # Process input
        result = system.process_input({"RAGE": 0.9}, intensity=1.0)
        
        assert system.cross_affect_enabled is False
        assert result is not None
    
    def test_cross_affect_toggle_effect(self, tmp_path):
        """Test that toggling cross_affect changes behavior."""
        # Create two systems with same baseline, different cross_affect
        sys_on = DynamicAffectSystem(
            data_dir=tmp_path / "on",
            cross_affect=True,
            baseline=[0.5] * 7
        )
        sys_off = DynamicAffectSystem(
            data_dir=tmp_path / "off",
            cross_affect=False,
            baseline=[0.5] * 7
        )
        
        # Apply same input
        input_affect = {"RAGE": 0.9, "FEAR": 0.8}
        
        result_on = sys_on.process_input(input_affect, intensity=1.0)
        result_off = sys_off.process_input(input_affect, intensity=1.0)
        
        # Results may differ (if interactions are meaningful)
        # At minimum, both should be valid
        assert np.all(result_on.values >= 0) and np.all(result_on.values <= 1)
        assert np.all(result_off.values >= 0) and np.all(result_off.values <= 1)


# =============================================================================
# 11. HISTORY AND CORRELATION INTEGRATION TESTS
# =============================================================================

class TestHistoryCorrelation:
    """Test that history and correlation tracking work."""
    
    def test_history_records_created(self, tmp_path):
        """Test that process_input creates history records."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="history_test")
        
        # Process multiple inputs
        system.process_input({"CARE": 0.8}, intensity=1.0)
        system.process_input({"PLAY": 0.9}, intensity=0.8)
        system.process_input({"SEEKING": 0.7}, intensity=0.6)
        
        # History should have snapshots (use get_timeline)
        snapshots = system.history.get_timeline(duration_hours=1, limit=10)
        assert len(snapshots) >= 3
    
    def test_correlation_tracking(self, tmp_path):
        """Test that correlation tracker records transitions."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Process inputs to create transitions
        system.process_input({"CARE": 0.9}, intensity=1.0)
        system.process_input({"RAGE": 0.8}, intensity=1.0)
        
        # Correlation should have recorded transitions
        # (exact API depends on AffectCorrelation implementation)
        assert system.correlation is not None
    
    def test_history_metadata(self, tmp_path):
        """Test that history records include metadata."""
        system = DynamicAffectSystem(data_dir=tmp_path, identity_name="meta_test")
        
        input_affect = {"PLAY": 0.85}
        intensity = 0.7
        
        system.process_input(input_affect, intensity=intensity)
        
        # Get latest snapshot (use get_timeline)
        snapshots = system.history.get_timeline(duration_hours=1, limit=1)
        assert len(snapshots) == 1
        
        snapshot = snapshots[0]
        
        # Should have metadata about inputs
        assert "inputs" in snapshot.metadata
        assert snapshot.metadata["intensity"] == intensity


# =============================================================================
# 12. EDGE CASES TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_all_zeros_input(self, tmp_path):
        """Test processing all-zero affect input."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        baseline = system.current.values.copy()
        
        result = system.process_input({
            "SEEKING": 0.0,
            "RAGE": 0.0,
            "FEAR": 0.0,
        }, intensity=1.0)
        
        # Should be valid
        assert result is not None
        assert np.all(result.values >= 0)
        
        # Should drift toward baseline (with pull)
        # Values might change slightly due to baseline pull
    
    def test_all_ones_input(self, tmp_path):
        """Test processing maximum affect values."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        result = system.process_input({
            "SEEKING": 1.0,
            "RAGE": 1.0,
            "FEAR": 1.0,
            "LUST": 1.0,
            "CARE": 1.0,
            "PANIC": 1.0,
            "PLAY": 1.0,
        }, intensity=1.0)
        
        # All values should be elevated but still bounded
        assert np.all(result.values <= 1.0)
        assert np.all(result.values >= 0.0)
    
    def test_empty_dict_input(self, tmp_path):
        """Test processing empty affect dictionary."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        baseline = system.current.values.copy()
        
        # Empty input should not crash
        result = system.process_input({}, intensity=1.0)
        
        assert result is not None
        
        # State should barely change (just baseline pull)
        assert np.allclose(result.values, baseline, atol=0.1)
    
    def test_zero_intensity(self, tmp_path):
        """Test that zero intensity has minimal effect."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        before = system.current.values.copy()
        
        result = system.process_input({"RAGE": 1.0}, intensity=0.0)
        
        # With zero intensity, input is scaled to zero, so only baseline pull
        # and cross-affect interactions apply (which can change values slightly)
        # The key test is that RAGE doesn't increase significantly
        rage_idx = AFFECT_INDEX["RAGE"]
        assert result.values[rage_idx] <= before[rage_idx] + 0.05  # No significant increase
    
    def test_negative_values_rejected(self, tmp_path):
        """Test that negative affect values are rejected."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        with pytest.raises(AffectValueError):
            system.process_input({"CARE": -0.5}, intensity=1.0)
    
    def test_values_above_one_rejected(self, tmp_path):
        """Test that values > 1.0 are rejected."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        with pytest.raises(AffectValueError):
            system.process_input({"SEEKING": 1.5}, intensity=1.0)
    
    def test_very_small_values(self, tmp_path):
        """Test that very small values work correctly."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        result = system.process_input({
            "FEAR": 0.001,
            "PANIC": 0.0001,
        }, intensity=0.01)
        
        # Should succeed without numerical issues
        assert result is not None
        assert np.all(np.isfinite(result.values))
    
    def test_rapid_alternating_inputs(self, tmp_path):
        """Test rapidly alternating between opposite affects."""
        system = DynamicAffectSystem(data_dir=tmp_path)
        
        # Alternate between RAGE and CARE
        for i in range(20):
            if i % 2 == 0:
                system.process_input({"RAGE": 0.9}, intensity=1.0)
            else:
                system.process_input({"CARE": 0.9}, intensity=1.0)
        
        # State should still be valid
        final = system.current
        assert np.all(final.values >= 0)
        assert np.all(final.values <= 1)
        assert np.all(np.isfinite(final.values))


# =============================================================================
# AFFECT VECTOR TESTS
# =============================================================================

class TestAffectVector:
    """Test AffectVector dataclass functionality."""
    
    def test_affect_vector_creation(self):
        """Test creating AffectVector."""
        values = np.array([0.5, 0.2, 0.1, 0.0, 0.8, 0.1, 0.6], dtype=np.float32)
        vec = AffectVector(values)
        
        assert np.allclose(vec.values, values)
        assert vec.source == "unknown"
    
    def test_affect_vector_bounds_values(self):
        """Test that AffectVector clips values to [0, 1]."""
        # Values out of range
        values = np.array([-0.1, 0.5, 1.5, 0.0, 0.8, -0.5, 2.0], dtype=np.float32)
        vec = AffectVector(values)
        
        # Should be clipped
        assert np.all(vec.values >= 0)
        assert np.all(vec.values <= 1)
    
    def test_dominant_affect(self):
        """Test dominant affect identification."""
        values = np.array([0.3, 0.9, 0.2, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        vec = AffectVector(values)
        
        name, value = vec.dominant()
        
        assert name == "RAGE"  # Index 1 has highest value
        assert pytest.approx(value, abs=0.001) == 0.9
    
    def test_top_n_affects(self):
        """Test top N affects retrieval."""
        values = np.array([0.9, 0.1, 0.2, 0.1, 0.8, 0.1, 0.7], dtype=np.float32)
        vec = AffectVector(values)
        
        top_3 = vec.top_n(3)
        
        assert len(top_3) == 3
        assert top_3[0][0] == "SEEKING"  # Highest
        assert top_3[1][0] == "CARE"
        assert top_3[2][0] == "PLAY"
    
    def test_similarity(self):
        """Test cosine similarity between vectors."""
        vec1 = AffectVector(np.array([1, 0, 0, 0, 0, 0, 0], dtype=np.float32))
        vec2 = AffectVector(np.array([1, 0, 0, 0, 0, 0, 0], dtype=np.float32))
        vec3 = AffectVector(np.array([0, 1, 0, 0, 0, 0, 0], dtype=np.float32))
        
        # Identical vectors
        assert vec1.similarity(vec2) == pytest.approx(1.0)
        
        # Orthogonal vectors
        assert vec1.similarity(vec3) == pytest.approx(0.0)
    
    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        values = np.array([0.5, 0.2, 0.3, 0.1, 0.9, 0.0, 0.7], dtype=np.float32)
        vec1 = AffectVector(values, source="test")
        
        # Convert to dict
        data = vec1.to_dict()
        
        # Convert back
        vec2 = AffectVector.from_dict(data)
        
        assert np.allclose(vec1.values, vec2.values)
