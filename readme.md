# EMG Flight Control Research Platform

**Research Platform for HardwareX Journal Publication**

An EMG-controlled flight simulator using the BioAmp EXG Pill sensor and Arduino Uno R4 for research into muscle signal-based human-machine interfaces. This platform enables validation of electromyography signals for real-time flight control applications.

## Research Objectives

- **EMG Signal Validation**: Demonstrate feasibility of muscle signal-based flight control
- **Hardware Integration**: Validate low-cost EMG acquisition system for real-time applications
- **Control System Development**: Design and implement EMG-to-flight command mapping
- **Performance Characterization**: Measure system response time, accuracy, and signal quality

## Hardware Requirements

### Core Components
- **Arduino Uno R4** (or compatible microcontroller)
- **BioAmp EXG Pill** - 4-channel EMG acquisition module
- **EMG Electrodes** - 8 disposable Ag/AgCl electrodes (2 per muscle group)
- **USB Cable** - Arduino to PC connection

### EMG Sensor Placement (Single Arm Configuration)

```
Right Arm EMG Sensor Placement:
                                    
    Shoulder                        
        |                           
        |   [A2] - Bicep Brachii (Pitch Control)
        |    ●●                     
    Upper Arm                       
        |    ●●                     
        |   [A3] - Tricep Brachii (Roll Control)
        |                           
    ────┴────                       
     Elbow                          
    ────┬────                       
        |                           
        |   [A1] - Forearm Extensor (Yaw Control)
        |    ●●                     
    Forearm                         
        |    ●●                     
        |   [A0] - Forearm Flexor (Throttle Control)
        |                           
    ────┴────                       
     Wrist                          
        |                           
      Hand                          

EMG Channel Mapping:
• A0 (Throttle): Forearm flexor muscles - Wrist flexion movement
• A1 (Yaw): Forearm extensor muscles - Wrist extension movement  
• A2 (Pitch): Bicep brachii - Elbow flexion movement
• A3 (Roll): Tricep brachii - Elbow extension movement

Electrode Placement Notes:
- Place electrodes (●●) over muscle belly for maximum signal
- Use bipolar configuration with 2cm inter-electrode distance
- Reference electrode on bony prominence (elbow or wrist)
- Clean skin with alcohol before electrode attachment
```

## Project Structure

```
emg_drone_research/
├── main.py                           # Main research application
├── arduino_emg_code.ino             # Arduino EMG acquisition code
├── README.md                         # Documentation
├── requirements.txt                  # Python dependencies
│
├── core_systems/
│   ├── drone.py                      # Drone physics simulation
│   ├── vector3.py                    # 3D vector mathematics
│   ├── physics_manager.py            # Physics and collision detection
│   ├── fpv_hud_system.py            # HUD display system
│   └── config.py                     # Core system configuration
│
├── research_modules/
│   ├── config.py                     # Research configuration
│   ├── research_config_ui.py         # Simplified configuration interface
│   ├── research_obstacles.py         # Target waypoints (no obstacles)
│   ├── emg_evaluation_system.py      # EMG signal analysis
│   └── emg_calibration_ui.py         # EMG calibration interface
│
└── data_output/                      # Generated during sessions
    ├── debug_logs/                   # Flight performance data
    ├── emg_data/                     # EMG signal recordings
    └── reports/                      # Analysis reports
```

## Installation & Setup

### 1. Python Environment Setup
```bash
# Create virtual environment
python -m venv emg_research_env
source emg_research_env/bin/activate  # Linux/Mac
# or
emg_research_env\Scripts\activate     # Windows

# Install dependencies
pip install pygame pyserial numpy
```

### 2. Hardware Configuration
In `main.py`, configure hardware settings:
```python
# Set to True when Arduino is connected
ARDUINO_MODE = False  # Change to True for hardware mode

# Arduino connection settings
arduino_port = 'COM3'    # Update for your system (Windows) or '/dev/ttyUSB0' (Linux)
baud_rate = 115200
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
- Additional Ag/AgCl EMG electrodes (disposable) - BioAmp EXG Pill includes 4, you need 8 total
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
- Placement: Two electrodes from single cable over muscle belly (differential measurement)

**Channel A1 - Forearm Extensor (Yaw Control)**
- Position: Dorsal forearm, 1/3 distance from wrist to elbow  
- Muscle: Extensor carpi radialis longus/brevis
- Placement: Two electrodes from single cable over muscle belly (differential measurement)

**Channel A2 - Bicep Brachii (Pitch Control)**
- Position: Anterior upper arm, muscle belly center
- Muscle: Bicep brachii (long head)
- Placement: Two electrodes from single cable along muscle fiber direction (differential measurement)

**Channel A3 - Tricep Brachii (Roll Control)**
- Position: Posterior upper arm, lateral head of tricep
- Muscle: Tricep brachii (lateral head)
- Placement: Two electrodes from single cable along muscle fiber direction (differential measurement)

#### Connection Verification
1. **Arduino Setup**: Upload `arduino_emg_code.ino` to Arduino Uno R4
2. **Serial Monitor**: Open Arduino IDE Serial Monitor (115200 baud)
3. **Signal Test**: Flex each muscle group individually
4. **Expected Output**: Four comma-separated values updating in real-time
5. **Signal Quality**: Values should range from 0-100, with clear increases during muscle contraction

### Hardware Assembly Steps

#### Step 1: Arduino Programming
```bash
1. Connect Arduino Uno R4 to computer via USB
2. Open Arduino IDE
3. Load arduino_emg_code.ino
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

## Running the Research Platform

### Testing Mode (No Hardware Required)
```bash
python main.py
```
- **Controls**: WASD (pitch/roll), Space (throttle), QE (yaw), R (reset)
- **View**: First-person flight perspective
- **Environment**: Empty space for pure flight physics testing
- **Data Collection**: Simulated EMG signals for algorithm development

### Hardware Mode (With EMG Sensors)
1. Connect Arduino with EMG sensors
2. Set `ARDUINO_MODE = True` in main.py
3. Update `arduino_port` if needed
4. Run platform: `python main.py`
5. Complete EMG calibration process
6. Begin research flight sessions with muscle control

## Research Configuration Options

The platform provides simplified configuration focused on research parameters:

### Flight Parameters
- **Conservative (120 km/h)**: Stable flight for initial EMG testing
- **Standard (150 km/h)**: Balanced performance for training
- **High Performance (180 km/h)**: Racing characteristics for advanced testing

### Range Configuration
- **Short Range (2 km)**: Close-proximity testing
- **Medium Range (5 km)**: Standard research range

### Research Environment
- **Obstacles**: DISABLED (research focus)
- **Ground Collision**: ENABLED (primary challenge)
- **Navigation Targets**: OPTIONAL
- **Physics**: Realistic flight dynamics
- **Data Logging**: Comprehensive EMG + flight data

## EMG Calibration Process

The platform includes a structured calibration workflow:

### Calibration Steps
1. **Baseline Calibration**: Record muscle relaxation state (10 seconds)
2. **Throttle Calibration**: Maximum forearm flexor contraction (5 seconds)
3. **Yaw Calibration**: Maximum forearm extensor contraction (5 seconds)
4. **Pitch Calibration**: Maximum bicep contraction (5 seconds)
5. **Roll Calibration**: Maximum tricep contraction (5 seconds)

### Signal Quality Monitoring
- **Real-time SNR calculation** for each EMG channel
- **Cross-talk detection** between muscle groups
- **Fatigue monitoring** through signal degradation analysis
- **Control accuracy assessment** based on intended vs actual response

## Research Data Collection

The platform automatically logs comprehensive data for analysis:

### EMG Data (`data_output/emg_data/`)
- Raw EMG signals from all 4 channels
- Processed EMG signals after filtering
- Signal-to-noise ratio measurements
- Control accuracy metrics
- Fatigue indicators

### Flight Performance Data (`data_output/debug_logs/`)
- Real-time flight parameters (speed, altitude, position)
- Control inputs (throttle, yaw, pitch, roll)
- System response characteristics
- Session timestamps and duration

### Evaluation Reports (`data_output/reports/`)
- Session summary with key metrics
- Signal quality assessment
- Control accuracy analysis
- Performance benchmarks
- Statistical analysis ready format

## Flight Physics and Characteristics

### Research-Optimized Flight Model
- **Physics**: Realistic 6-DOF flight dynamics
- **Control Response**: Low-latency EMG to flight command mapping
- **Flight Envelope**: Full 3D maneuverability with ground collision detection
- **Performance**: Speeds up to 180 km/h with precise altitude control
- **Environment**: Simplified for focus on control validation

## Safety Considerations

### EMG Safety
- Use only medical-grade, skin-safe electrodes
- Replace electrodes after each session or when adhesion degrades
- Stop immediately if skin irritation occurs
- Clean electrode sites with alcohol after removal

### Electrical Safety
- Use only USB-powered Arduino (isolated from mains power)
- Verify BioAmp EXG Pill is designed for human EMG measurement
- Do not modify circuit connections while electrodes are attached
- Disconnect electrodes before making any hardware changes

### Signal Quality Assurance
- Maintain electrode impedance below 10kΩ
- Monitor for 50/60Hz noise pickup
- Verify muscle activation produces clear, repeatable EMG signals
- Document baseline and maximum signal levels for each session

## Performance Metrics & Validation

### EMG Signal Quality Metrics
- **Signal-to-Noise Ratio**: >20dB for reliable control
- **Response Latency**: <100ms from muscle activation to flight response
- **Control Accuracy**: ±5% deviation from intended control input
- **Cross-talk Rejection**: <10% interference between channels

### Flight Performance Benchmarks
- **Navigation Accuracy**: >90% accuracy within training scenarios
- **Control Precision**: Stable flight path maintenance
- **System Response**: Consistent EMG-to-flight control mapping
- **Fatigue Resistance**: <20% performance degradation in 30-minute sessions

## Research Applications

### Potential Studies
1. **System Characterization**: EMG signal quality and control precision measurement
2. **Response Latency Analysis**: Time from muscle activation to flight response
3. **Signal Processing Optimization**: Filter design and noise reduction effectiveness
4. **Control Mapping Evaluation**: Different EMG-to-command mapping strategies
5. **Hardware Validation**: Component performance and reliability testing
6. **User Training Protocols**: Learning curve analysis and skill acquisition
7. **Fatigue Analysis**: Muscle fatigue effects on control performance
8. **Accessibility Research**: Alternative control methods for motor impairments

### Experimental Protocol Recommendations

#### Participant Requirements
- **Age Range**: 18-65 years
- **Health Status**: No known neuromuscular disorders
- **Experience Level**: Mixed (novice to experienced operators)
- **Sample Size**: Minimum 20 participants for statistical significance

#### Study Design
1. **Baseline Assessment**: Traditional control method performance
2. **EMG Calibration**: Individual muscle activation mapping
3. **Training Phase**: 5 sessions, 30 minutes each, over 2 weeks
4. **Performance Testing**: Standardized scenarios for comparison
5. **Follow-up**: Retention testing after 1-week interval

## Troubleshooting

### Common Issues

**No Arduino Connection**:
- Verify COM port in Device Manager (Windows) or `ls /dev/tty*` (Linux)
- Check USB cable and Arduino power LED
- Ensure correct baud rate (115200)
- Try different USB port

**Poor EMG Signal Quality**:
- Re-clean skin with alcohol, ensure completely dry
- Check electrode contact and positioning
- Replace electrodes if signal is noisy
- Verify cable connections to BioAmp inputs
- Ensure proper muscle contraction technique

**Platform Crashes or Errors**:
- Check Python dependencies installation
- Verify all required files are present
- Review console output for specific error messages
- Ensure sufficient system resources available

## Advanced Features

### Signal Processing Pipeline
- **Band-pass filtering**: 74.5-149.5 Hz for EMG signals
- **Envelope detection**: Moving average with 128-sample buffer
- **Noise threshold**: Configurable minimum activation level
- **Adaptive calibration**: Real-time adjustment to user characteristics

### Data Analysis Tools
- **Real-time monitoring**: Live EMG signal visualization
- **Performance metrics**: Automated calculation of key indicators
- **Export capabilities**: CSV and JSON formats for external analysis
- **Statistical analysis**: Built-in correlation and trend analysis

## Contributing

This is an open-source research platform. Contributions welcome:
- Enhanced EMG signal processing algorithms
- Additional flight physics models
- Improved calibration procedures
- Data analysis and visualization tools
- Documentation improvements
- Bug reports and feature requests

## References

- BioAmp EXG Pill Documentation: [Upside Down Labs](https://upsidedownlabs.tech/)
- EMG Signal Processing: Butterworth filtering implementation
- HardwareX Journal Guidelines: [Elsevier HardwareX](https://www.journals.elsevier.com/hardwarex)
- Arduino Uno R4 Specifications: [Arduino Official](https://docs.arduino.cc/)
- Pygame Documentation: [pygame.org](https://www.pygame.org/docs/)

## License

This research platform is intended for academic and educational purposes. Always follow proper safety protocols when using EMG equipment and conducting human subjects research. Obtain appropriate institutional review board (IRB) approval for studies involving human participants.

## Support

For technical support, bug reports, or research collaboration inquiries, please refer to the project documentation or contact the development team through the appropriate academic channels.