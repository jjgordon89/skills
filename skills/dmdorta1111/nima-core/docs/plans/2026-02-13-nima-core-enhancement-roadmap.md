# NIMA-Core Enhancement Roadmap

**Date:** 2026-02-13
**Status:** Draft
**Version:** 1.0
**Review Type:** Comprehensive Feature Enhancement

---

## Executive Summary

This document outlines a comprehensive enhancement roadmap for the NIMA-Core Dynamic Affect System. Based on a thorough code review across core emotional engine, integration/API capabilities, and observability/tooling, this roadmap proposes a **modular enhancement approach** that maintains backward compatibility while enabling significant new capabilities.

**Key Findings:**
- Codebase demonstrates strong architectural principles with clean separation of concerns
- Scientific foundation (Panksepp 7-affect system) is well-implemented
- Thread-safe implementation with proper locking
- Limited test coverage and observability tools
- Missing key features: profile blending, multi-agent modeling, REST API, metrics/visualization

**Recommendation:** Modular Enhancement (Option A) - add independent, opt-in modules without breaking changes.

---

## Part I: Current State Assessment

### 1.1 Architecture Strengths

| Area | Assessment | Details |
|------|------------|---------|
| **Scientific Foundation** | Excellent | Panksepp 7-affect model with proper mathematical modeling |
| **Code Organization** | Excellent | Clean module separation, dataclasses, type hints |
| **Thread Safety** | Excellent | Comprehensive RLock usage, atomic file writes |
| **Documentation** | Very Good | 7+ markdown docs covering usage, API, migration |
| **Persistence** | Very Good | File-based with atomic writes, time-based decay |
| **Cross-Language** | Very Good | Python/JavaScript maintain identical math models |

### 1.2 Identified Gaps

| Category | Gap | Impact | Priority |
|----------|-----|--------|----------|
| **Core Engine** | Hard-coded constants not configurable | Limited flexibility for different agent types | Medium |
| **Core Engine** | No contextual memory integration | Emotions don't consider conversation history | High |
| **Core Engine** | No multi-agent interaction modeling | Agents can't affect each other's emotional states | High |
| **Core Engine** | No circadian rhythm support | No time-of-day baseline variations | Low |
| **Integration** | No REST API | Cannot monitor/control externally | High |
| **Integration** | File-only persistence | No database support for production deployments | Medium |
| **Integration** | No event streaming | Cannot integrate with external monitoring systems | Medium |
| **Integration** | Limited profile capabilities | No blending, inheritance, or runtime mutation | High |
| **Observability** | No metrics collection | No Prometheus/Grafana integration | High |
| **Observability** | No visualization tools | Cannot visualize affect evolution over time | Medium |
| **Observability** | Limited debugging support | No emotion transition logging or profiling hooks | Medium |
| **Testing** | Single integration test file | Low coverage, no edge case or performance tests | High |

### 1.3 Code Quality Issues

**Singleton Pattern Fragility** (`dynamic_affect.py:536-566`):
```python
# Current: Global singleton with ignored kwargs warning
_instance: Optional[DynamicAffectSystem] = None

def get_affect_system(...) -> DynamicAffectSystem:
    global _instance
    if _instance is None:
        _instance = DynamicAffectSystem(...)
    # WARNING: kwargs ignored on subsequent calls!
```

**Performance Bottleneck** (`emotion_detection.py:125-149`):
- Word-by-word lexicon lookup with stemming
- Could be optimized with pre-computed dictionary or ternary search trees

**Type Inconsistency** (`dynamic_affect.py:402-403`):
```python
input_vec[AFFECT_INDEX[name_upper]] = float(value)
# float() cast suggests validation should happen earlier
```

---

## Part II: Enhancement Approaches

### Option A: Modular Enhancement (RECOMMENDED)

Add enhancements as optional, independent modules.

**Pros:**
- Backward compatible - existing code unchanged
- Incremental adoption possible
- Lower risk, easier to test
- Faster feedback loop

**Cons:**
- More complex architecture (module coordination)
- Some duplication between core and modules

**Example Usage:**
```python
# Core unchanged, opt-in enhancements
system = DynamicAffectSystem("agent")
system.add_module(CircadianModule())
system.add_module(MetricsCollector())
system.add_module(ContextAwareModule())
```

### Option B: Major Version Upgrade (v3.0)

Significant refactor addressing architectural limitations.

**Pros:**
- Clean technical debt
- Coherent, unified design
- Future-proof architecture

**Cons:**
- Breaking changes for users
- Higher risk, longer timeline
- Migration required

**Example Usage:**
```python
# New architecture
container = AffectContainer()
container.register_persistence(PostgresPersistence())
container.register_feature(MultiAgentInteraction())
agent = container.create_agent("my-agent")
```

### Option C: Focused Feature Additions

Add only high-impact features without architectural changes.

**Pros:**
- Fast to implement
- Low disruption
- Immediate value

**Cons:**
- Technical debt remains
- Limited extensibility
- May need refactor later

**Example Usage:**
```python
# Simple additions
DynamicAffectSystem.blend_profiles(p1, p2, ratio=0.6)
rest_api.start_monitoring(port=8080)
system.visualize_timeline()
```

---

## Part III: Detailed Enhancement Proposals

### 3.1 Core Emotional Engine

#### 3.1.1 Profile Blending API

**Problem:** Profiles are static; cannot create hybrid personalities dynamically.

**Solution:** Add profile blending with weighted interpolation.

```python
# nima_core/cognition/personality_profiles.py

def blend_profiles(
    profile1: Union[str, PersonalityProfile],
    profile2: Union[str, PersonalityProfile],
    ratio: float = 0.5,
    name: Optional[str] = None
) -> PersonalityProfile:
    """
    Create a new profile by blending two existing profiles.

    Args:
        profile1: First profile (name or Profile object)
        profile2: Second profile (name or Profile object)
        ratio: Blend ratio (0.0 = all profile1, 1.0 = all profile2)
        name: Optional name for blended profile

    Returns:
        New PersonalityProfile with blended baseline

    Example:
        >>> guardian = get_profile("guardian")
        >>> explorer = get_profile("explorer")
        >>> protective_explorer = blend_profiles(guardian, explorer, 0.3)
    """
    p1 = _resolve_profile(profile1)
    p2 = _resolve_profile(profile2)

    blended_baseline = p1.baseline * (1 - ratio) + p2.baseline * ratio

    return PersonalityProfile(
        name=name or f"{p1.name}_{p2.name}_blended",
        baseline=blended_baseline,
        description=f"Blend of {p1.name} ({1-ratio:.0%}) and {p2.name} ({ratio:.0%})"
    )
```

#### 3.1.2 Context-Aware Processing Module

**Problem:** System doesn't incorporate conversation history or contextual events.

**Solution:** Optional module that enhances emotion detection with context.

```python
# nima_core/cognition/context_aware.py (new module)

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ConversationContext:
    """Context about the current conversation."""
    turns_count: int
    user_sentiment_trend: str  # "improving", "declining", "stable"
    topic_continuity: float  # 0-1, how much topic has changed
    time_since_last_exchange: float  # seconds
    recent_affects: List[str]  # Last 5 dominant affects

class ContextAwareModule:
    """
    Optional module for context-enhanced emotion processing.

    This module considers:
    - Conversation history trends
    - Topic continuity
    - Time patterns
    - Recent emotional states
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._history: List[Dict] = []

    def enhance_detection(
        self,
        detected: Dict[str, float],
        context: ConversationContext
    ) -> Dict[str, float]:
        """
        Enhance emotion detection with contextual modifiers.

        Example:
            - If user_sentiment_trend is "declining", increase CARE sensitivity
            - If topic_continuity is high, maintain current emotional momentum
            - If time_since_last_exchange > 1 hour, reduce all affects slightly
        """
        enhanced = detected.copy()

        # Sentiment trend modifier
        if context.user_sentiment_trend == "declining":
            enhanced["CARE"] = enhanced.get("CARE", 0) * 1.2
            enhanced["FEAR"] = enhanced.get("FEAR", 0) * 1.1
        elif context.user_sentiment_trend == "improving":
            enhanced["PLAY"] = enhanced.get("PLAY", 0) * 1.2
            enhanced["SEEKING"] = enhanced.get("SEEKING", 0) * 1.1

        # Topic continuity modifier
        if context.topic_continuity > 0.7:
            # Maintain emotional momentum in continuous conversations
            for affect in enhanced:
                enhanced[affect] *= 1.1

        # Time decay modifier
        if context.time_since_last_exchange > 3600:
            decay_factor = max(0.5, 1 - (context.time_since_last_exchange / 86400))
            for affect in enhanced:
                enhanced[affect] *= decay_factor

        return self._normalize(enhanced)

    def _normalize(self, affects: Dict[str, float]) -> Dict[str, float]:
        """Ensure affect values are in valid range."""
        return {k: min(1.0, max(0.0, v)) for k, v in affects.items()}
```

#### 3.1.3 Multi-Agent Interaction Modeling

**Problem:** No capability to model emotional influence between agents.

**Solution:** Module for cross-agent emotional contagion.

```python
# nima_core/cognition/multi_agent_interaction.py (new module)

from typing import Dict, Optional
import numpy as np

class MultiAgentAffectSystem:
    """
    Manages emotional interactions between multiple agents.

    Models:
    - Emotional contagion (affects spreading between agents)
    - Influence relationships (agent A affects agent B more)
    - Group emotional dynamics (fear spreading, panic amplification)
    """

    def __init__(self):
        self._systems: Dict[str, DynamicAffectSystem] = {}
        self._influence_matrix: Dict[str, Dict[str, float]] = {}

    def register_agent(
        self,
        agent_id: str,
        system: DynamicAffectSystem
    ) -> None:
        """Register an agent's affect system."""
        self._systems[agent_id] = system

    def set_influence(
        self,
        from_agent: str,
        to_agent: str,
        strength: float
    ) -> None:
        """
        Set how much one agent influences another.

        Args:
            from_agent: Agent that influences
            to_agent: Agent being influenced
            strength: Influence strength (0-1)
        """
        if from_agent not in self._influence_matrix:
            self._influence_matrix[from_agent] = {}
        self._influence_matrix[from_agent][to_agent] = strength

    def process_interaction(
        self,
        agent_a: str,
        agent_b: str,
        interaction_type: str
    ) -> None:
        """
        Process an interaction between two agents.

        Interaction types:
        - "conflict": Increases RAGE, FEAR; decreases CARE, PLAY
        - "cooperation": Increases CARE, PLAY, SEEKING
        - "competition": Increases RAGE, SEEKING; decreases PANIC
        - "isolation": Increases PANIC, FEAR
        """
        if agent_a not in self._systems or agent_b not in self._systems:
            return

        # Get current states
        state_a = self._systems[agent_a].current
        state_b = self._systems[agent_b].current

        # Apply interaction effects
        effects = self._get_interaction_effects(interaction_type)

        for affect, delta in effects.items():
            # Agent A affects Agent B
            influence = self._influence_matrix.get(agent_a, {}).get(agent_b, 0.5)
            self._systems[agent_b].process_input(
                {affect: delta * influence},
                intensity=0.3
            )

            # Agent B affects Agent A
            influence = self._influence_matrix.get(agent_b, {}).get(agent_a, 0.5)
            self._systems[agent_a].process_input(
                {affect: delta * influence},
                intensity=0.3
            )

    def _get_interaction_effects(self, interaction_type: str) -> Dict[str, float]:
        """Get affect changes for interaction type."""
        effects = {
            "conflict": {"RAGE": 0.3, "FEAR": 0.2, "CARE": -0.2, "PLAY": -0.3},
            "cooperation": {"CARE": 0.3, "PLAY": 0.2, "SEEKING": 0.2},
            "competition": {"RAGE": 0.2, "SEEKING": 0.3, "PANIC": -0.1},
            "isolation": {"PANIC": 0.3, "FEAR": 0.2},
        }
        return effects.get(interaction_type, {})

    def get_group_emotional_state(self) -> Dict[str, float]:
        """
        Calculate the aggregate emotional state of all agents.

        Returns average affect values across all agents.
        """
        if not self._systems:
            return {}

        all_values = np.array([
            s.current.values for s in self._systems.values()
        ])

        return {
            affect: float(np.mean(all_values[:, idx]))
            for affect, idx in AFFECT_INDEX.items()
        }
```

#### 3.1.4 Circadian Rhythm Module

**Problem:** No time-of-day variation in emotional baselines.

**Solution:** Optional module that modulates baselines based on time.

```python
# nima_core/cognition/circadian.py (new module)

from datetime import datetime, time
from typing import Dict, Callable
import numpy as np

class CircadianModule:
    """
    Optional module for time-of-day emotional modulation.

    Different times of day naturally affect emotional baselines:
    - Morning: Higher SEEKING, PLAY (energetic)
    - Midday: Higher FEAR (stress peak)
    - Evening: Higher CARE, PLAY (social time)
    - Night: Higher PANIC (isolation), lower SEEKING
    """

    # Default time-of-day modifiers (affect -> modifier)
    DEFAULT_MODIFIERS = {
        "morning": {  # 6-12
            "SEEKING": 0.1, "PLAY": 0.1, "RAGE": -0.05,
        },
        "midday": {  # 12-17
            "FEAR": 0.1, "RAGE": 0.05, "CARE": -0.05,
        },
        "evening": {  # 17-22
            "CARE": 0.1, "PLAY": 0.1, "SEEKING": 0.05,
        },
        "night": {  # 22-6
            "PANIC": 0.15, "FEAR": 0.1, "SEEKING": -0.2, "PLAY": -0.1,
        },
    }

    def __init__(
        self,
        custom_modifiers: Optional[Dict[str, Dict[str, float]]] = None
    ):
        self.modifiers = custom_modifiers or self.DEFAULT_MODIFIERS
        self._timezone_offset: float = 0  # Hours from UTC

    def set_timezone(self, offset_hours: float) -> None:
        """Set timezone offset for circadian calculations."""
        self._timezone_offset = offset_hours

    def get_time_period(self, dt: Optional[datetime] = None) -> str:
        """Determine time period from datetime."""
        if dt is None:
            dt = datetime.now()

        hour = (dt.hour + self._timezone_offset) % 24

        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "midday"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    def get_modulated_baseline(
        self,
        baseline: np.ndarray,
        dt: Optional[datetime] = None
    ) -> np.ndarray:
        """
        Get baseline modulated by time of day.

        Returns a new array with circadian adjustments applied.
        """
        period = self.get_time_period(dt)
        modifiers = self.modifiers.get(period, {})

        modulated = baseline.copy()
        for affect, modifier in modifiers.items():
            if affect in AFFECT_INDEX:
                idx = AFFECT_INDEX[affect]
                modulated[idx] = np.clip(
                    modulated[idx] + modifier,
                    0, 1
                )

        return modulated
```

### 3.2 Integration & API Enhancements

#### 3.2.1 REST API Module

**Problem:** No HTTP interface for external monitoring/control.

**Solution:** Optional FastAPI-based REST API server.

```python
# nima_core/api/rest.py (new module)

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import uvicorn

class AffectState(BaseModel):
    """REST API model for affect state."""
    identity: str
    SEEKING: float
    FEAR: float
    RAGE: float
    LUST: float
    CARE: float
    PANIC: float
    PLAY: float
    dominant: str
    timestamp: float

class EmotionInput(BaseModel):
    """REST API model for emotion input."""
    affects: Dict[str, float]
    intensity: Optional[float] = 1.0

class NimaRestAPI:
    """
    REST API server for NIMA-Core.

    Provides HTTP endpoints for:
    - Querying current affect state
    - Submitting emotion inputs
    - Getting history and correlations
    - Managing profiles
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        nima_home: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.nima_home = nima_home
        self.app = FastAPI(title="NIMA-Core API", version="2.0.0")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.app.get("/affect/{identity}/state", response_model=AffectState)
        async def get_state(identity: str):
            """Get current affect state for an identity."""
            system = get_affect_system(
                identity_name=identity,
                nima_home=self.nima_home
            )
            state = system.current
            baseline = system.baseline

            return AffectState(
                identity=identity,
                SEEKING=float(state.values[0]),
                FEAR=float(state.values[1]),
                RAGE=float(state.values[2]),
                LUST=float(state.values[3]),
                CARE=float(state.values[4]),
                PANIC=float(state.values[5]),
                PLAY=float(state.values[6]),
                dominant=state.dominant()[0],
                timestamp=state.timestamp
            )

        @self.app.post("/affect/{identity}/input")
        async def submit_input(identity: str, input_data: EmotionInput):
            """Submit emotion input for an identity."""
            system = get_affect_system(
                identity_name=identity,
                nima_home=self.nima_home
            )
            result = system.process_input(
                input_data.affects,
                intensity=input_data.intensity
            )
            return {"status": "processed", "dominant": result.dominant()}

        @self.app.get("/affect/{identity}/history")
        async def get_history(
            identity: str,
            duration_hours: float = 24
        ):
            """Get affect history for an identity."""
            system = get_affect_system(
                identity_name=identity,
                nima_home=self.nima_home
            )
            if not hasattr(system, 'history') or system.history is None:
                raise HTTPException(status_code=404, detail="History not enabled")

            timeline = system.history.get_timeline(duration_hours)
            return {
                "identity": identity,
                "duration_hours": duration_hours,
                "snapshots": [s.to_dict() for s in timeline]
            }

        @self.app.get("/affect/{identity}/profile")
        async def get_profile(identity: str):
            """Get current personality profile."""
            system = get_affect_system(
                identity_name=identity,
                nima_home=self.nima_home
            )
            return {
                "identity": identity,
                "profile": system.profile.name if system.profile else None,
                "baseline": system.baseline.values.tolist()
            }

    def start(self) -> None:
        """Start the REST API server."""
        uvicorn.run(self.app, host=self.host, port=self.port)

    def start_in_background(self) -> None:
        """Start the server in a background thread."""
        import threading
        thread = threading.Thread(target=self.start, daemon=True)
        thread.start()
```

#### 3.2.2 Database Persistence Layer

**Problem:** Only file-based persistence; no database support.

**Solution:** Abstract persistence interface with database implementations.

```python
# nima_core/persistence/interface.py (new module)

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

class AffectPersistence(ABC):
    """Abstract interface for affect state persistence."""

    @abstractmethod
    def save_state(
        self,
        identity: str,
        state: np.ndarray,
        timestamp: float,
        source: str
    ) -> None:
        """Save current state."""
        pass

    @abstractmethod
    def load_state(self, identity: str) -> Optional[Dict]:
        """Load state for identity. Returns None if not found."""
        pass

    @abstractmethod
    def delete_state(self, identity: str) -> bool:
        """Delete state for identity. Returns True if deleted."""
        pass

    @abstractmethod
    def list_identities(self) -> List[str]:
        """List all identities with saved states."""
        pass

# nima_core/persistence/postgres.py (new module)

class PostgresPersistence(AffectPersistence):
    """PostgreSQL implementation of affect persistence."""

    def __init__(
        self,
        connection_string: str,
        table_name: str = "affect_states"
    ):
        import psycopg
        self.conn = psycopg.connect(connection_string)
        self.table_name = table_name
        self._init_table()

    def _init_table(self) -> None:
        """Create table if not exists."""
        with self.conn.cursor() as cur:
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    identity VARCHAR(255) PRIMARY KEY,
                    seeking FLOAT NOT NULL,
                    fear FLOAT NOT NULL,
                    rage FLOAT NOT NULL,
                    lust FLOAT NOT NULL,
                    care FLOAT NOT NULL,
                    panic FLOAT NOT NULL,
                    play FLOAT NOT NULL,
                    timestamp FLOAT NOT NULL,
                    source VARCHAR(100),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def save_state(
        self,
        identity: str,
        state: np.ndarray,
        timestamp: float,
        source: str
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {self.table_name}
                (identity, seeking, fear, rage, lust, care, panic, play, timestamp, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (identity) DO UPDATE SET
                    seeking = EXCLUDED.seeking,
                    fear = EXCLUDED.fear,
                    rage = EXCLUDED.rage,
                    lust = EXCLUDED.lust,
                    care = EXCLUDED.care,
                    panic = EXCLUDED.panic,
                    play = EXCLUDED.play,
                    timestamp = EXCLUDED.timestamp,
                    source = EXCLUDED.source,
                    updated_at = CURRENT_TIMESTAMP
            """, (identity, *state, timestamp, source))
            self.conn.commit()

    def load_state(self, identity: str) -> Optional[Dict]:
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT seeking, fear, rage, lust, care, panic, play, timestamp, source
                FROM {self.table_name} WHERE identity = %s
            """, (identity,))
            row = cur.fetchone()
            if row:
                return {
                    "values": np.array(row[:7]),
                    "timestamp": row[7],
                    "source": row[8]
                }
        return None
```

#### 3.2.3 Event Streaming

**Problem:** Cannot stream affect changes to external systems.

**Solution:** Optional event streaming module with WebSocket and Pub/Sub support.

```python
# nima_core/streaming/event_stream.py (new module)

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import asyncio

@dataclass
class AffectEvent:
    """An affect state change event."""
    identity: str
    timestamp: float
    event_type: str  # "input_processed", "state_decayed", "baseline_changed"
    previous_state: Optional[Dict[str, float]]
    new_state: Dict[str, float]
    dominant_affect: str
    metadata: Dict

    def to_json(self) -> str:
        """Convert to JSON for streaming."""
        return json.dumps({
            "identity": self.identity,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "dominant_affect": self.dominant_affect,
            "metadata": self.metadata
        })

class AffectEventStream:
    """
    Manages streaming of affect state events.

    Supports:
    - WebSocket broadcast to subscribers
    - Redis Pub/Sub for distributed systems
    - Custom callback handlers
    """

    def __init__(self):
        self._subscribers: List[Callable] = []
        self._redis_client = None
        self._channel_prefix = "nima:affect"

    def subscribe(self, callback: Callable[[AffectEvent], None]) -> None:
        """Subscribe a callback to affect events."""
        self._subscribers.append(callback)

    def publish(self, event: AffectEvent) -> None:
        """Publish event to all subscribers."""
        # Local subscribers
        for callback in self._subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Subscriber error: {e}")

        # Redis Pub/Sub
        if self._redis_client:
            asyncio.create_task(
                self._redis_client.publish(
                    f"{self._channel_prefix}:{event.identity}",
                    event.to_json()
                )
            )

    def enable_redis(self, redis_url: str) -> None:
        """Enable Redis Pub/Sub for distributed streaming."""
        import redis.asyncio as redis
        self._redis_client = redis.from_url(redis_url)

    def create_websocket_handler(self):
        """Create a FastAPI WebSocket handler for real-time updates."""
        from fastapi import WebSocket
        from collections import deque

        # Queue for each websocket connection
        queues: deque = deque()

        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            queues.append(websocket)

            try:
                # Subscribe to events
                def on_event(event: AffectEvent):
                    if websocket in queues:
                        asyncio.create_task(
                            websocket.send_text(event.to_json())
                        )

                self.subscribe(on_event)

                while True:
                    # Keep connection alive
                    await websocket.receive_text()

            except Exception:
                queues.remove(websocket)

        return websocket_endpoint
```

### 3.3 Observability & Tooling Enhancements

#### 3.3.1 Metrics Collection

**Problem:** No built-in metrics for monitoring and alerting.

**Solution:** Optional metrics collector with Prometheus export.

```python
# nima_core/observability/metrics.py (new module)

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class EmotionEvent:
    """Record of an emotion processing event."""
    identity: str
    input_affects: Dict[str, float]
    intensity: float
    resulting_dominant: str
    processing_time_ms: float
    timestamp: float

class AffectMetrics:
    """
    Collects and manages metrics for affect system monitoring.

    Metrics collected:
    - Processing latency (p50, p95, p99)
    - Emotion transition rates
    - Dominant affect distribution
    - State change frequency
    - Error rates
    """

    def __init__(self, retention_hours: float = 168):  # 1 week
        self.retention_hours = retention_hours
        self._metrics: List[MetricPoint] = []
        self._events: List[EmotionEvent] = []
        self._counters: Dict[str, float] = {}

    def record_processing_time(
        self,
        identity: str,
        duration_ms: float
    ) -> None:
        """Record emotion processing duration."""
        self._metrics.append(MetricPoint(
            name="processing_time_ms",
            value=duration_ms,
            timestamp=time.time(),
            tags={"identity": identity}
        ))
        self._prune()

    def record_emotion_transition(
        self,
        identity: str,
        from_affect: str,
        to_affect: str
    ) -> None:
        """Record a transition in dominant affect."""
        self._counters[f"transition_{from_affect}_to_{to_affect}"] = \
            self._counters.get(f"transition_{from_affect}_to_{to_affect}", 0) + 1

    def get_percentiles(
        self,
        metric_name: str,
        percentiles: List[float] = [50, 95, 99]
    ) -> Dict[float, float]:
        """Calculate percentiles for a metric."""
        values = [
            m.value for m in self._metrics
            if m.name == metric_name
        ]
        if not values:
            return {}

        values.sort()
        return {
            p: values[int(len(values) * p / 100)] for p in percentiles
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        # Processing time histogram
        pt_values = [m.value for m in self._metrics if m.name == "processing_time_ms"]
        if pt_values:
            lines.append(f"# HELP nima_processing_time_ms Emotion processing latency")
            lines.append(f"# TYPE nima_processing_time_ms gauge")
            lines.append(f"nima_processing_time_ms {sum(pt_values)/len(pt_values):.2f}")

        # Transition counters
        for key, value in self._counters.items():
            lines.append(f"# TYPE nima_transition_{key} counter")
            lines.append(f"nima_transition_{key} {value}")

        return "\n".join(lines)

    def _prune(self) -> None:
        """Remove old metrics beyond retention period."""
        cutoff = time.time() - (self.retention_hours * 3600)
        self._metrics = [m for m in self._metrics if m.timestamp > cutoff]
        self._events = [e for e in self._events if e.timestamp > cutoff]
```

#### 3.3.2 Visualization Tools

**Problem:** No built-in visualization for affect evolution.

**Solution:** Optional visualization module with ASCII charts and HTML export.

```python
# nima_core/observability/visualization.py (new module)

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

class AffectVisualizer:
    """
    Visualization tools for affect state history.

    Provides:
    - ASCII timeline charts
    - HTML interactive charts
    - Affect correlation heatmaps
    - Profile comparison charts
    """

    def __init__(self, system: 'DynamicAffectSystem'):
        self.system = system

    def ascii_timeline(
        self,
        duration_hours: float = 24,
        width: int = 80,
        height: int = 10
    ) -> str:
        """Generate ASCII chart of affect evolution over time."""
        if not hasattr(self.system, 'history') or self.system.history is None:
            return "History not enabled"

        timeline = self.system.history.get_timeline(duration_hours)
        if len(timeline) < 2:
            return "Insufficient data for timeline"

        lines = []
        lines.append(f"Affect Timeline - Last {duration_hours}h")
        lines.append("=" * width)

        # Create chart for each affect
        for affect in AFFECTS:
            idx = AFFECT_INDEX[affect]
            values = [s.values[idx] for s in timeline]

            # Normalize to chart height
            chart = self._ascii_bar(values, width, height)
            lines.append(f"\n{affect:6} |{chart}")

        return "\n".join(lines)

    def _ascii_bar(
        self,
        values: List[float],
        width: int,
        height: int
    ) -> str:
        """Create ASCII bar chart from values."""
        if not values:
            return ""

        # Downsample to fit width
        step = max(1, len(values) // width)
        sampled = values[::step][:width]

        bars = []
        for v in sampled:
            bar_height = int(v * height)
            bar = "█" * bar_height + "░" * (height - bar_height)
            bars.append(bar[-height:])

        # Transpose to show time horizontally
        result = []
        for row in range(height):
            result.append("".join(b[row] if len(b) > row else " " for b in bars))

        return "\n       |".join(result[::-1])

    def export_html_dashboard(
        self,
        duration_hours: float = 24,
        output_path: Optional[str] = None
    ) -> str:
        """
        Export interactive HTML dashboard.

        Uses Chart.js for interactive visualization.
        """
        if not hasattr(self.system, 'history') or self.system.history is None:
            raise ValueError("History not enabled")

        timeline = self.system.history.get_timeline(duration_hours)

        # Prepare data for Chart.js
        timestamps = [datetime.fromtimestamp(s.timestamp).isoformat() for s in timeline]

        datasets = []
        colors = {
            "SEEKING": "#4CAF50", "FEAR": "#F44336", "RAGE": "#FF5722",
            "LUST": "#E91E63", "CARE": "#2196F3", "PANIC": "#9C27B0",
            "PLAY": "#FF9800"
        }

        for affect, color in colors.items():
            idx = AFFECT_INDEX[affect]
            values = [s.values[idx] for s in timeline]
            datasets.append({
                "label": affect,
                "data": values,
                "borderColor": color,
                "backgroundColor": color + "20",
                "fill": False,
                "tension": 0.4
            })

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NIMA-Core Dashboard - {self.system.identity_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: system-ui; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NIMA-Core Dashboard</h1>
        <div class="card">
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="dominant">{self.system.current.dominant()[0]}</div>
                    <div class="stat-label">Dominant Affect</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="deviation">{self.system.current.deviation(self.system.baseline):.2f}</div>
                    <div class="stat-label">Baseline Deviation</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="snapshots">{len(timeline)}</div>
                    <div class="stat-label">Snapshots</div>
                </div>
            </div>
        </div>
        <div class="card">
            <h2>Affect Timeline ({duration_hours}h)</h2>
            <canvas id="affectChart"></canvas>
        </div>
    </div>
    <script>
        new Chart(document.getElementById('affectChart'), {{
            type: 'line',
            data: {{
                labels: {timestamps},
                datasets: {datasets}
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{ min: 0, max: 1 }},
                    x: {{ ticks: {{ maxTicksLimit: 20 }}} }}
                }},
                interaction: {{ intersect: false, mode: 'index' }}
            }}
        }});
    </script>
</body>
</html>
        """

        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)

        return html
```

#### 3.3.3 Debug Tracing

**Problem:** Limited debugging support for emotion flow.

**Solution:** Optional debug tracer with configurable verbosity.

```python
# nima_core/observability/tracing.py (new module)

import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager

class AffectTraceLogger:
    """
    Detailed tracing of affect system operations.

    Provides visibility into:
    - Input processing steps
    - Baseline modifications
    - Cross-affect interactions
    - Decay calculations
    - State transitions
    """

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        level: int = logging.DEBUG
    ):
        self.logger = logger or logging.getLogger("nima.trace")
        self.level = level
        self._enabled = True

    @contextmanager
    def trace_operation(self, operation: str, **context):
        """Context manager for tracing an operation."""
        if not self._enabled:
            yield
            return

        self.logger.log(self.level, f"[ENTER] {operation}", extra=context)
        start = time.time()

        try:
            yield
        finally:
            duration = (time.time() - start) * 1000
            self.logger.log(
                self.level,
                f"[EXIT] {operation} ({duration:.2f}ms)",
                extra=context
            )

    def log_input_processing(
        self,
        identity: str,
        input_affects: Dict[str, float],
        intensity: float,
        current_state: np.ndarray,
        result_state: np.ndarray
    ) -> None:
        """Log details of input processing."""
        self.logger.log(
            self.level,
            f"[INPUT] {identity} processed input",
            extra={
                "identity": identity,
                "input_affects": input_affects,
                "intensity": intensity,
                "previous_dominant": self._get_dominant_name(current_state),
                "new_dominant": self._get_dominant_name(result_state),
                "state_delta": (result_state - current_state).tolist()
            }
        )

    def log_decay(
        self,
        identity: str,
        hours_elapsed: float,
        deviation_before: float,
        deviation_after: float
    ) -> None:
        """Log temporal decay operation."""
        self.logger.log(
            self.level,
            f"[DECAY] {identity} decayed over {hours_elapsed:.2f}h",
            extra={
                "identity": identity,
                "hours_elapsed": hours_elapsed,
                "deviation_before": deviation_before,
                "deviation_after": deviation_after
            }
        )

    def log_cross_affect(
        self,
        source_affect: str,
        source_intensity: float,
        target_affect: str,
        delta: float
    ) -> None:
        """Log cross-affect interaction."""
        self.logger.log(
            self.level,
            f"[INTERACTION] {source_affect} ({source_intensity:.2f}) → {target_affect} ({delta:+.2f})",
            extra={
                "source_affect": source_affect,
                "source_intensity": source_intensity,
                "target_affect": target_affect,
                "delta": delta
            }
        )

    @staticmethod
    def _get_dominant_name(state: np.ndarray) -> str:
        """Get dominant affect name from state vector."""
        idx = int(np.argmax(state))
        return AFFECTS[idx]
```

---

## Part IV: Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Focus:** Code quality fixes and testing infrastructure

| Task | Module | Priority | Effort |
|------|--------|----------|--------|
| Add comprehensive test suite | `tests/` | High | 5 days |
| Fix singleton pattern fragility | `dynamic_affect.py` | High | 1 day |
| Add input validation decorators | `dynamic_affect.py` | High | 2 days |
| Performance benchmarks | `benchmarks/` | Medium | 2 days |
| CI/CD pipeline setup | `.github/workflows/` | Medium | 1 day |

**Deliverables:**
- 80%+ test coverage
- Benchmark baseline
- Passing CI checks

### Phase 2: Core Enhancements (Weeks 3-4)

**Focus:** Profile blending and context awareness

| Task | Module | Priority | Effort |
|------|--------|----------|--------|
| Profile blending API | `personality_profiles.py` | High | 2 days |
| Context-aware module | `context_aware.py` (new) | High | 3 days |
| Configurable constants | `dynamic_affect.py` | Medium | 1 day |
| Documentation updates | `docs/` | Medium | 2 days |

**Deliverables:**
- `blend_profiles()` function
- `ContextAwareModule` class
- Environment variable configuration

### Phase 3: Integration Layer (Weeks 5-7)

**Focus:** REST API and persistence

| Task | Module | Priority | Effort |
|------|--------|----------|--------|
| REST API server | `api/rest.py` (new) | High | 3 days |
| Database persistence interface | `persistence/` (new) | High | 4 days |
| PostgreSQL implementation | `persistence/postgres.py` | Medium | 2 days |
| Event streaming module | `streaming/` (new) | Medium | 3 days |

**Deliverables:**
- FastAPI-based REST server
- Postgres persistence option
- WebSocket/Redis streaming

### Phase 4: Observability (Weeks 8-9)

**Focus:** Metrics, visualization, tracing

| Task | Module | Priority | Effort |
|------|--------|----------|--------|
| Metrics collection | `observability/metrics.py` | High | 3 days |
| Prometheus exporter | `observability/metrics.py` | High | 1 day |
| Visualization tools | `observability/visualization.py` | High | 3 days |
| Debug tracer | `observability/tracing.py` | Medium | 2 days |

**Deliverables:**
- Metrics dashboard
- HTML export
- Debug logging

### Phase 5: Advanced Features (Weeks 10-12)

**Focus:** Multi-agent and circadian modules

| Task | Module | Priority | Effort |
|------|--------|----------|--------|
| Multi-agent interaction | `multi_agent_interaction.py` (new) | Medium | 5 days |
| Circadian rhythms | `circadian.py` (new) | Low | 2 days |
| Integration tests | `tests/integration/` | High | 3 days |

**Deliverables:**
- Multi-agent emotional contagion
- Time-of-day modulation
- Full integration test suite

---

## Part V: Testing Strategy

### 5.1 Unit Tests

```python
# tests/test_profile_blending.py
def test_blend_profiles_equal_ratio():
    """Blending with 0.5 ratio should average baselines."""
    p1 = PersonalityProfile(name="p1", baseline=np.array([0.2] * 7))
    p2 = PersonalityProfile(name="p2", baseline=np.array([0.8] * 7))
    blended = blend_profiles(p1, p2, 0.5)
    expected = np.array([0.5] * 7)
    assert np.allclose(blended.baseline, expected)

def test_context_aware_sentiment_modifier():
    """Declining sentiment should increase CARE sensitivity."""
    module = ContextAwareModule()
    context = ConversationContext(
        turns_count=5,
        user_sentiment_trend="declining",
        topic_continuity=0.5,
        time_since_last_exchange=100,
        recent_affects=["CARE", "CARE"]
    )
    detected = {"CARE": 0.5, "FEAR": 0.3}
    enhanced = module.enhance_detection(detected, context)
    assert enhanced["CARE"] > 0.5  # Should be amplified
```

### 5.2 Integration Tests

```python
# tests/integration/test_rest_api.py
def test_rest_api_full_flow():
    """Test REST API state query and input submission."""
    api = NimaRestAPI(host="localhost", port=8081)
    api.start_in_background()
    time.sleep(1)  # Let server start

    # Create system
    system = get_affect_system("test_rest")
    initial = system.current.dominant()[0]

    # Submit input via API
    response = requests.post(
        "http://localhost:8081/affect/test_rest/input",
        json={"affects": {"RAGE": 0.8}, "intensity": 0.7}
    )

    assert response.status_code == 200

    # Verify state changed
    state_response = requests.get("http://localhost:8081/affect/test_rest/state")
    assert state_response.json()["dominant"] == "RAGE"
```

### 5.3 Performance Tests

```python
# benchmarks/test_performance.py
def test_emotion_processing_throughput():
    """Benchmark emotion processing throughput."""
    system = get_affect_system("bench")
    iterations = 10000

    start = time.time()
    for i in range(iterations):
        system.process_input({"PLAY": 0.5})
    duration = time.time() - start

    throughput = iterations / duration
    assert throughput > 1000  # Should handle >1000 ops/sec

    print(f"Throughput: {throughput:.0f} ops/sec")
```

---

## Part VI: API Changes Summary

### 6.1 Backward Compatibility

**All proposed changes are backward compatible.** Existing code will continue to work without modification.

### 6.2 New Public APIs

```python
# Profile Management
def blend_profiles(
    profile1: Union[str, PersonalityProfile],
    profile2: Union[str, PersonalityProfile],
    ratio: float = 0.5,
    name: Optional[str] = None
) -> PersonalityProfile

# Context-Aware Processing
class ContextAwareModule:
    def enhance_detection(
        self,
        detected: Dict[str, float],
        context: ConversationContext
    ) -> Dict[str, float]

# Multi-Agent
class MultiAgentAffectSystem:
    def register_agent(agent_id: str, system: DynamicAffectSystem)
    def set_influence(from_agent: str, to_agent: str, strength: float)
    def process_interaction(agent_a: str, agent_b: str, interaction_type: str)

# REST API
class NimaRestAPI:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080)
    def start() -> None
    def start_in_background() -> None

# Persistence
class AffectPersistence(ABC):
    def save_state(identity: str, state: np.ndarray, timestamp: float, source: str)
    def load_state(identity: str) -> Optional[Dict]

class PostgresPersistence(AffectPersistence):
    def __init__(self, connection_string: str)

# Metrics
class AffectMetrics:
    def record_processing_time(identity: str, duration_ms: float)
    def record_emotion_transition(identity: str, from_affect: str, to_affect: str)
    def export_prometheus() -> str

# Visualization
class AffectVisualizer:
    def ascii_timeline(duration_hours: float = 24) -> str
    def export_html_dashboard(duration_hours: float = 24, output_path: str) -> str
```

---

## Part VII: Migration Guide

### 7.1 Version Path

- **v2.1.0**: Profile blending + context awareness
- **v2.2.0**: REST API + persistence layer
- **v2.3.0**: Metrics + visualization
- **v2.4.0**: Multi-agent + circadian modules

### 7.2 Upgrade Steps

```python
# v2.0 → v2.1 (Profile Blending)
from nima_core.cognition.personality_profiles import blend_profiles

# Create custom personality
custom = blend_profiles("guardian", "explorer", ratio=0.3)

# v2.1 → v2.2 (REST API)
from nima_core.api.rest import NimaRestAPI

api = NimaRestAPI(port=8080)
api.start_in_background()

# v2.2 → v2.3 (Metrics)
from nima_core.observability.metrics import AffectMetrics

system = get_affect_system("my-agent")
system.metrics = AffectMetrics()

# v2.3 → v2.4 (Multi-Agent)
from nima_core.cognition.multi_agent_interaction import MultiAgentAffectSystem

multi = MultiAgentAffectSystem()
multi.register_agent("agent1", system1)
multi.register_agent("agent2", system2)
multi.process_interaction("agent1", "agent2", "cooperation")
```

---

## Part VIII: Open Questions

1. **Persistence Priority**: Is PostgreSQL support needed immediately, or is file-based persistence sufficient for now?

2. **Streaming Requirements**: Do you need WebSocket support, or is the REST API polling sufficient for monitoring needs?

3. **Multi-Agent Use Cases**: Are there specific multi-agent scenarios you want to prioritize (competitive, cooperative, hierarchical)?

4. **Circadian Importance**: How important is time-of-day emotional variation for your use cases?

5. **Deployment Model**: Will this run in a single-agent environment, or do you need distributed system support from day one?

---

## Approval Checklist

- [x] Project context explored
- [x] Current state documented
- [x] Enhancement approaches proposed
- [x] Detailed enhancement specifications
- [ ] Implementation timeline approved
- [ ] Open questions resolved
- [ ] Ready to proceed to writing-plans skill
