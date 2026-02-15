"""
Comprehensive tests for AffectCorrelation module.

Tests cover:
- Constructor initialization
- Transition recording
- Trigger analysis
- Sensitivity analysis
- Clear functionality
- Thread safety
- Edge cases
"""

import pytest
import numpy as np
import time
import threading
from collections import deque
from nima_core.cognition.affect_correlation import (
    AffectCorrelation,
    StateTransition,
    AFFECTS,
)


class TestStateTransition:
    """Test StateTransition dataclass."""
    
    def test_transition_creation(self):
        """Test basic transition creation."""
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        transition = StateTransition(
            input_affects={"SEEKING": 0.8, "CARE": 0.3},
            from_values=from_state,
            to_values=to_state,
            timestamp=time.time()
        )
        
        assert "SEEKING" in transition.input_affects
        assert transition.input_affects["SEEKING"] == 0.8
        assert isinstance(transition.from_values, np.ndarray)
        assert isinstance(transition.to_values, np.ndarray)
    
    def test_transition_to_dict(self):
        """Test transition serialization."""
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        transition = StateTransition(
            input_affects={"CARE": 0.9},
            from_values=from_state,
            to_values=to_state,
            timestamp=1234567890.0
        )
        
        data = transition.to_dict()
        
        assert data["input_affects"]["CARE"] == 0.9
        assert isinstance(data["from_values"], list)
        assert isinstance(data["to_values"], list)
        assert data["timestamp"] == 1234567890.0


class TestAffectCorrelationConstructor:
    """Test AffectCorrelation initialization."""
    
    def test_default_constructor(self):
        """Test creation with default parameters."""
        corr = AffectCorrelation()
        
        assert corr.window_size == 100
        assert len(corr) == 0
        assert isinstance(corr._transitions, deque)
    
    def test_custom_window_size(self):
        """Test custom window_size parameter."""
        corr = AffectCorrelation(window_size=50)
        assert corr.window_size == 50
        assert corr._transitions.maxlen == 50
    
    def test_uses_deque_not_list(self):
        """Test that _transitions is a deque, not a list."""
        corr = AffectCorrelation()
        assert isinstance(corr._transitions, deque)
        assert not isinstance(corr._transitions, list)


class TestAffectCorrelationRecord:
    """Test transition recording functionality."""
    
    def test_record_stores_transition(self):
        """Test that record_transition() stores data."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition(
            input_affects={"SEEKING": 0.8},
            from_state=from_state,
            to_state=to_state
        )
        
        assert len(corr) == 1
    
    def test_record_copies_inputs(self):
        """Test that record copies arrays, not references."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        input_dict = {"CARE": 0.9}
        
        corr.record_transition(input_dict, from_state, to_state)
        
        # Modify originals
        from_state[0] = 999
        to_state[0] = 999
        input_dict["CARE"] = 0.0
        
        # Should not affect stored transition
        recent = corr.get_recent_transitions(1)
        assert recent[0]["inputs"]["CARE"] == 0.9
    
    def test_record_respects_window_size(self):
        """Test that deque auto-prunes when window exceeded."""
        corr = AffectCorrelation(window_size=5)
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        # Record 10 transitions
        for i in range(10):
            corr.record_transition(
                input_affects={"SEEKING": 0.5},
                from_state=from_state,
                to_state=to_state
            )
        
        # Should only keep 5 (deque maxlen)
        assert len(corr) == 5
    
    def test_record_multiple_transitions(self):
        """Test recording multiple transitions."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # CARE increase
        to_state1 = np.array([0.5, 0.1, 0.1, 0.1, 0.9, 0.1, 0.4], dtype=np.float32)
        corr.record_transition({"CARE": 0.8}, from_state, to_state1)
        
        # FEAR increase
        to_state2 = np.array([0.5, 0.1, 0.7, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        corr.record_transition({"FEAR": 0.7}, from_state, to_state2)
        
        assert len(corr) == 2


class TestAffectCorrelationTriggers:
    """Test trigger analysis functionality."""
    
    def test_analyze_triggers_basic(self):
        """Test basic trigger identification."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Record multiple CARE increases from CARE input
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.8 + i*0.01, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.8}, from_state, to_state)
        
        # Analyze what triggers CARE
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        
        assert len(triggers) > 0
        # Should identify CARE input as trigger
        trigger_names = [t[0] for t in triggers]
        assert "CARE" in trigger_names
    
    def test_analyze_triggers_min_samples(self):
        """Test min_samples threshold."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Only 2 samples
        for i in range(2):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.8}, from_state, to_state)
        
        # Require 3 samples
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        assert len(triggers) == 0
        
        # Require 2 samples
        triggers = corr.analyze_triggers("CARE", min_samples=2)
        assert len(triggers) > 0
    
    def test_analyze_triggers_min_correlation(self):
        """Test min_correlation threshold."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Weak correlation
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.51, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.8}, from_state, to_state)
        
        # High threshold
        triggers = corr.analyze_triggers("CARE", min_correlation=0.5)
        assert len(triggers) == 0
        
        # Low threshold
        triggers = corr.analyze_triggers("CARE", min_correlation=0.0)
        assert len(triggers) > 0
    
    def test_analyze_triggers_ignores_decreases(self):
        """Test that only increases are analyzed."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
        
        # Record CARE decreases
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.3, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"RAGE": 0.8}, from_state, to_state)
        
        # Should find no triggers (only decreases)
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        assert len(triggers) == 0
    
    def test_analyze_triggers_sorted_by_strength(self):
        """Test that results are sorted by correlation strength."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Strong CARE trigger
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.9, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.9}, from_state, to_state)
        
        # Weak SEEKING trigger
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"SEEKING": 0.8}, from_state, to_state)
        
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        
        # Should be sorted strongest first
        if len(triggers) >= 2:
            assert triggers[0][1] >= triggers[1][1]
    
    def test_analyze_triggers_invalid_affect(self):
        """Test with invalid affect name."""
        corr = AffectCorrelation()
        
        triggers = corr.analyze_triggers("INVALID_AFFECT")
        assert len(triggers) == 0
    
    def test_analyze_triggers_returns_tuple_format(self):
        """Test return format: (input_name, strength, count)."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.8}, from_state, to_state)
        
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        
        assert len(triggers) > 0
        # Check tuple structure
        trigger = triggers[0]
        assert isinstance(trigger, tuple)
        assert len(trigger) == 3
        assert isinstance(trigger[0], str)    # input name
        # Accept both Python float and numpy float types
        assert isinstance(trigger[1], (float, np.floating))  # strength
        assert isinstance(trigger[2], int)    # count


class TestAffectCorrelationSensitivity:
    """Test sensitivity analysis functionality."""
    
    def test_analyze_sensitivity_basic(self):
        """Test basic sensitivity analysis."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # CARE changes a lot
        to_state1 = np.array([0.5, 0.1, 0.1, 0.1, 0.9, 0.1, 0.4], dtype=np.float32)
        corr.record_transition({"CARE": 0.8}, from_state, to_state1)
        
        # SEEKING barely changes
        to_state2 = np.array([0.51, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        corr.record_transition({"SEEKING": 0.3}, from_state, to_state2)
        
        sensitivity = corr.analyze_sensitivity()
        
        # CARE should be more sensitive than SEEKING
        assert sensitivity["CARE"] > sensitivity["SEEKING"]
    
    def test_analyze_sensitivity_returns_all_affects(self):
        """Test that all 7 affects are in results."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.6, 0.2, 0.2, 0.2, 0.6, 0.2, 0.5], dtype=np.float32)
        
        corr.record_transition({"SEEKING": 0.5}, from_state, to_state)
        
        sensitivity = corr.analyze_sensitivity()
        
        assert len(sensitivity) == 7
        for affect in AFFECTS:
            assert affect in sensitivity
    
    def test_analyze_sensitivity_empty_history(self):
        """Test sensitivity with no transitions."""
        corr = AffectCorrelation()
        
        sensitivity = corr.analyze_sensitivity()
        
        # Should return all zeros
        for affect in AFFECTS:
            assert sensitivity[affect] == 0.0
    
    def test_analyze_sensitivity_scores_are_positive(self):
        """Test that sensitivity scores are non-negative."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Some increases, some decreases
        to_state1 = np.array([0.7, 0.0, 0.3, 0.2, 0.3, 0.2, 0.6], dtype=np.float32)
        corr.record_transition({"SEEKING": 0.8}, from_state, to_state1)
        
        sensitivity = corr.analyze_sensitivity()
        
        for affect, score in sensitivity.items():
            assert score >= 0.0


class TestAffectCorrelationClear:
    """Test clear functionality."""
    
    def test_clear_empties_deque(self):
        """Test clear() removes all transitions."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        # Record several
        for i in range(5):
            corr.record_transition({"SEEKING": 0.5}, from_state, to_state)
        
        assert len(corr) == 5
        
        corr.clear()
        
        assert len(corr) == 0
        assert isinstance(corr._transitions, deque)
    
    def test_clear_deque_not_list(self):
        """Test that clear() maintains deque type (not list)."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition({"CARE": 0.8}, from_state, to_state)
        corr.clear()
        
        # Should still be deque
        assert isinstance(corr._transitions, deque)
        assert not isinstance(corr._transitions, list)


class TestAffectCorrelationThreadSafety:
    """Test thread safety of concurrent operations."""
    
    def test_concurrent_record(self):
        """Test concurrent record_transition() calls."""
        corr = AffectCorrelation(window_size=200)
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        errors = []
        
        def record_many():
            try:
                for i in range(20):
                    corr.record_transition({"SEEKING": 0.5}, from_state, to_state)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Spawn 5 threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=record_many)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have no errors
        assert len(errors) == 0
        
        # Should have recorded 100 transitions
        assert len(corr) == 100
    
    def test_concurrent_read_write(self):
        """Test concurrent analysis and recording."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        errors = []
        
        def writer():
            try:
                for i in range(10):
                    corr.record_transition({"CARE": 0.8}, from_state, to_state)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(10):
                    _ = corr.analyze_triggers("CARE")
                    _ = corr.analyze_sensitivity()
                    _ = len(corr)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        # Spawn writer and reader threads
        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestAffectCorrelationEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_history_analyze_triggers(self):
        """Test analyze_triggers with no transitions."""
        corr = AffectCorrelation()
        
        triggers = corr.analyze_triggers("CARE")
        assert len(triggers) == 0
    
    def test_empty_history_analyze_sensitivity(self):
        """Test analyze_sensitivity with no transitions."""
        corr = AffectCorrelation()
        
        sensitivity = corr.analyze_sensitivity()
        assert all(v == 0.0 for v in sensitivity.values())
    
    def test_single_transition(self):
        """Test analysis with only one transition."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition({"CARE": 0.9}, from_state, to_state)
        
        # Should not crash, but won't have enough samples
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        assert len(triggers) == 0
        
        # Sensitivity should work
        sensitivity = corr.analyze_sensitivity()
        assert sensitivity["CARE"] > 0
    
    def test_low_input_intensity_ignored(self):
        """Test that low input intensities are ignored in trigger analysis."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        
        # Very low input (< 0.1 threshold)
        for i in range(5):
            to_state = np.array([0.5, 0.1, 0.1, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
            corr.record_transition({"CARE": 0.05}, from_state, to_state)
        
        # Should not identify as trigger
        triggers = corr.analyze_triggers("CARE", min_samples=3)
        assert len(triggers) == 0


class TestAffectCorrelationMiscellaneous:
    """Test miscellaneous functionality."""
    
    def test_len_operator(self):
        """Test __len__ operator."""
        corr = AffectCorrelation()
        assert len(corr) == 0
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition({"SEEKING": 0.5}, from_state, to_state)
        assert len(corr) == 1
    
    def test_repr(self):
        """Test __repr__ string representation."""
        corr = AffectCorrelation(window_size=50)
        repr_str = repr(corr)
        
        assert "AffectCorrelation" in repr_str
        assert "transitions" in repr_str
    
    def test_get_input_distribution(self):
        """Test get_input_distribution method."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition({"CARE": 0.8}, from_state, to_state)
        corr.record_transition({"CARE": 0.7}, from_state, to_state)
        corr.record_transition({"SEEKING": 0.6}, from_state, to_state)
        
        dist = corr.get_input_distribution()
        assert dist["CARE"] == 2
        assert dist["SEEKING"] == 1
    
    def test_get_recent_transitions(self):
        """Test get_recent_transitions method."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.8, 0.1, 0.4], dtype=np.float32)
        
        for i in range(5):
            corr.record_transition({"CARE": 0.8}, from_state, to_state)
        
        recent = corr.get_recent_transitions(count=3)
        assert len(recent) == 3
        
        # Check structure
        assert "inputs" in recent[0]
        assert "dominant_change" in recent[0]
        assert "timestamp" in recent[0]
    
    def test_get_recent_transitions_limit(self):
        """Test get_recent_transitions with fewer transitions than requested."""
        corr = AffectCorrelation()
        
        from_state = np.array([0.5, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4], dtype=np.float32)
        to_state = np.array([0.7, 0.1, 0.2, 0.1, 0.6, 0.1, 0.4], dtype=np.float32)
        
        corr.record_transition({"SEEKING": 0.5}, from_state, to_state)
        
        recent = corr.get_recent_transitions(count=10)
        assert len(recent) == 1
