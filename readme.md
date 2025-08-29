# EMG-Controlled Drone Training Simulator

**Research Platform for HardwareX Journal Publication**

An innovative drone training simulator controlled by electromyography (EMG) signals using the BioAmp EXG Pill sensor and Arduino Uno R4. This system enables muscle-based drone control for research into human-machine interfaces and accessible drone operation.

## Research Objectives

- **EMG-Based Drone Control**: Demonstrate feasibility of muscle signal-based drone operation
- **Hardware Integration**: Validate low-cost EMG acquisition system for real-time control
- **Control System Development**: Design and implement EMG-to-flight command mapping
- **Performance Characterization**: Measure system response time, accuracy, and signal quality

## Hardware Requirements

### Core Components
- **Arduino Uno R4** (or compatible)
- **BioAmp EXG Pill** - 4-channel EMG acquisition module
- **EMG Electrodes** - 8 electrodes (2 per muscle group)
- **USB Cable** - Arduino to PC connection

### EMG Sensor Placement (Single Arm Configuration)

```
Right Arm EMG Sensor Placement:
                                    
    Shoulder                        
        |                           
        |   [A2] ← Bicep Brachii (Pitch Control)
        |    ●●                     
    Upper Arm                       
        |    ●●                     
        |   [A3] ← Tricep Brachii (Roll Control)
        |                           
    ────┴────                       
     Elbow                          
    ────┬────                       
        |                           
        |   [A1] ← Forearm Extensor (Yaw Control)
        |    ●●                     
    Forearm                         
        |    ●●                     
        |   [A0] ← Forearm Flexor (Throttle Control)
        |                           
    ────┴────                       
     Wrist                          
        |                           
      Hand                          

EMG Channel Mapping:
• A0 (Throttle): Forearm flexor muscles → Wrist flexion movement
• A1 (Yaw): Forearm extensor muscles → Wrist extension movement  
• A2 (Pitch): Bicep brachii → Elbow flexion movement
• A3 (Roll): Tricep brachii → Elbow extension movement

Electrode Placement Notes:
- Place electrodes (●●) over muscle belly for maximum signal
- Use bipolar configuration with 2cm inter-electrode distance
- Reference electrode on bony prominence (elbow or wrist)
- Clean skin with alcohol before electrode attachment
```

## Project Structure

```
drone_simulator/
├── main.py                 # Main simulator application
├── arduino_emg_control.ino # Arduino EMG acquisition code
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
└── images/                # Required visual assets
    ├── sky_background.png # Sky background image
    ├── ground_texture.png # Ground surface texture
    ├── building.png       # Obstacle building texture
    ├── checkpoint.png     # Target checkpoint icon
    └── hud_overlay.png    # Instrument panel graphics (optional)
```

## Installation & Setup

### 1. Python Environment Setup
```bash
# Create virtual environment
python -m venv drone_sim_env
source drone_sim_env/bin/activate  # Linux/Mac
# or
drone_sim_env\Scripts\activate     # Windows

# Install dependencies
pip install pygame pyserial numpy
```

## Hardware Setup

### BioAmp EXG Pill to Arduino Connection
```
BioAmp EXG Pill    Arduino Uno R4
─────────────────  ──────────────
VCC             →  3.3V
GND             →  GND
OUT1            →  A0 (Throttle)
OUT2            →  A1 (Yaw)
OUT3            →  A2 (Pitch) 
OUT4            →  A3 (Roll)
```

### EMG Electrode Preparation and Placement

#### Required Materials
- 8 Ag/AgCl EMG electrodes (disposable)
- 4 EMG electrode cables (3-lead configuration)
- Isopropyl alcohol (70% minimum)
- Cotton pads or alcohol wipes
- Skin preparation gel (optional)

#### Skin Preparation Protocol
1. **Clean the skin**: Use alcohol wipes to remove oils and dead skin
2. **Dry completely**: Ensure no alcohol residue remains
3. **Light abrasion**: Gently rub with cotton pad to improve conductivity
4. **Wait**: Allow 30 seconds before electrode placement

#### Electrode Placement Procedure

**Channel A0 - Forearm Flexor (Throttle Control)**
- Position: Ventral forearm, 1/3 distance from wrist to elbow
- Muscle: Flexor carpi radialis and palmaris longus
- Placement: Two electrodes 2cm apart over muscle belly
- Reference: Place reference electrode on wrist bone (radial styloid)

**Channel A1 - Forearm Extensor (Yaw Control)**
- Position: Dorsal forearm, 1/3 distance from wrist to elbow  
- Muscle: Extensor carpi radialis longus/brevis
- Placement: Two electrodes 2cm apart over muscle belly
- Reference: Use same wrist bone reference as A0

**Channel A2 - Bicep Brachii (Pitch Control)**
- Position: Anterior upper arm, muscle belly center
- Muscle: Bicep brachii (long head)
- Placement: Two electrodes 2cm apart along muscle fiber direction
- Reference: Place reference electrode on lateral epicondyle (elbow)

**Channel A3 - Tricep Brachii (Roll Control)**
- Position: Posterior upper arm, lateral head of tricep
- Muscle: Tricep brachii (lateral head)
- Placement: Two electrodes 2cm apart along muscle fiber direction  
- Reference: Use same elbow reference as A2

#### Connection Verification
1. **Arduino Setup**: Upload `arduino_emg_control.ino` to Arduino Uno R4
2. **Serial Monitor**: Open Arduino IDE Serial Monitor (115200 baud)
3. **Signal Test**: Flex each muscle group individually
4. **Expected Output**: Four comma-separated values updating in real-time
5. **Signal Quality**: Values should range from 0-100, with clear increases during muscle contraction

### Hardware Assembly Steps

#### Step 1: Arduino Programming
```bash
1. Connect Arduino Uno R4 to computer via USB
2. Open Arduino IDE
3. Load arduino_emg_control.ino
4. Select correct board: Arduino Uno R4 WiFi (or Minima)
5. Select correct COM port
6. Upload sketch to Arduino
```

#### Step 2: BioAmp EXG Pill Configuration  
```bash
1. Connect BioAmp EXG Pill to Arduino using jumper wires
2. Ensure correct pin mapping (VCC→3.3V, GND→GND, OUT1-4→A0-A3)
3. Power on Arduino (USB connection provides power)
4. Verify BioAmp power LED is illuminated
```

#### Step 3: EMG Electrode Setup
```bash
1. Prepare skin surfaces using alcohol wipes
2. Attach electrodes according to placement diagram
3. Connect electrode cables to BioAmp EXG Pill inputs
4. Ensure secure connections and good skin contact
5. Test signal quality using Arduino Serial Monitor
```

#### Step 4: Software Configuration
```bash
1. Install Python dependencies: pip install -r requirements.txt
2. Configure COM port in main.py (arduino_port = 'COM3')  
3. Set ARDUINO_MODE = True in main.py
4. Run initial calibration to determine EMG thresholds
```

### Calibration Process

#### EMG Signal Calibration
```python
# Calibration procedure in main.py
1. Rest Position: Record EMG signals at complete muscle relaxation
2. Maximum Voluntary Contraction (MVC): Record peak EMG for each muscle
3. Threshold Setting: Set activation threshold at 20-30% of MVC
4. Range Mapping: Map EMG range to control inputs (0-100%)
```

#### Control Sensitivity Adjustment
- **emg_threshold**: Minimum signal level to register as intentional control
- **emg_max**: Maximum expected signal level for full control authority  
- **Fine-tuning**: Adjust values based on individual muscle strength and signal quality

### Troubleshooting Hardware Issues

#### Poor EMG Signal Quality
- **Check skin preparation**: Re-clean with alcohol, ensure dry skin
- **Electrode contact**: Press electrodes firmly, check for air bubbles
- **Cable connections**: Verify secure connections to BioAmp inputs
- **Muscle activation**: Ensure proper muscle contraction technique

#### Arduino Connection Problems  
- **COM port**: Verify correct port selection in Device Manager (Windows)
- **USB cable**: Test with known good USB cable, try different ports
- **Driver installation**: Install Arduino drivers if not automatically recognized
- **Power supply**: Ensure Arduino receives adequate USB power (500mA minimum)

#### BioAmp EXG Pill Issues
- **Power verification**: Check 3.3V supply voltage with multimeter
- **Ground connection**: Ensure solid GND connection between Arduino and BioAmp
- **Channel isolation**: Test each EMG channel individually for proper function
- **Signal saturation**: Reduce input signal if readings consistently at maximum

### Safety Considerations

#### Electrical Safety
- Use only USB-powered Arduino (isolated from mains power)
- Verify BioAmp EXG Pill is designed for human EMG measurement
- Do not modify circuit connections while electrodes are attached
- Disconnect electrodes before making any hardware changes

#### Biological Safety  
- Use only medical-grade, skin-safe electrodes
- Replace electrodes after each session or when adhesion degrades
- Stop immediately if skin irritation occurs
- Clean electrode sites with alcohol after removal

#### Signal Quality Assurance
- Maintain electrode impedance below 10kΩ (check with multimeter if available)
- Monitor for 50/60Hz noise pickup (indicates poor grounding or interference)
- Verify muscle activation produces clear, repeatable EMG signals
- Document baseline and maximum signal levels for each session

### 3. Image Assets
Create an `images/` folder and add the required PNG files:
- **sky_background.png** (1200x800px) - Sky/landscape background
- **ground_texture.png** (tileable texture) - Ground surface pattern
- **building.png** (variable size) - Building obstacle texture
- **checkpoint.png** (64x64px) - Target waypoint icon
- **hud_overlay.png** (optional) - Instrument panel graphics

*Note: Simulator includes fallback graphics if images are missing*

### 4. Hardware Configuration
In `main.py`, configure hardware settings:
```python
# Set to True when Arduino is connected
ARDUINO_MODE = False  # Change to True for hardware mode

# Arduino connection settings
arduino_port = 'COM3'    # Update for your system
baud_rate = 115200
emg_threshold = 30.0     # Adjust based on signal strength
emg_max = 100.0         # Maximum expected EMG amplitude
```

## Running the Simulator

### Testing Mode (No Hardware)
```bash
python main.py
```
- **Controls**: WASD (pitch/roll), Space (throttle), QE (yaw), R (reset)
- **View**: First-person perspective from FPV drone cockpit
- **Flight Mode**: Single FPV racing drone configuration

### Hardware Mode (With EMG)
1. Connect Arduino with EMG sensors
2. Set `ARDUINO_MODE = True` in main.py
3. Update `arduino_port` if needed
4. Run simulator: `python main.py`
5. Use first-person FPV racing drone view with EMG muscle control
6. Calibrate EMG thresholds based on your muscle signals

## Drone Flight Characteristics

### FPV Racing Drone Configuration
- **Flight Model**: Omnidirectional movement with hover capability and high-speed forward flight
- **Maneuverability**: Acrobatic flight capabilities with immediate response to control inputs
- **Control Response**: Sensitive, direct thrust vectoring with low latency
- **First-Person View**: Racing drone cockpit with high-refresh stabilized camera
- **Applications**: Racing competitions, aerial photography, inspection, emergency response
- **Flight Envelope**: Full 3D flight capability including inverted flight and rapid direction changes

## Training Scenarios

### High-Speed Navigation Course
- **Objective**: Navigate efficiently through waypoints using first-person perspective at high speed
- **View**: FPV racing cockpit with navigation instruments and target indicators
- **Time Limit**: 90 seconds
- **Speed Challenge**: Navigate at speeds up to 90 km/h while maintaining precision
- **Focus**: High-speed flight control, obstacle avoidance, precision navigation
- **Skills**: Split-second decision making, high-speed maneuvering, instrument flying

### Precision Agility Course  
- **Objective**: Execute complex flight patterns through tight spaces using cockpit view
- **View**: High-refresh FPV camera with racing-style HUD elements
- **Time Limit**: 60 seconds
- **Maneuver Challenge**: Perform rapid direction changes, loops, and precision flying
- **Focus**: Agility, control precision, spatial awareness through first-person control
- **Skills**: Acrobatic maneuvering, reaction time, fine motor control precision

## Research Data Collection

The simulator logs performance metrics for research analysis:
- **EMG Signal Strength**: Real-time muscle activation levels displayed in FPV cockpit HUD
- **Flight Performance**: Speed (km/h), altitude, trajectory tracking from first-person perspective
- **Navigation Accuracy**: Target acquisition and waypoint navigation precision at high speeds
- **Control Precision**: Crosshair accuracy and flight path stability during high-speed flight
- **System Response**: EMG-to-flight control latency measurement during dynamic maneuvers

## Safety Considerations

- **EMG Safety**: Use only body-safe electrodes and proper skin preparation
- **Signal Quality**: Ensure good electrode contact for reliable control
- **Muscle Fatigue**: Take breaks to prevent overexertion
- **Calibration**: Regularly recalibrate EMG thresholds for consistent performance

## Troubleshooting

### Common Issues

**No Arduino Connection**:
- Verify COM port in Device Manager
- Check USB cable and Arduino power
- Ensure correct baud rate (115200)

**Poor EMG Signal Quality**:
- Clean skin with alcohol before electrode placement
- Check electrode contact and positioning
- Adjust `emg_threshold` and `emg_max` values
- Replace electrodes if signal is noisy

**Missing Images**:
- Verify all PNG files exist in `images/` folder
- Check file names match exactly (case-sensitive)
- Simulator will use fallback graphics if images missing

## Research Applications

### Potential Studies
1. **System Characterization**: EMG signal quality and control precision measurement
2. **Response Latency Analysis**: Time from muscle activation to drone response
3. **Signal Processing Optimization**: Filter design and noise reduction effectiveness
4. **Control Mapping Evaluation**: Different EMG-to-command mapping strategies
5. **Hardware Validation**: Component performance and reliability testing

### Data Export
- Modify `main.py` to log performance data to CSV files
- Export EMG signal data for offline analysis
- Record system performance metrics for technical validation


## Contributing

This is an open-source research platform. Contributions welcome:
- Additional drone flight models
- New training scenarios  
- Enhanced EMG signal processing
- Improved calibration algorithms
- Data analysis tools


## References

- BioAmp EXG Pill Documentation: [Upside Down Labs](https://upsidedownlabs.tech/)
- EMG Signal Processing: Butterworth filtering implementation
- HardwareX Journal Guidelines: [Elsevier HardwareX](https://www.journals.elsevier.com/hardwarex)
- Arduino Uno R4 Specifications: [Arduino Official](https://docs.arduino.cc/)
- Pygame Documentation: [pygame.org](https://www.pygame.org/docs/)

## Performance Metrics & Validation

### EMG Signal Quality Metrics
- **Signal-to-Noise Ratio**: >20dB for reliable control
- **Response Latency**: <100ms from muscle activation to drone response
- **Control Accuracy**: ±5% deviation from intended control input
- **Cross-talk Rejection**: <10% interference between channels

### Flight Performance Benchmarks
- **Shahed 136 Mode**: Completion rate >80% for navigation missions
- **FPV Racing Mode**: Average lap times competitive with keyboard controls
- **Collision Avoidance**: <15% obstacle collision rate after training
- **Target Acquisition**: >90% accuracy within training scenarios

### Training Effectiveness Measures
- **Learning Curve**: 50% improvement in completion time over 10 sessions
- **Skill Retention**: Performance maintained after 1-week break
- **Fatigue Resistance**: <20% performance degradation in 30-minute sessions
- **Adaptability**: Successful control transfer between drone types

## Experimental Protocols

### Study Design Recommendations

#### Participant Requirements
- **Age Range**: 18-65 years
- **Health Status**: No known neuromuscular disorders
- **Experience Level**: Mixed (novice to experienced drone operators)
- **Sample Size**: Minimum 20 participants for statistical significance

#### Training Protocol
1. **Baseline Assessment**: Traditional joystick control performance
2. **EMG Calibration**: Individual muscle activation mapping
3. **Training Phase**: 5 sessions, 30 minutes each, over 2 weeks
4. **Performance Testing**: Standardized scenarios for both control methods
5. **Follow-up**: Retention testing after 1-week interval

#### Data Collection Points
- **Pre-training**: Demographics, experience, baseline performance
- **Each Session**: EMG signals, flight paths, completion times, errors
- **Post-training**: Performance comparison, user experience surveys
- **Follow-up**: Skill retention, preference feedback

### Statistical Analysis Framework
- **Primary Outcomes**: Task completion time, accuracy measures
- **Secondary Outcomes**: Learning curves, user satisfaction, fatigue measures
- **Analysis Methods**: Repeated measures ANOVA, regression analysis
- **Effect Size**: Cohen's d for meaningful difference detection

## Advanced Features

### Signal Processing Enhancements
```python
# Example EMG preprocessing pipeline
def advanced_emg_processing(raw_signal):
    # Notch filter for 50/60Hz noise removal
    filtered = notch_filter(raw_signal, 50)
    
    # Adaptive threshold based on recent history
    threshold = adaptive_threshold(filtered, window_size=500)
    
    # Fatigue compensation
    compensated = fatigue_compensation(filtered, session_time)
    
    return compensated
```

### Machine Learning Integration
- **Pattern Recognition**: Classify different muscle activation patterns
- **Adaptive Calibration**: Automatically adjust to user's EMG characteristics  
- **Predictive Control**: Anticipate user intentions based on EMG trends
- **Anomaly Detection**: Identify signal artifacts or electrode displacement

### Extended Scenarios
```python
# Additional training scenarios
def create_search_rescue_scenario():
    """Search and rescue mission with multiple objectives"""
    return TrainingScenario(
        "Search & Rescue Mission",
        "Locate and mark survivor positions in disaster zone",
        obstacles=disaster_debris(),
        targets=survivor_locations(),
        time_limit=180
    )

def create_formation_flight():
    """Multi-drone coordination scenario"""
    return TrainingScenario(
        "Formation Flight Training", 
        "Maintain formation with AI wingmen",
        obstacles=dynamic_obstacles(),
        targets=formation_waypoints(),
        time_limit=120
    )
```

## Data Visualization & Analysis

### Real-time Monitoring Dashboard
- **EMG Signal Plots**: Live waveform display with frequency analysis
- **Flight Path Tracking**: 3D trajectory visualization
- **Performance Metrics**: Real-time KPI dashboard
- **Fatigue Indicators**: Muscle activation trend analysis

### Post-Session Analysis Tools
```python
# Example analysis functions
def analyze_learning_curve(session_data):
    """Calculate learning rate and performance trends"""
    completion_times = [s['completion_time'] for s in session_data]
    return np.polyfit(range(len(completion_times)), completion_times, 1)

def emg_fatigue_analysis(emg_data, timestamps):
    """Analyze muscle fatigue over session duration"""
    median_frequency = calculate_median_frequency(emg_data)
    return correlation(median_frequency, timestamps)
```

## Applications & Impact

### Research Domains
- **Biomedical Engineering**: Muscle signal acquisition and processing
- **Control Systems**: Human-machine interface development
- **Signal Processing**: EMG filtering and feature extraction
- **Hardware Design**: Low-cost biosensor integration
- **Computer Graphics**: Real-time simulation and visualization

### Technical Applications
- **FPV Flight Training**: Immersive first-person drone piloting experience
- **Alternative Control Systems**: Hands-free cockpit operation
- **Flight Simulation**: Realistic pilot perspective with EMG integration
- **Educational Platforms**: Bioengineering demonstration through flight simulation
- **Research Equipment**: Standardized EMG-flight control testbed
- **Prototype Development**: Proof-of-concept for muscle-controlled vehicle interfaces

### Social Impact
- **Educational Value**: STEM learning through bioengineering applications
- **Open Source Hardware**: Accessible platform for EMG research
- **Technical Innovation**: Demonstration of low-cost biosensor integration
- **Research Advancement**: Standardized platform for EMG control studies

---

**Disclaimer**: This research platform is intended for academic and educational purposes. Always follow proper safety protocols when using EMG equipment and conducting human subjects research. Obtain appropriate institutional review board (IRB) approval for studies involving human participants.