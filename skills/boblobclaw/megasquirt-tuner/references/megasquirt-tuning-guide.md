# Megasquirt Comprehensive Tuning Guide

## Pre-Tuning Checklist

### Mechanical Verification
- [ ] Engine compression tested and within spec
- [ ] Valve lash adjusted correctly
- [ ] Timing belt/chain properly aligned
- [ ] No vacuum leaks (intake manifold, hoses, PCV)
- [ ] Fuel pressure verified at regulator
- [ ] Fuel filter clean
- [ ] Injectors flowing evenly
- [ ] Spark plugs gapped and in good condition
- [ ] Ignition wires/coil packs functioning
- [ ] All sensors reading correctly

### Electrical Verification
- [ ] Battery fully charged (>12.4V)
- [ ] Alternator charging properly
- [ ] Megasquirt grounds clean and tight
- [ ] Injector harness polarity correct
- [ ] Coil wiring correct
- [ ] Sensor wiring verified with multimeter
- [ ] Wideband O2 powered and heated

### Software Verification
- [ ] INI file matches installed firmware version (no "signature mismatch" errors)
- [ ] TunerStudio project created for correct firmware variant (MS1/Extra, MS2/Extra, MS3)
- [ ] Trigger wheel type and trigger angle configured correctly
- [ ] Tooth logger run and trigger pattern verified (see Trigger Setup section)
- [ ] Output test mode used to verify injector and coil wiring
- [ ] All settings burned to flash (Ctrl+B) before disconnecting

## Trigger Setup and Verification

### Trigger Wheel Configuration
The trigger/wheel decoder setup is one of the most critical steps — an incorrect configuration means the engine will not start or will misfire.

1. **Identify your trigger wheel type** — common types:
   - Missing-tooth wheels: 36-1, 60-2, 12-1, 24-1
   - OEM patterns: Ford TFI, GM HEI, Nissan CAS, Toyota 24+1, Honda 24+1
   - Distributor: single tooth per revolution
2. **Configure in Ignition Settings → Trigger Wizard**:
   - Select wheel type
   - Set number of teeth and missing teeth
   - Choose trigger edge (rising or falling — depends on sensor type: VR vs. Hall)
   - Set trigger angle (degrees BTDC for the reference tooth)
3. **Secondary trigger (cam sensor)** — required for sequential injection/ignition:
   - Configure cam sensor type and edge
   - Set cam trigger angle
4. **Noise filtering** — if using VR (variable reluctor) sensors:
   - Enable noise filtering on primary and/or secondary tach inputs
   - Increase filtering if experiencing false triggers at low RPM

### Trigger Verification with Tooth Logger
**Always run the tooth logger before first start:**
1. Open Diagnostics → Tooth Logger in TunerStudio
2. Crank the engine (fuel/ignition can be disabled for safety)
3. Capture the tooth pattern
4. Verify:
   - Correct number of teeth per revolution
   - Missing tooth gap is clearly visible and in the right position
   - No spurious extra teeth (indicates noise or wiring issues)
   - Tooth spacing is even (worn reluctor wheels show uneven spacing)
5. If the pattern looks wrong, check:
   - Sensor air gap (VR sensors: typically 0.5-1.0mm)
   - Wiring polarity (VR sensors are polarity-sensitive)
   - Shield grounding
   - Noise filtering settings

### Composite Logger for Cam Sync
If using sequential injection/ignition:
1. Open Diagnostics → Composite Logger
2. Crank or run the engine
3. Verify cam signal appears at the correct position relative to crank signal
4. If cam sync is lost intermittently, check cam sensor wiring and air gap

## Initial Startup Procedure

### First Start Preparation
1. Load conservative base tune
2. Set required fuel for your injectors
3. Set cranking pulse widths (typically 2-5ms)
4. Verify timing with light before cranking
5. Prime fuel system, check for leaks
6. Have fire extinguisher ready

### Cranking Settings
**Cranking RPM Threshold**: 300 RPM (below this = cranking mode)

**Cranking Pulse Widths:**
- Cold (-20°C): 8-15ms
- Warm (20°C): 4-8ms
- Hot (70°C): 2-4ms
- Adjust based on injector size and engine needs

**Prime Pulse:**
- 1-3ms at key-on
- Helps first start
- Don't flood engine

### Post-Start Verification
1. Oil pressure builds within 5 seconds
2. No unusual noises
3. Coolant circulating
4. AFR gauge responding
5. All sensors reading reasonable values

## Idle Tuning Procedure

### Step 1: Mechanical Idle
1. Disconnect idle valve or set to manual control at 0%
2. Adjust throttle stop screw for 400-500 RPM (below target)
3. This ensures throttle plate isn't controlling idle

### Step 2: Minimum Airflow
1. Enable idle valve
2. Set closed-loop idle control
3. Target 50-100 RPM below desired idle
4. Adjust minimum duty for stability

### Step 3: VE Table at Idle
1. Target AFR: 13.5-14.0
2. Adjust VE until AFR matches target
3. EGO correction should be near 0%
4. Note: Some engines prefer richer idle (13.0-13.5)

### Step 4: Idle Advance
1. Start with 15-20° BTDC
2. More advance can improve stability
3. Too much advance causes roughness
4. Typical range: 15-25°

### Step 5: Idle Valve Tuning
- **Closed Position**: PWM for hot idle (20-40%)
- **Open Position**: PWM for cold start (60-80%)
- **Cranking Position**: PWM during start (50-70%)
- Adjust curve between these points

### Step 6: Closed-Loop PID
Start conservative:
- **P (Proportional)**: 20-50
- **I (Integral)**: 10-30
- **D (Derivative)**: 0-10

Increase P until oscillation, then back off.
Add I to eliminate steady-state error.
Use minimal D (can cause instability).

## Fuel Table Tuning

### Tuning Order Priority
1. Idle region (600-1200 RPM, 30-50kPa)
2. Light cruise (1500-2500 RPM, 40-60kPa)
3. Part throttle acceleration
4. Highway cruise
5. WOT tuning
6. High RPM/load

### Steady-State Tuning Method
1. Warm engine fully (CLT > 80°C)
2. Select fixed gear (dyno or long straight road)
3. Hold RPM/load cell for 3-5 seconds
4. Allow EGO correction to stabilize
5. Note correction percentage
6. Adjust VE by inverse of correction

Example:
- Current VE: 60
- EGO correction: +12%
- New VE: 60 × 1.12 = 67

### AFR-Based Calculation
```
New VE = Current VE × (Target AFR / Measured AFR)
```

Example:
- Target: 14.0
- Measured: 12.5 (rich)
- Current VE: 70
- New VE: 70 × (14.0/12.5) = 78.4

### Transition Tuning
Cells between steady-state points:
- Interpolate between tuned cells
- Test during actual driving
- Fine-tune if transition feels rough

### Injection Timing (MS2/Extra)
End-of-injection angle affects fuel atomization and mixture preparation:
- **Port injection**: Aim to finish injection while the intake valve is closed (fuel pools on back of valve)
- **Typical starting point**: 350-400° BTDC (injection ends before intake valve opens)
- MS2/Extra supports up to 3 injection timing tables vs RPM/load
- Fine-tuning injection timing can improve idle quality, emissions, and transient response

### Fuel Trim Tables (MS2/Extra)
Per-cylinder or per-bank fuel trims for correcting individual cylinder variations:
- Up to 4 fuel trim tables available
- Apply percentage corrections on top of the main VE table
- **Use cases**: Unequal-length intake runners, cylinder-to-cylinder variation, bank-to-bank balance
- Requires individual cylinder AFR measurement (per-cylinder EGT or individual runner wideband)

## Ignition Timing Tuning

### Base Timing Verification
1. Disconnect injector connector (prevents starting)
2. Set fixed timing in software (usually 10° or 15°)
3. Crank engine with timing light
4. Verify light shows set advance
5. Adjust trigger angle if offset
6. Re-enable variable timing

### Conservative Starting Point
| RPM \ kPa | 20 | 40 | 60 | 80 | 100 |
|-----------|----|----|----|----|-----|
| 800       | 20 | 18 | 15 | 12 | 10  |
| 1500      | 35 | 30 | 25 | 20 | 15  |
| 2500      | 40 | 35 | 30 | 25 | 20  |
| 4000      | 42 | 38 | 32 | 28 | 22  |
| 6000      | 45 | 40 | 35 | 30 | 25  |

### Tuning for Power
1. Start with conservative map
2. Increase timing 2° at a time in target cells
3. Dyno or acceleration test each change
4. Stop when no more power gained
5. Back off 2° for safety margin

### Knock Detection
Listen for:
- Pinging/rattling under load
- Loss of power
- Elevated EGT

If knock detected:
- Reduce timing immediately
- Add fuel in affected area
- Check for hot spots, carbon buildup
- Verify fuel quality (octane rating)

## Acceleration Enrichment

### TPS-Based Enrichment
**When to use**: Most applications with cable throttle

**Settings:**
- **Threshold**: 5-10%/second TPS rate
- **Enrichment**: 10-25% added fuel
- **Decay**: 0.5-1.5 seconds

**Tuning Procedure:**
1. Start with conservative settings
2. Perform tip-in from steady cruise
3. Watch AFR: Should briefly richen (0.5-1.0 lambda)
4. If lean spike (>1.1 lambda), increase enrichment
5. If no lean spike but bog, reduce enrichment
6. Too rich causes hesitation and black smoke

### MAP-Based Enrichment
**When to use**: Individual throttle bodies, ITBs

**Settings:**
- **Threshold**: 20-50 kPa/second
- **Enrichment**: Scales with MAPdot

**Tuning similar to TPS-based**

### Cold Accel Multiplier
Increases enrichment when engine is cold:
- -20°C: 2.0-3.0×
- 0°C: 1.5-2.0×
- 20°C: 1.2-1.5×
- 60°C+: 1.0× (no extra)

### Decay Rate
- Too fast: Bog returns after initial tip-in
- Too slow: Rich surge continues
- Target: Just covers the transient event

### Enhanced Accel Enrichment (EAE) — Recommended for MS2/Extra

EAE uses a **wall-wetting fuel model** that's more accurate than basic TPSdot/MAPdot enrichment. It models fuel film behavior on intake port walls.

**How it works:**
- A portion of injected fuel lands on intake port walls ("wall film") instead of entering the cylinder
- When throttle opens, more fuel is needed to both fill the cylinder and build up the wall film
- When throttle closes, fuel evaporating off the wall film provides extra fuel (contributing to rich decel)
- EAE calculates the correct transient fuel based on this model

**Key EAE Parameters:**
- **Wall wetting factor (tau)**: How much fuel sticks to the wall (higher = more wall film)
- **Evaporation factor (beta)**: How fast fuel evaporates off the wall (higher = faster)
- **RPM correction**: Wall wetting changes with airflow velocity at different RPMs
- **CLT correction**: Cold walls absorb more fuel — EAE increases enrichment when cold

**Tuning EAE:**
1. Enable EAE in Accel Enrich settings (replaces basic AE)
2. Start with default coefficients
3. Perform tip-in tests from steady cruise, monitoring AFR
4. If lean on tip-in: increase wall wetting factor or reduce evaporation factor
5. If rich on tip-in: decrease wall wetting factor or increase evaporation factor
6. Tune lag compensation for the delay between injection and combustion
7. Adjust RPM and CLT correction curves as needed
8. Test across the full RPM and temperature range

## Warmup Enrichment

### Afterstart Enrichment
- **Duration**: 50-200 engine cycles
- **Initial**: 20-40% extra fuel
- **Taper**: Linear to 0% over duration

### Warmup Enrichment Curve
| Coolant Temp | Enrichment |
|--------------|-----------|
| -40°C        | 180%      |
| -20°C        | 160%      |
| 0°C          | 140%      |
| 20°C         | 120%      |
| 40°C         | 110%      |
| 70°C         | 100%      |
| 80°C+        | 100%      |

### Tuning Warmup
1. Cold start engine
2. Monitor AFR during warm-up
3. Should be slightly rich (12-13 AFR)
4. Smoothly transition to 14.7
5. Adjust curve if too lean or rich at specific temps

## Deceleration Fuel Cut (DFCO)

### Purpose
- Save fuel during deceleration
- Reduce emissions
- Prevent afterfire in exhaust

### Settings
- **TPS Threshold**: <5-10%
- **RPM Threshold**: 200-500 RPM above idle
- **MAP Threshold**: <30-40 kPa (high vacuum)

### Re-Enable Conditions
- TPS rises above threshold
- RPM drops to threshold
- MAP rises above threshold

### Tuning
- Enable if popping/backfiring on decel
- Disable if causing hesitation when returning to throttle
- Add taper for smooth re-enable

## Boost Control (Turbo/Supercharged)

### Open Loop Boost Control
1. Create duty cycle table vs RPM
2. Start conservative (low duty = low boost)
3. Increase duty in 5% increments
4. Target boost level at each RPM
5. Log boost vs duty for each gear

### Closed Loop Boost Control (if available)
**PID Tuning:**
Note: PID values are firmware-specific and integer-scaled in MS2/Extra. Start conservative and adjust incrementally:
- Start with low P gain, zero I and D
- Increase P until boost begins to oscillate around the target, then reduce P by ~30%
- Add small I gain to eliminate steady-state offset (boost sitting above or below target)
- Use minimal or zero D — derivative gain can cause erratic solenoid behavior
- Monitor actual vs. target boost in datalogs to evaluate PID response
- Tuning PID on a dyno under controlled conditions is strongly recommended

**Target Boost Table:**
- Low RPM: Minimize boost (spool)
- Mid RPM: Target boost level
- High RPM: May taper to prevent over-speed

### Overboost Protection
- Set fuel/ignition cut above target
- Margin: 1-3 PSI above target boost
- Prevents engine damage

## Launch Control

### Settings
- **Launch RPM**: 4000-6000 (engine dependent)
- **Retard Timing**: 0-10° BTDC during launch
- **Fuel/Ignition Cut**: Hard limit method

### Flat Shift
- Maintain throttle during shifts
- Brief cut (100-200ms) at shift point
- Retains boost between gears

## Troubleshooting Common Issues

### Hard Starting
- Cranking PW too lean/rich
- No spark during cranking
- Trigger issue (no RPM signal)
- Fuel pump not priming

### Idle Instability
- Vacuum leaks
- Incorrect TPS calibration
- EGO correction too aggressive
- Ignition timing fluctuating
- Mechanical issues (valves, compression)

### Hesitation on Acceleration
- Lean condition (insufficient accel enrichment)
- Ignition timing too retarded
- Fuel pressure dropping
- Restricted fuel filter

### Surging at Cruise
- EGO correction oscillating
- VE table cells uneven
- MAP signal noisy
- O2 sensor slow response

### Rich at Light Load
- VE table too high
- Fuel pressure too high
- Leaking injector
- Incorrect required fuel setting

### Lean at WOT
- VE table too low
- Fuel pump insufficient
- Injectors at max duty cycle
- Fuel pressure dropping under load

### Detonation/Knock
- Timing too advanced
- Fuel octane insufficient
- Lean mixture
- Hot intake air (IAT high)
- Carbon buildup
- Incorrect spark plugs

## Safety and Monitoring

### Critical Limits
| Parameter | Warning | Danger |
|-----------|---------|--------|
| Coolant Temp | 100°C | 110°C+ |
| AFR at WOT | 12.0-13.0 | <11.8 or >14.0 |
| EGT | 800°C | 900°C+ |
| Injector DC | 80% | 90%+ |
| Knock | Any | Persistent |

### Data Logging Strategy
**Always log:**
- RPM, MAP, TPS
- AFR (wideband)
- CLT, IAT
- Spark advance
- Injector PW
- Battery voltage

**Add for specific issues:**
- EGO correction (tuning)
- Knock retard (detonation)
- Boost pressure (turbo)
- Oil pressure (engine health)

### Burning Changes
- Always **burn changes to flash** (Ctrl+B) after completing a tuning session
- VE, Spark, and AFR tables support live tuning (changes apply immediately to RAM) but must still be burned to persist
- All other settings (engine constants, sensor config, idle control, etc.) require a burn before they take effect
- Flash supports ~100,000 burn cycles — batch your changes rather than burning after every cell edit

### Tune Versioning
Save tune with descriptive names:
- `baseline_2024-01-15.msq`
- `idle_tuned_2024-01-20.msq`
- `cruise_complete_2024-02-01.msq`
- `final_v1_2024-02-10.msq`

Include notes about changes in each version.

## Advanced Topics

### Flex Fuel (Ethanol)
- Requires ethanol content sensor
- Blends fuel/spark tables based on ethanol %
- E85 requires ~30% more fuel
- Can retard timing for E85 (slower burn)

### Sequential Injection
- Requires cam position sensor
- More precise fuel delivery
- Better idle and emissions
- Fuel trim per cylinder possible

### Individual Cylinder Tuning
- Requires EGT per cylinder or wideband per runner
- Trim fuel/spark for cylinder variations
- Useful for unequal runner lengths

### Traction Control
- Based on RPM rise rate
- Cuts fuel/spark when wheelspin detected
- Adjustable sensitivity

### Variable Cam Timing
- Control intake/exhaust cam position
- Separate tables for cam advance
- Tuning for low-end torque vs high RPM power

### Nitrous Control (MS2/Extra)
- Supports Stage 1 and Stage 2 nitrous systems
- **Activation conditions**: Minimum RPM, minimum TPS (WOT only), minimum coolant temp
- **Fuel enrichment**: Additional injector PW to compensate for added oxygen — calculate from nitrous jet size and fuel jet size
- **Timing retard**: Retard ignition during nitrous activation (typically 2-4° per 50hp shot)
- **Safety**: Configure overboost cut, lean cut, and RPM limit during nitrous operation
- Configure via Boost/Advanced → Nitrous in TunerStudio

### Table Switching
- Switch between up to 3 fuel tables and 3 spark tables based on external conditions
- **Switching inputs**: Digital input pin, CAN message, or internal condition
- **Use cases**:
  - Race fuel vs. pump gas (different octane → different timing)
  - Nitrous on/off (richer targets and less timing when nitrous active)
  - Traction control intervention (reduced torque table)
  - Wet vs. dry conditions
- Configure via Boost/Advanced → Table Switching Control

### Programmable On/Off Outputs
- Configure spare ECU output pins to activate based on conditions
- **Available conditions**: RPM range, TPS threshold, MAP range, coolant temp, timer-based
- **Common uses**:
  - Cooling fan relay (activate above coolant temp threshold)
  - Shift light (activate at target RPM)
  - Water/methanol injection (activate above boost threshold)
  - Warning light (lean AFR, high EGT, overboost)
  - Nitrous solenoid enable
- Configure via Boost/Advanced → Programmable On/Off Outputs
