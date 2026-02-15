# Dynamic Affect System: Technical Deep Dive

## Overview

The Dynamic Affect System is a stateful emotional engine based on Jaak Panksepp's Affective Neuroscience. Unlike discrete sentiment analysis (which labels a single text as "Positive" or "Negative"), this system models emotion as a **continuous, high-dimensional vector** that evolves over time.

It has:
1. **Inertia:** It takes energy to move it.
2. **Momentum:** Once moving, it keeps moving.
3. **Gravity:** It naturally pulls back to a "baseline" personality.

## Mathematical Model

The state is a 7-dimensional vector $\mathbf{v} \in [0, 1]^7$.

The affects are:
$A = \{ \text{SEEKING, RAGE, FEAR, LUST, CARE, PANIC, PLAY} \}$

### State Update Equation

When new input $\mathbf{i}$ (input vector) arrives with blend strength $\alpha$ (typically 0.25):

$$
\mathbf{v}_{t+1} = \mathbf{v}_t + \alpha (\mathbf{i} - \mathbf{v}_t) + \gamma (\mathbf{b} - \mathbf{v}_t)
$$

Where:
- $\mathbf{v}_t$: Current state vector
- $\mathbf{i}$: Detected emotion vector from input
- $\mathbf{b}$: Baseline (Identity) vector
- $\alpha$: Blend strength (reactivity)
- $\gamma$: Baseline pull (gravity, typically 0.02 per step)

This creates a "rubber band" effect. You can stretch the agent into RAGE, but as soon as the input stops, it snaps back to its baseline (e.g., CARE for a Guardian).

### Temporal Decay

Time is a first-class citizen. If the agent is idle, the state decays exponentially toward baseline.

$$
\mathbf{v}_{t+hours} = \mathbf{b} + (\mathbf{v}_t - \mathbf{b}) \cdot e^{-\lambda t}
$$

Where $\lambda$ is the decay rate (default 0.1/hour).
This means an agent left in a state of RAGE will "cool off" over a few hours.

## Persistence & File Format

State is stored in JSON format at `~/.nima/affect/affect_state_{identity}.json` (or `NIMA_HOME`).

```json
{
  "version": 1,
  "current": {
    "values": [0.6, 0.1, 0.1, 0.1, 0.5, 0.1, 0.4],
    "timestamp": 1707849200.5,
    "source": "blended",
    "named": {
      "SEEKING": 0.6,
      "RAGE": 0.1,
      ...
    }
  },
  "baseline": { ... },
  "identity_name": "MyBot"
}
```

### Concurrency & Atomic Writes
To prevent corruption when multiple processes (e.g., sub-agents) access the state:
1. **Reads:** Use shared file locks (`fcntl.LOCK_SH` in Python).
2. **Writes:** Atomic strategy.
   - Write to `filename.tmp`
   - `fsync` to disk
   - `rename` (atomic OS operation) to `filename.json`

## Python/JS Consistency

The core logic exists in both Python (`nima_core`) and JavaScript (`openclaw_plugin`).

- **Emotion Mapping:** Both use the same lexicon keys and weights.
- **Math:** The blend and decay formulas are identical.
- **Archetypes:** The `ARCHETYPES` constant is synchronized.

This allows a hybrid setup where:
1. OpenClaw (Node.js) handles real-time chat updates.
2. Python background tasks (dreaming, memory consolidation) read the *same* state file to understand the agent's mood.

## Environment Variables

- `NIMA_HOME`: Overrides the default `~/.nima` storage location. Useful for containers or testing.

## Integration with LLMs

The `ResponseModulator` converts the numeric vector into semantic instructions.

**Vector:** `SEEKING=0.9, RAGE=0.1`
**Prompt:** `Tone: Intensely curious. Style: Expansive. Embrace: Questions, exploration.`

This bridge allows the mathematical model to influence the probabilistic generation of the LLM without requiring fine-tuning.
