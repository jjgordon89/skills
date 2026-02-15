# NIMA Core Improvement Checklist

**Date:** 2026-02-13
**Status:** In Progress

## Phase 4: Integration

### 4.1 Response Injection Hook
- [x] Added `before_response_send` hook to OpenClaw plugin
- [x] Injects affect hints based on dominant affect:
  - CARE > 0.6 → "💚 [express warmth and nurturing]"
  - PLAY > 0.6 → "😊 [light-hearted, humor welcome]"
  - SEEKING > 0.6 → "🔍 [curious, exploratory tone]"
  - RAGE > 0.4 → "⚡ [direct, firm, boundary-setting]"
  - FEAR > 0.4 → "⚠️ [cautious, thorough, careful]"
  - PANIC > 0.4 → "💜 [gentle, reassuring, grounding]"
- [x] Adds `affect_state` metadata to response

### 4.2 Conversation Isolation
- [x] Modified `getStatePath()` to accept `conversationId`
- [x] Creates `~/.nima/affect/conversations/{identity}_{convId}.json`
- [x] Updated all hooks to extract conversationId from context
- [x] Falls back to shared state if no conversationId

### Status
- [x] All 4 phases complete
- [x] Synced to active plugin

### 3.1 Emotion History API
- [x] Created `nima_core/cognition/affect_history.py`
- [x] AffectSnapshot: frozen moment in affect state
- [x] AffectHistory: manager with size/time-based pruning
- [x] Timeline queries: get_timeline, get_dominant_timeline
- [x] Deviation trend analysis
- [x] Optional persistence to disk

### 3.2 Correlation Analysis
- [x] Created `nima_core/cognition/affect_correlation.py`
- [x] AffectCorrelation: tracks input→state transitions
- [x] analyze_triggers(): which inputs trigger which affects
- [x] analyze_sensitivity(): which affects are most reactive
- [x] get_input_distribution(): input frequency analysis
- [x] detect_emotional_patterns(): pattern detection utility

### 3.3 Integration
- [x] Integrated history into DynamicAffectSystem
- [x] Integrated correlation into process_input()
- [x] Synced to lilu_core
- [x] All tests passing

### 2.1 Cross-Affect Interactions
- [x] Created `nima_core/cognition/affect_interactions.py`
- [x] Interaction matrix: FEAR suppresses PLAY, CARE suppresses RAGE, etc.
- [x] Threshold of 0.5 — only strong emotions affect others
- [x] Integrated into `process_input()` with `cross_affect` toggle
- [x] Synced to lilu_core

### 2.2 Intensity-Aware Decay
- [x] Updated `_apply_temporal_decay()` in dynamic_affect.py
- [x] Low intensity (< 0.3): faster decay (1.3x)
- [x] Moderate (0.3-0.6): normal decay
- [x] High intensity (> 0.6): slower decay (emotional hangover)
- [x] Synced to lilu_core

## Files to Update
1. `lilu_core/cognition/dynamic_affect.py`
2. `nima_core/nima_core/cognition/dynamic_affect.py`
3. `nima_core/nima_core/cognition/response_modulator_v2.py`
4. `nima_core/nima_core/cognition/archetypes.py`
5. `nima_core/openclaw_plugin/index.js`