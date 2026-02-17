---
name: megasquirt-tuner
description: Megasquirt ECU tuning and calibration using TunerStudio. Use when working with Megasquirt engine management systems for: (1) VE table tuning and fuel map optimization, (2) Ignition timing maps and spark advance, (3) Idle control and warmup enrichment, (4) AFR target tuning and closed-loop feedback, (5) Sensor calibration (TPS, MAP, CLT, IAT, O2), (6) Acceleration enrichment and deceleration fuel cut, (7) Boost control and launch control setup, (8) Datalog analysis and troubleshooting, (9) Base engine configuration and injector setup, (10) Any Megasquirt/TunerStudio ECU tuning tasks.
---

# Megasquirt ECU Tuning with TunerStudio

Guidance for tuning Megasquirt engine management systems using TunerStudio software.

## Core Concepts

### Required Fuel Equation
Megasquirt calculates fuel delivery using:
```
Pulse Width = Required Fuel × VE% × MAP × AFR Target Correction × Air Density × Warmup × Accel Enrichment × Other Corrections
```

**Required Fuel** is the base injector pulse width at 100% VE, 100kPa MAP, standard temperature.

### Key Tuning Tables

| Table | Purpose | Typical Resolution |
|-------|---------|-------------------|
| VE Table | Volumetric efficiency vs RPM/MAP | 12×12 (MS2), up to 16×16 (MS3) |
| AFR Target | Desired air-fuel ratio vs RPM/MAP | 12×12 (MS2), up to 16×16 (MS3) |
| Spark Advance | Ignition timing vs RPM/MAP | 12×12 (MS2), up to 16×16 (MS3) |
| Warmup Enrichment | Fuel correction vs coolant temp | 10-20 points |
| TPS-based Accel | Accel enrichment vs TPSdot | 10-20 points |
| MAP-based Accel | Accel enrichment vs MAPdot | 10-20 points |

## Tuning Workflow

### 1. Base Configuration
Before tuning, verify:
- Engine displacement and cylinder count
- Injector flow rate (cc/min or lb/hr)
- Injector staging (simultaneous, alternating, sequential)
- Required Fuel — TunerStudio calculates this automatically from engine constants (displacement, number of injectors, injector flow rate, and divider). Do not hand-calculate; use the firmware's built-in calculation.
- Ignition input/output settings match hardware
- Trigger wheel and ignition mode configured (use the Trigger Wizard for wheel decoder setup)
- INI file matches installed firmware version (mismatch causes connection errors or wrong settings)

### 2. Sensor Calibration
Calibrate sensors before tuning (all under **Tools** menu in TunerStudio):
- **CLT (Coolant Temp)**: Tools → Calibrate Thermistor — select preset (GM, Ford, Bosch) or enter custom resistance pairs
- **IAT (Intake Air Temp)**: Tools → Calibrate Thermistor — same process as CLT
- **TPS**: Tools → Calibrate TPS — sample closed throttle and WOT positions
- **MAP**: Tools → Calibrate MAP/Baro — verify atmospheric reading at key-on; common sensors: MPX4250 (250kPa), MPXH6400 (400kPa)
- **O2 Sensor**: Tools → Calibrate AFR — set wideband controller voltage-to-AFR mapping

### 3. VE Table Tuning (Speed Density)

**Method 1: Wideband O2 Feedback**
1. Enable EGO correction with moderate authority (±15-20%)
2. Set realistic AFR targets
3. Run engine at steady state (fixed RPM/load cell)
4. Allow EGO to correct, note correction percentage
5. Adjust VE by inverse of correction (if +10% correction, increase VE by 10%)
6. Save and move to next cell

**Method 2: Calculate from Measured AFR**
```
New VE = Current VE × (Measured AFR / Target AFR)
```

**Tuning Order:**
1. Start with idle region (600-1000 RPM, 30-50kPa)
2. Light cruise (1500-2500 RPM, 40-60kPa)
3. Part throttle acceleration
4. WOT high load
5. Transition regions

### 4. AFR Target Table

Set targets based on application:

| Condition | Target AFR | Lambda |
|-----------|-----------|--------|
| Idle | 13.5-14.5 | 0.92-0.99 |
| Light Cruise | 14.5-15.5 | 0.99-1.06 |
| Part Throttle | 13.5-14.5 | 0.92-0.99 |
| WOT Naturally Aspirated | 12.5-13.0 | 0.85-0.88 |
| WOT Turbo/Supercharged | 11.8-12.5 | 0.80-0.85 |

### 5. Ignition Timing

**Base Settings:**
- Set cranking advance (typically 10-20° BTDC)
- Set idle advance (typically 15-25° BTDC)
- Build spark table following engine-specific guidelines

**Typical Spark Advance Table (Naturally Aspirated):**
- Low RPM/High Load: 10-20°
- Low RPM/Low Load: 25-35°
- High RPM/High Load: 25-35°
- High RPM/Low Load: 35-45°

**Knock Considerations:**
- Reduce timing 1-2° at a time if knock detected
- Add more fuel in knock-prone areas
- Use knock sensor feedback if available

### 6. Idle Control

**Idle Valve PWM Settings:**
- Closed position: PWM at hot idle (typically 20-40%)
- Open position: PWM for cold start (typically 60-80%)
- Cranking position: PWM during start (typically 50-70%)

**Idle Target RPM Table:**
- Hot: 700-900 RPM
- Cold (0°C): 1200-1500 RPM
- Interpolate between

### 7. Warmup Enrichment

**Afterstart Enrichment:**
- Duration: 30-200 cycles (engine revolutions)
- Amount: 20-40% additional fuel
- Taper to zero over duration

**Warmup Enrichment Curve:**
- -40°C: 150-200%
- 0°C: 120-140%
- 70°C (operating): 100%

### 8. Acceleration Enrichment

**Basic AE (TPS-based):**
- Threshold: 5-10%/sec TPSdot
- Enrichment: 10-30% added fuel
- Decay: 0.5-2 seconds

**Basic AE (MAP-based, for ITBs):**
- Threshold: 10-30 kPa/sec
- Enrichment scales with rate of change

**Enhanced Accel Enrichment (EAE) — Recommended for MS2/Extra:**
- Uses a wall-wetting fuel model instead of simple TPSdot/MAPdot
- Accounts for fuel film on intake walls that absorbs and releases fuel
- EAE coefficients control how much fuel sticks to walls vs. enters cylinder
- Provides smoother transient response than basic AE
- Configure via Accel Enrich → EAE settings; tune lag compensation and RPM/CLT corrections

**Cold Multiplier:**
- Increase accel enrichment when cold (1.5-3× at -20°C)

## Advanced Features

### Boost Control

**Open Loop:**
- Duty cycle table vs RPM/target boost

**Closed Loop (if supported):**
- PID parameters for wastegate control
- Target boost table vs RPM/gear

### Launch Control

- Set RPM limit (typically 4000-6000 RPM)
- Configure retard timing during launch (0-10° BTDC)
- Set fuel/ignition cut method

### Flat Shift / Sequential Shift Cut

- Maintain throttle during shifts
- Brief fuel/ignition cut at shift point (100-200ms)
- Retain boost between gears
- Configure via Boost/Advanced → Sequential Shift Cut

### Nitrous Control (MS2/Extra)

- Supports Stage 1 and Stage 2 nitrous systems
- Configure activation conditions (RPM window, TPS threshold, coolant temp minimum)
- Fuel enrichment added to compensate for additional oxygen
- Timing retard during nitrous activation
- Configure via Boost/Advanced → Nitrous

### Table Switching

- MS2/Extra supports switching between multiple fuel and spark tables
- Controlled by an input pin, CAN input, or other condition
- Useful for: race fuel vs. pump gas, nitrous on/off, traction control intervention
- Configure via Boost/Advanced → Table Switching Control

### Programmable On/Off Outputs

- Configure spare outputs to trigger based on RPM, TPS, MAP, coolant temp, or other conditions
- Useful for: fans, shift lights, warning lights, nitrous solenoids, water/meth injection
- Configure via Boost/Advanced → Programmable On/Off Outputs

## Trigger Setup and Diagnostics

### Wheel Decoder / Trigger Wizard
Setting up the trigger pattern is one of the first and most critical configuration steps:
- Use **Ignition Settings → Trigger Wizard** for guided setup
- Select your trigger wheel type (e.g., 36-1, 60-2, Ford TFI, GM HEI, etc.)
- Set the trigger angle (degrees BTDC for the trigger event)
- Configure primary and secondary tach input noise filtering if experiencing misfires or sync loss

### Tooth Logger / Composite Logger
Essential diagnostic tools for verifying trigger signal quality:
- **Tooth Logger**: Records raw tooth arrival times — use to verify tooth count and missing tooth detection
- **Composite Logger**: Overlays crank and cam signals — use to verify cam sync and trigger alignment
- **Sync Error Logger**: Captures sync loss events for diagnosing intermittent trigger issues
- Access via the Diagnostics menu in TunerStudio
- Always run tooth logger before first start to verify clean trigger signal

## Datalog Analysis

### Key Parameters to Log

| Parameter | What to Watch |
|-----------|---------------|
| RPM | Stability, limiter hits |
| MAP | Response to throttle, leaks |
| AFR (wideband) | Deviation from target |
| EGO Correction | Should stay within ±10% |
| CLT | Reaches operating temp |
| IAT | Heat soak effects |
| Spark Advance | Matches table |
| Injector PW | Headroom, max duty cycle |
| TPS | Smooth operation, TPSdot |

### Common Issues

**Lean at Tip-In:**
- Increase TPS-based accel enrichment
- Check MAPdot sensitivity

**Rich at Decel:**
- Enable deceleration fuel cut (DFCO)
- Set appropriate TPS threshold (typically <10%)
- Set RPM threshold above idle

**Idle Hunting:**
- Check for vacuum leaks
- Adjust idle PID gains
- Verify TPS closed position
- Check ignition timing stability

**Knock at High Load:**
- Reduce spark advance in affected cells
- Enrich mixture (reduce target AFR)

## TunerStudio Specific

### Burning Changes to Flash
When you change settings in TunerStudio, changes are held in RAM until you **burn** them to the ECU's flash memory. Unburned changes are lost when the ECU powers off.
- **Burn**: Ctrl+B or the Burn button writes current page to flash
- VE Tables, Spark Tables, and AFR Tables support **live tuning** — changes take effect immediately in RAM without burning, but still must be burned to persist
- Flash memory supports approximately **100,000 burn cycles** — avoid excessive rapid burns
- Always burn after completing a tuning session

### INI File
The INI file defines the TunerStudio interface for a specific firmware version. It maps all constants, tables, output channels, menus, and gauges.
- A **mismatch between INI file and firmware** is the most common connection/compatibility issue
- Symptoms: "Controller code version does not match signature" error, missing menus, garbled readings
- Fix: Download the correct INI from msextra.com matching your exact firmware version
- TunerStudio can auto-detect and download the correct INI in most cases

### Project Setup
1. Create new project → select firmware (MS1, MS2, MS3) — ensures correct INI file
2. Load base tune (.msq file) or start from default
3. Connect to controller (serial, USB, or Bluetooth)
4. Sync with controller to load current settings

### Tuning Interface
- **Basic/Customize Tuning**: Navigate tables
- **Table**: View/edit individual tables
- **Runtime Data**: Real-time monitoring
- **Datalog**: Record and playback logs

### Auto-Tune
- Enable VEAL (VE Analyze Live) with wideband
- Set acceptable AFR range
- Drive through as many cells as possible
- Review and accept changes
- Disable when done

### Safety Limits

**Rev Limiter:**
- Soft limit: retard timing
- Hard limit: fuel/ignition cut
- Set 200-500 RPM above max desired

**Overboost Protection:**
- Fuel cut above target pressure
- Ignition cut option

**Lean Cut:**
- Disable injectors if AFR exceeds safe threshold
- Typically 15:1+ under load

## Reference Materials

For detailed documentation, see:
- [references/tunerstudio-reference.md](references/tunerstudio-reference.md) - Full TunerStudio documentation
- [references/megasquirt-tuning-guide.md](references/megasquirt-tuning-guide.md) - Comprehensive tuning procedures

## Quick Reference Formulas

**Injector Duty Cycle:**
```
DC% = (Injector PW / Injection Period) × 100
```
Keep under 85% for safety margin.

**Required Fuel:**
TunerStudio calculates Required Fuel automatically when you enter engine displacement, number of injectors, injector flow rate (cc/min), and the injection divider. **Do not hand-calculate** — use the firmware's built-in calculation under Basic/Load Settings → Engine Constants to avoid errors.

**VE Adjustment from Measured AFR:**
```
New VE = Current VE × (Measured AFR / Target AFR)
```

**Airflow Estimation:**
```
MAF (g/s) ≈ (RPM × Displacement × VE% × MAP/100) / (2 × 60 × R × Temp)
```

## Safety Checklist

Before starting engine:
- [ ] Injector flow rate correct in settings
- [ ] Ignition timing verified with timing light
- [ ] Fuel pump primes and holds pressure
- [ ] No fuel leaks
- [ ] Wideband O2 sensor warmed up
- [ ] Emergency fuel/ignition cut accessible

During tuning:
- [ ] Monitor EGT if available
- [ ] Listen for detonation/knock
- [ ] Watch AFR on transitions
- [ ] Keep VE table changes conservative
- [ ] Save tune frequently with version notes
