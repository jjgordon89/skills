# TunerStudio Reference Guide

## Connection Setup

### Serial Connection
- Default baud rate: 115200
- Select correct COM port (Windows) or /dev/tty* (Linux/Mac)
- USB-serial adapters often use FTDI or CH340 chips

### Bluetooth Connection
- Pair Megasquirt Bluetooth module
- Default PIN: typically 1234 or 0000
- Connection may be slower than USB

### Firmware Selection
- **MS1/Extra**: Original Megasquirt with enhanced code
- **MS2/Extra**: Improved processor, more features
- **MS3**: Latest generation, most capable
- Select matching firmware in project settings

## Burning Changes to Flash

When you change settings in TunerStudio, changes are held in the ECU's RAM until explicitly written ("burned") to flash memory. **Unburned changes are lost when the ECU powers off.**

### How Burning Works
- **Burn command**: Ctrl+B or click the Burn button to write the current page to flash
- TunerStudio shows a yellow "needs burn" indicator when RAM differs from flash
- After burning, the indicator clears

### Live Tuning Exception
- **VE Tables, Ignition Tables, and AFR Tables** support live tuning — changes take effect immediately in RAM
- These still must be burned to persist across power cycles
- All other settings (engine constants, sensor config, etc.) require a burn before taking effect

### Flash Memory Limits
- Flash memory supports approximately **100,000 burn cycles** over its lifetime
- Avoid excessive rapid burns (e.g., burning after every single cell change)
- Best practice: make a batch of related changes, then burn once

## INI File

The INI file is the configuration file that defines the entire TunerStudio interface for a specific firmware version. It maps every constant, table, output channel, menu, gauge, and dialog.

### Why It Matters
- A **mismatch between INI file and loaded firmware** is the #1 cause of connection and compatibility issues
- Error: "Controller code version does not match signature" means INI doesn't match firmware
- Missing menus, garbled readings, or "command not recognized" errors also indicate a mismatch

### Managing INI Files
- TunerStudio can auto-detect firmware signature and download the matching INI
- Manual download: get the correct INI from msextra.com matching your exact firmware version and date code
- When creating a new project, selecting the correct firmware variant (MS1/Extra, MS2/Extra, MS3) ensures the right INI

### After Firmware Updates
- Always reload/update the INI file after flashing new firmware
- Creating a new TunerStudio project for the new firmware version is safest
- Load your saved .MSQ tune into the new project — TunerStudio will translate compatible settings

## Main Interface Sections

### Tuning → Basic/Customize Tuning
Access primary tuning tables:
- VE Table (fuel)
- AFR Target Table
- Spark Table
- Idle Control
- Startup/Enrichment

### Tuning → Advanced
- Injection timing
- Boost control
- Launch/flat shift
- Nitrous control
- Variable cam timing

### Tuning → Algorithm
Switch between:
- **Speed Density**: MAP-based (most common)
- **Alpha-N**: TPS-based (individual throttle bodies)
- **Blended**: Combination approach

## Data Logging

### Creating Logs
1. Go to Datalog → Start Logging
2. Select save location
3. Drive/monitor system
4. Stop logging when complete

### Log Analysis
- Open in MegaLogViewer (separate tool)
- Or view in TunerStudio built-in viewer
- Filter by time range or conditions

### Key Logged Parameters
- rpm - Engine speed
- map - Manifold pressure (kPa)
- tps - Throttle position (%)
- clt - Coolant temperature (°C or °F)
- iat - Intake air temperature
- afr1 - Wideband O2 reading
- egoCorrection - Closed-loop correction %
- veCurr - Current VE value
- pulseWidth - Injector pulse width (ms)
- advance - Current spark advance (°)

## VE Analyze (Auto-Tune)

### Setup
1. Requires wideband O2 sensor
2. Go to Tuning → VE Analyze
3. Set target AFR table
4. Configure filter settings:
   - Minimum RPM
   - Minimum engine temperature
   - Maximum EGO correction (limits unsafe changes)

### Running VEAL
1. Start with engine warm
2. Enable VE Analyze → Live
3. Drive through various loads/RPM
4. VEAL automatically adjusts cells
5. Accept or reject changes
6. Save tune when satisfied

### Safety Settings
- Max negative correction: 15-20%
- Max positive correction: 15-20%
- Prevents extreme lean/rich conditions during tuning

## Table Editing

### Keyboard Shortcuts
- **Arrow keys**: Navigate cells
- **+ / -**: Increment/decrement selected cell
- **Ctrl+Click**: Select multiple cells
- **Ctrl+C / Ctrl+V**: Copy/paste
- **Ctrl+Z**: Undo

### Interpolation
- **Interpolate Horizontal**: Smooth row
- **Interpolate Vertical**: Smooth column
- **Smooth**: Apply to selected region

### Table Properties
- Right-click → Table Properties
- Set axis breakpoints
- Adjust table dimensions (if firmware supports)

## Calibration

### TPS Calibration
1. Tools → Calibrate TPS
2. Ensure throttle fully closed
3. Click "Get Current" for closed
4. Open throttle fully
5. Click "Get Current" for WOT
6. Accept calibration

### MAP Sensor Calibration
1. Tools → Calibrate MAP/Baro
2. Key on, engine off (reading = atmospheric)
3. Verify or set offset/scale
4. Common sensors: MPX4250 (250kPa), MPXH6400 (400kPa)

### Temperature Sensor Calibration
1. Tools → Calibrate Thermistor
2. Select from preset curves:
   - **CLT**: GM, Ford, Bosch common sensors
   - **IAT**: Same options
   - Or enter custom resistance/temperature pairs

### Battery Voltage Calibration
1. Tools → Calibrate Battery Voltage
2. Measure actual battery voltage with multimeter
3. Enter measured value to correct ADC offset

### Wideband Calibration
1. Tools → Calibrate AFR Table
2. Depends on controller type:
   - **Innovate LC-1/LC-2**: 0-5V = 10-20 AFR (typical)
   - **AEM UEGO**: 0-5V = 10-20 AFR (typical)
   - **14Point7**: Verify voltage range per controller documentation
3. Set voltage-to-AFR mapping points to match your wideband controller's output

## Advanced Features

### Acceleration Wizard
Step-by-step setup for:
- TPS-based accel enrichment
- MAP-based accel enrichment
- Cold accel multiplier
- Decay rates

### Idle Control Wizard
Guides through:
- Valve type selection (PWM, stepper, on/off)
- PWM frequency
- PID tuning
- Target RPM table

### Ignition Wizard
For distributor or coil-on-plug:
- Trigger wheel setup
- Spark output settings
- Dwell time configuration

### Shift Light Settings
- RPM threshold
- Output pin assignment
- Hysteresis (prevent flicker)

## Dashboard Gauges

### Customizing Display
- Right-click → Add Gauge
- Drag to reposition
- Resize by dragging edges

### Available Gauge Types
- Numeric readout
- Horizontal/vertical bar
- Circular gauge
- LED indicator
- Graph (time-based)

### Alerts
Set warnings for:
- High coolant temp
- Lean AFR
- High MAP (overboost)
- Low oil pressure (if sensor connected)

## Controller Settings

### Engine Constants
Critical base settings:
- **Displacement**: Total engine size
- **Injector Flow**: Rated cc/min or lb/hr
- **Number of Cylinders**
- **Injector Opening Time**: Latency at 13.2V
- **Battery Voltage Correction**: PW adjustment for voltage

### Injection Settings
- **Staging**: Simultaneous, alternating, sequential
- **Injection Timing**: End of injection angle (degrees BTDC) — configurable via injection timing tables
- **Dual Table**: Enable for independent bank control
- **Injector PWM**: For high-impedance (peak-and-hold) injectors, configure PWM duty and frequency to reduce injector heating
- **Injector Dead-Time**: Latency compensation at reference voltage (typically 13.2V) — critical for accurate fuel delivery
- **Staged Injection**: For engines with primary and secondary injectors — configure staging point (RPM and load thresholds), transition blend, and secondary injector flow rate
- **Flex Fuel**: When an ethanol content sensor is installed, blends between fuel/spark tables based on ethanol percentage

### Ignition Settings
- **Ignition Type**: Basic trigger, wheel decoder, etc.
- **Trigger Angle**: Degrees BTDC for trigger event
- **Spark Output**: Going high, going low, inverted
- **Dwell Battery Correction**: Curve that adjusts coil dwell time based on battery voltage — ensures consistent spark energy across voltage variations
- **MAT-Based Timing Retard**: Automatically retards ignition timing when intake air temperature rises — protects against knock from heat soak
- **Noise Filtering**: Configurable filtering for primary and secondary tach inputs — increase if experiencing false trigger events or sync loss from electrical noise

### Trigger Wizard
Guided setup for crank/cam trigger configuration:
1. Ignition Settings → Trigger Wizard
2. Select trigger wheel type (36-1, 60-2, Ford TFI, GM HEI, Nissan CAS, etc.)
3. Configure number of teeth and missing teeth
4. Set primary and secondary trigger edges (rising/falling)
5. Set trigger angle (degrees BTDC for trigger reference point)
6. Verify with tooth logger before starting engine

## Troubleshooting Connection

### Cannot Connect
1. Verify correct COM port
2. Check baud rate matches firmware
3. Try different USB cable
4. Check device manager for driver issues
5. Verify Megasquirt is powered

### Intermittent Connection
- Poor grounding causing noise
- USB cable too long (keep under 10ft)
- Bluetooth interference
- Insufficient power supply

### Data Corruption
- Check grounds
- Shield signal wires
- Reduce serial cable length
- Update firmware

## Firmware Updates

### MS2/Extra
1. Download latest firmware from msextra.com
2. Tools → Upgrade Firmware
3. Select .S19 file
4. Follow prompts (do not interrupt)
5. Reload base tune after update

### MS3
Similar process, use MS3-specific firmware files
Always backup tune before updating

## Keyboard Commands During Runtime

- **Spacebar**: Pause datalog playback
- **F1**: Help (context-sensitive)
- **F5**: Refresh connection
- **Ctrl+S**: Save project
- **Ctrl+R**: Reset connection

## Project Files

### .MSQ Files
- Contains all tuning parameters
- Save versions: baseline, idle-tuned, drivable, etc.
- Can be shared between similar setups

### .MSL Files
- Datalog files recorded by TunerStudio
- Tab-separated text format (CSV-like), viewable in any text editor
- Best analyzed in MegaLogViewer for graphing, scatter plots, and histogram analysis
- Can be exported to standard CSV for use in spreadsheets

### Project Directory
Located in Documents/TunerStudioProjects/
Contains:
- Project settings
- Gauge layouts
- Log files
- Tune revisions

## ECU Profiles

### Loading a Profile
- File → Load Tune
- Select .MSQ file
- Sync to controller or save as new

### Saving a Profile
- File → Save Tune
- Choose location
- Use descriptive names with dates/versions

### Compare Tunes
- Tools → Compare MSQs
- Select two files
- Shows differences in tables/settings
- Useful for troubleshooting changes

## CAN Bus

### Overview
Megasquirt uses a two-wire CAN (Controller Area Network) connection for expansion boards and external devices. MS2/Extra supports two CAN protocols:
- **29-bit proprietary CAN** — used for Megasquirt expansion boards (GPIO, additional ADC inputs)
- **11-bit standard broadcasting** — used for aftermarket dashes and external devices

### CAN Parameters (CAN bus/Testmodes menu)
- **My CAN ID**: Keep at 0 unless this ECU is a secondary data capture unit
- **Master Enable**: Activates data retrieval from expansion boards
- **Enable PWM Polling**: Captures pulse/frequency data from expansion boards
- **Remote CAN ID**: Specifies the expansion board's CAN ID

### CAN Broadcasting
- **Realtime Data Broadcasting**: Streams live engine data to external devices over CAN
- **Dash Broadcasting**: Sends formatted data for aftermarket dashboard displays
- Configure broadcast rates and which channels to transmit

### Common CAN Uses
- Additional analog/digital inputs via GPIO expansion boards
- Aftermarket digital dashes (AIM, RacePak, etc.)
- Data acquisition systems
- Secondary ECU communication (e.g., transmission controller)

## Diagnostics and High-Speed Loggers

### Tooth Logger
- Records raw tooth arrival times from the crank/cam trigger wheel
- Use to verify: correct tooth count, missing tooth detection, clean signal edges
- **Run before first start** to confirm trigger signal quality
- Access: Diagnostics menu → Tooth Logger

### Composite Logger
- Overlays crank and cam signals on a single plot
- Use to verify: cam sync timing relative to crank, correct phasing
- Essential for diagnosing sequential injection/ignition sync issues
- Access: Diagnostics menu → Composite Logger

### Sync Error Logger
- Captures sync loss events with timing data
- Use to diagnose: intermittent trigger issues, noise-induced sync loss, worn reluctor wheels
- Access: Diagnostics menu → Sync Error Logger

### Trigger Logger
- Records detailed trigger event data
- Use for advanced debugging of trigger/decoder issues
- Access: Diagnostics menu → Trigger Logger

### Output Test Mode
Test individual hardware outputs without running the engine:
- **Injector Test**: Fire individual injectors to verify wiring and flow
- **Coil Test**: Fire individual coils to verify spark output
- **PWM Test**: Test idle valve and other PWM outputs
- **I/O Test**: Verify digital input/output pins
- Access: CAN bus/Testmodes menu → Output Test Mode
- **Highly recommended before first startup** to verify all wiring

## Protocol Statistics
- Tools → Protocol Stats
- Shows communication health: packets sent, received, errors, retries
- Useful for diagnosing intermittent connection issues
- High error rates indicate wiring problems, ground loops, or interference
