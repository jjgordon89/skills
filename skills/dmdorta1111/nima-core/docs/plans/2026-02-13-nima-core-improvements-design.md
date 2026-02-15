# NIMA-Core Improvement Design

**Date:** 2026-02-13
**Status:** Draft
**Author:** Code Review

---

## Executive Summary

This design document outlines concrete improvements to the nima-core Dynamic Affect System across four critical areas:

1. **Code Quality**: Fix typos, improve error handling, add validation
2. **Affective Model**: Implement momentum, cross-affect interactions, intensity-aware decay
3. **Feature Completeness**: Add emotion history, correlation analysis, conversation isolation
4. **Integration**: Enhanced OpenClaw plugin with response injection

---

## 1. Code Quality Improvements

### 1.1 Typo Fixes (Priority: HIGH)

**Files affected:**
- `nima_core/cognition/dynamic_affect.py`
- `nima_core/cognition/response_modulator_v2.py`
- `nima_core/cognition/archetypes.py`
- `openclaw_plugin/index.js`

**Specific fixes needed:**

| File | Line | Current | Correct |
|------|------|---------|---------|
| dynamic_affect.py | 38 | `@dataclass` | `@dataclass` |
| dynamic_affect.py | 63 | `"blended"` | `"blended"` |
| dynamic_affect.py | 104 | `"similarity"` | `"similarity"` |
| dynamic_affect.py | 130 | `"curious"` | `"curious"` |
| dynamic_affect.py | 368 | `"deviation"` | `"deviation"` |
| dynamic_affect.py | 370 | `"similarity"` | `"similarity"` |
| response_modulator_v2.py | 31 | `"guidance"` | `"guidance"` |
| response_modulator_v2.py | 43 | `"dominant_affect"` | `"dominant_affect"` |
| response_modulator_v2.py | 317 | `{guidance.tone}` | `{guidance.tone}` |
| archetypes.py | 13 | `"Curious"` | `"Curious"` |
| index.js | 8 | `exclamations` | `exclamations` |
| index.js | 18 | `Tier 1` | `Tier 1` |
| index.js | 318 | `named.CARE` | `named.CARE` |
| index.js | 319 | `named.SEEKING` | `named.SEEKING` |
| index.js | 435 | `"1.00"` | `"1.00"` |

### 1.2 Exception Hierarchy

```python
# nima_core/cognition/exceptions.py (new file)

class NimaError(Exception):
    """Base exception for nima-core."""
    pass

class AffectVectorError(NimaError):
    """Raised when affect vector is invalid."""
    pass

class InvalidAffectNameError(AffectVectorError):
    """Raised when an unknown affect name is used."""
    pass

class BaselineValidationError(AffectVectorError):
    """Raised when baseline vector has wrong dimensions or values."""
    pass

class StatePersistenceError(NimaError):
    """Raised when state cannot be saved/loaded."""
    pass

class ProfileNotFoundError(NimaError):
    """Raised when a requested profile doesn't exist."""
    pass
```

### 1.3 Input Validation

```python
# Add to dynamic_affect.py

def _validate_affect_dict(self, affect_dict: Dict[str, float]) -> None:
    """Validate affect dictionary has correct keys and values."""
    for name, value in affect_dict.items():
        name_upper = name.upper()
        if name_upper not in AFFECT_INDEX:
            raise InvalidAffectNameError(
                f"Unknown affect '{name}'. Valid: {', '.join(AFFECTS)}"
            )
        if not isinstance(value, (int, float)):
            raise AffectVectorError(f"Affect value must be numeric, got {type(value)}")
        if not 0 <= value <= 1:
            raise AffectVectorError(f"Affect value must be in [0, 1], got {value}")

def _validate_baseline(self, baseline: Union[List, np.ndarray]) -> None:
    """Validate baseline vector has correct shape and values."""
    if len(baseline) != 7:
        raise BaselineValidationError(
            f"Baseline must have 7 values, got {len(baseline)}"
        )
    if not all(0 <= v <= 1 for v in baseline):
        raise BaselineValidationError("Baseline values must be in [0, 1]")
```

---

## 2. Affective Model Enhancements

### 2.1 Implement Momentum Parameter

**Current issue:** `momentum` parameter (0.85) is set but never used.

**Proposed fix:**

```python
def process_input(self, detected_affect: Dict[str, float],
                 intensity: float = 1.0,
                 profile: Optional[str] = None) -> AffectVector:
    # ... existing setup code ...

    # Apply momentum: blend input with current state
    # Higher momentum = more resistance to change
    momentum_factor = 1.0 - self.momentum  # 0.15 by default
    effective_blend = self.blend_strength * momentum_factor

    new_values = self._current.values + effective_blend * (input_vec - self._current.values)

    # ... rest of method ...
```

### 2.2 Cross-Affect Interactions

**New module:** `nima_core/cognition/affect_interactions.py`

```python
"""
Cross-affect interactions model certain affects suppress or amplify others.
"""

# Interaction matrix: rows affect columns
# Negative = suppression, positive = amplification
INTERACTION_MATRIX = {
    "FEAR": {
        "PLAY": -0.4,    # Fear suppresses playfulness
        "SEEKING": -0.2, # Fear reduces curiosity
    },
    "RAGE": {
        "CARE": -0.3,    # Anger suppresses nurturing
        "FEAR": -0.5,    # Rage suppresses fear (fight response)
    },
    "PANIC": {
        "SEEKING": -0.3,  # Panic reduces exploration
        "PLAY": -0.5,     # Grief suppresses play
    },
    "CARE": {
        "RAGE": -0.4,     # Caring suppresses anger
    },
    "PLAY": {
        "PANIC": -0.3,    # Playfulness reduces distress
        "FEAR": -0.2,      # Play reduces fear
    },
    "SEEKING": {
        "PANIC": -0.2,    # Curiosity reduces anxiety
    },
}

def apply_cross_affect_interactions(values: np.ndarray,
                                 affect_index: Dict[str, int]) -> np.ndarray:
    """
    Apply cross-affect interactions to a 7D affect vector.

    Returns a new vector with interactions applied.
    """
    result = values.copy()

    for affect, interactions in INTERACTION_MATRIX.items():
        source_idx = affect_index.get(affect)
        if source_idx is None:
            continue

        source_val = values[source_idx]
        if source_val < 0.3:  # Threshold for applying interactions
            continue

        for target, strength in interactions.items():
            target_idx = affect_index.get(target)
            if target_idx is None:
                continue

            # Interaction strength scales with source affect intensity
            delta = source_val * strength
            result[target_idx] = np.clip(result[target_idx] + delta, 0, 1)

    return result
```

### 2.3 Intensity-Aware Decay

```python
def _apply_temporal_decay(self) -> None:
    """
    Decay current state toward baseline with intensity awareness.

    High-intensity states decay slower initially, then accelerate.
    This models the "emotional hangover" effect.
    """
    if self._current is None:
        return

    hours_elapsed = (time.time() - self._current.timestamp) / 3600
    if hours_elapsed <= 0:
        return

    # Calculate deviation magnitude
    deviation = np.abs(self._current.values - self.baseline.values)
    avg_deviation = np.mean(deviation)

    # Decay rate depends on intensity:
    # - Low intensity (< 0.3): normal decay
    # - High intensity (> 0.7): slower initial decay, faster later
    if avg_deviation > 0.7:
        # Emotional shock: slower decay, non-linear
        decay_factor = np.exp(-self.decay_rate * hours_elapsed * 0.7)
    elif avg_deviation > 0.4:
        # Moderate: normal decay
        decay_factor = np.exp(-self.decay_rate * hours_elapsed)
    else:
        # Low intensity: faster return to baseline
        decay_factor = np.exp(-self.decay_rate * hours_elapsed * 1.3)

    self._current.values = self.baseline.values + decay_factor * deviation
    self._current.values = np.clip(self._current.values, 0. 1)
    self._current.timestamp = time.time()
    self._current.source = "decayed"
```

---

## 3. Feature Additions

### 3.1 Emotion History API

**New module:** `nima_core/cognition/affect_history.py`

```python
"""
Emotion state history with configurable retention.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class AffectSnapshot:
    """A frozen moment in affect state."""
    values: np.ndarray
    timestamp: float
    source: str
    dominant: Tuple[str, float]
    deviation: float

    def to_dict(self) -> Dict:
        return {
            "values": self.values.tolist(),
            "timestamp": self.timestamp,
            "source": self.source,
            "dominant": self.dominant,
            "deviation": self.deviation,
        }

class AffectHistory:
    """Manages emotion state history with size/time-based retention."""

    def __init__(self,
                 max_snapshots: int = 1000,
                 max_age_hours: float = 168):  # 1 week default
        """
        Args:
            max_snapshots: Maximum snapshots to keep (LRU eviction)
            max_age_hours: Maximum age of snapshots to keep
        """
        self.max_snapshots = max_snapshots
        self.max_age_hours = max_age_hours
        self._snapshots: List[AffectSnapshot] = []

    def record(self, affect: AffectVector,
               baseline: AffectVector) -> AffectSnapshot:
        """Record a snapshot of current state."""
        deviation = float(np.linalg.norm(affect.values - baseline.values))

        snapshot = AffectSnapshot(
            values=affect.values.copy(),
            timestamp=affect.timestamp,
            source=affect.source,
            dominant=affect.dominant(),
            deviation=deviation,
        )

        self._snapshots.append(snapshot)
        self._prune()

        return snapshot

    def _prune(self) -> None:
        """Prune old snapshots beyond limits."""
        now = time.time()
        cutoff = now - (self.max_age_hours * 3600)

        # Remove by age
        self._snapshots = [
            s for s in self._snapshots
            if s.timestamp > cutoff
        ]

        # Remove by count (LRU: keep newest)
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots = self._snapshots[-self.max_snapshots:]

    def get_state_at(self, timestamp: float) -> Optional[AffectSnapshot]:
        """Get state closest to given timestamp."""
        if not self._snapshots:
            return None

        closest = min(self._snapshots,
                     key=lambda s: abs(s.timestamp - timestamp))

        if abs(closest.timestamp - timestamp) < 3600:  # Within 1 hour
            return closest
        return None

    def get_timeline(self, duration_hours: float = 24) -> List[AffectSnapshot]:
        """Get snapshots from last N hours."""
        cutoff = time.time() - (duration_hours * 3600)
        return [s for s in self._snapshots if s.timestamp > cutoff]
```

### 3.2 Correlation Analysis

```python
class AffectCorrelation:
    """Analyzes correlation between input patterns and affect states."""

    def __init__(self, window_size: int = 100):
        """
        Args:
            window_size: Number of recent transitions to analyze
        """
        self.window_size = window_size
        self._transitions: List[Dict] = []

    def record_transition(self,
                          input_affects: Dict[str, float],
                          previous_state: AffectVector,
                          new_state: AffectVector):
        """Record a state transition."""
        self._transitions.append({
            "input": input_affects,
            "from": previous_state.values.copy(),
            "to": new_state.values.copy(),
            "timestamp": time.time(),
        })

        if len(self._transitions) > self.window_size:
            self._transitions.pop(0)

    def analyze_triggers(self,
                         target_affect: str,
                         min_correlation: float = 0.3) -> List[Tuple[str, float]]:
        """
        Analyze which input patterns trigger a target affect.

        Returns:
            List of (input_pattern, correlation_strength) sorted by strength
        """
        if target_affect not in AFFECT_INDEX:
            raise InvalidAffectNameError(f"Unknown affect: {target_affect}")

        target_idx = AFFECT_INDEX[target_affect]
        correlations: Dict[str, List[float]] = {}

        for trans in self._transitions:
            from_val = trans["from"][target_idx]
            to_val = trans["to"][target_idx]
            delta = to_val - from_val

            if delta <= 0:  # Only analyze increases
                continue

            for input_affect, input_val in trans["input"].items():
                if input_val < 0.2:  # Threshold
                    continue

                if input_affect not in correlations:
                    correlations[input_affect] = []

                # Correlate input intensity with output change
                correlations[input_affect].append((input_val, delta))

        # Calculate correlation coefficient
        results = []
        for affect, pairs in correlations.items():
            if len(pairs) < 3:  # Need minimum samples
                continue

            inputs = [p[0] for p in pairs]
            outputs = [p[1] for p in pairs]

            # Simple correlation: avg(output) / avg(input)
            strength = np.mean(outputs) / (np.mean(inputs) + 0.01)

            if strength > min_correlation:
                results.append((affect, strength))

        return sorted(results, key=lambda x: x[1], reverse=True)
```

---

## 4. Enhanced OpenClaw Integration

### 4.1 Response Injection Hook

**Add to `openclaw_plugin/index.js`:**

```javascript
// ─── Hook 4: before_response_send (injects affect into response) ───
api.on("before_response_send", (event, ctx) => {
  try {
    if (skipSubagents && ctx.sessionKey?.includes(":subagent:")) return;

    const affect = getCurrentAffect(identityName, baseline);
    const { named, dominant } = affect;

    // Determine style modifier based on affect
    let styleModifier = "";

    if (dominant.name === "PLAY" && named.PLAY > 0.6) {
      styleModifier = " 😊 [emoji playfulness allowed]";
    } else if (dominant.name === "CARE" && named.CARE > 0.7) {
      styleModifier = " 💚 [emphasize warmth in tone]";
    } else if (dominant.name === "RAGE" && named.RAGE > 0.5) {
      styleModifier = " ⚡ [be direct and firm]";
    } else if (dominant.name === "FEAR" && named.FEAR > 0.5) {
      styleModifier = " ⚠️ [be cautious and thorough]";
    }

    // Subtle injection - doesn't modify content directly
    // The AI will interpret the style modifier naturally
    if (styleModifier && event.response) {
      event.response.metadata = event.response.metadata || {};
      event.response.metadata.affect_hint = styleModifier.trim();
    }

  } catch (err) {
    log.debug?.(`[nima-affect] before_response_send error: ${err.message}`);
  }
}, { priority: 5 });
```

### 4.2 Conversation Isolation

```javascript
// Store affect per-conversation, not just per-identity
function getStatePath(identityName, conversationId) {
  const nimaHome = process.env.NIMA_HOME || join(os.homedir(), ".nima");
  if (conversationId) {
    return join(nimaHome, "affect", "conversations",
                `${identityName}_${conversationId}.json`);
  }
  return join(nimaHome, "affect", `affect_state_${identityName}.json`);
}
```

---

## 5. Implementation Priority

### Phase 1: Critical Fixes (Week 1)
1. Fix all typos (1.1)
2. Add exception hierarchy (1.2)
3. Implement momentum parameter (2.1)

### Phase 2: Model Improvements (Week 2)
1. Cross-affect interactions (2.2)
2. Intensity-aware decay (2.3)
3. Input validation (1.3)

### Phase 3: Features (Week 3-4)
1. Emotion history API (3.1)
2. Correlation analysis (3.2)
3. Conversation isolation (4.2)

### Phase 4: Integration (Week 4)
1. Response injection hook (4.1)
2. Plugin configuration UI

---

## 6. Testing Strategy

### Unit Tests Required

```python
# tests/test_affect_interactions.py
def test_cross_affect_fear_suppresses_play():
    """High FEAR should suppress PLAY affect."""
    values = np.array([0.3, 0.1, 0.8, 0.1, 0.5, 0.1, 0.7])  # High FEAR, PLAY
    result = apply_cross_affect_interactions(values, AFFECT_INDEX)
    assert result[6] < 0.7  # PLAY should be reduced

# tests/test_history.py
def test_history_pruning():
    """History should prune old snapshots."""
    history = AffectHistory(max_snapshots=3)
    for i in range(5):
        history.record(create_test_vector())
    assert len(history._snapshots) == 3
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_emotion_cycle():
    """Test emotion input → affect update → history → decay."""
    system = DynamicAffectSystem(identity_name="test")
    system.process_input({"CARE": 0.9}, intensity=0.8)

    history = system.history
    snapshot = history.record(system.current, system.baseline)

    time.sleep(0.1)
    system.drift_toward_baseline()

    assert snapshot.dominant[0] == "CARE"
    assert system.current.values[4] < 0.9  # Should decay
```

---

## 7. API Changes Summary

### Breaking Changes
None proposed. All additions are backward compatible.

### New Public APIs

```python
# History
class AffectHistory:
    def record(affect: AffectVector, baseline: AffectVector) -> AffectSnapshot
    def get_state_at(timestamp: float) -> Optional[AffectSnapshot]
    def get_timeline(duration_hours: float) -> List[AffectSnapshot]

# Correlation
class AffectCorrelation:
    def record_transition(input_affects, previous_state, new_state)
    def analyze_triggers(target_affect: str) -> List[Tuple[str, float]]

# Enhanced DynamicAffectSystem
class DynamicAffectSystem:
    @property
    def history(self) -> AffectHistory
    @property
    def correlations(self) -> AffectCorrelation
```

---

## 8. Performance Considerations

- History storage: O(max_snapshots) memory, O(log n) lookup
- Correlation analysis: O(window_size) per analysis
- Cross-affect interactions: O(1) constant time (7x7 matrix)

---

## 9. Migration Path

1. **v2.0.0**: Include typo fixes + momentum (no breaking changes)
2. **v2.1.0**: Add cross-affect interactions + intensity-aware decay
3. **v2.2.0**: Add history and correlation APIs
4. **v2.3.0**: Enhanced OpenClaw integration

All versions maintain state file compatibility through version handling.

---

## Approval

- [ ] Architecture approved
- [ ] Implementation timeline approved
- [ ] Ready to proceed to writing-plans skill
