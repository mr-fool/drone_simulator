# config.py - Debug and Testing Configuration
"""
Central configuration for debugging and testing the FPV drone simulator.
Change these flags to enable/disable features during development.
"""

class DebugConfig:
    """Debug and testing configuration flags"""
    
    # === PHYSICS TESTING ===
    DISABLE_OBSTACLES = True           # Remove all obstacles for speed testing
    DISABLE_TARGETS = True             # Remove all targets/checkpoints
    DISABLE_GROUND_COLLISION = True    # Disable ground crash detection
    DISABLE_OBSTACLE_COLLISION = True  # Disable obstacle crash detection
    DISABLE_RANGE_LIMITS = True        # Disable max range enforcement
    DISABLE_BATTERY_DRAIN = True       # Infinite battery for testing
    
    # === SPAWN CONFIGURATION ===
    SAFE_SPAWN_ALTITUDE = 200          # Spawn at Y=200 instead of Y=300
    
    # === VISUAL DEBUG ===
    SHOW_SPEED_DEBUG = True            # Show speed info on screen
    SHOW_POSITION_DEBUG = True         # Show position coordinates
    SHOW_PHYSICS_DEBUG = True          # Show physics values (thrust, drag, etc.)
    VERBOSE_CONSOLE_OUTPUT = True      # Extra console logging
    
    # === CONTROL TESTING ===
    SIMPLIFIED_CONTROLS = False        # Use simplified keyboard controls
    AUTO_THROTTLE = False              # Automatic throttle for hands-free testing
    
    # === ENVIRONMENT ===
    EMPTY_ENVIRONMENT = True           # Force empty environment regardless of selection
    
    @classmethod
    def is_testing_mode(cls):
        """Returns True if any testing flags are enabled"""
        return (cls.DISABLE_OBSTACLES or cls.DISABLE_GROUND_COLLISION or 
                cls.DISABLE_OBSTACLE_COLLISION or cls.EMPTY_ENVIRONMENT)
    
    @classmethod
    def print_active_flags(cls):
        """Print which debug flags are currently active"""
        if cls.is_testing_mode():
            print("=== DEBUG MODE ACTIVE ===")
            active_flags = []
            
            if cls.DISABLE_OBSTACLES: active_flags.append("No Obstacles")
            if cls.DISABLE_TARGETS: active_flags.append("No Targets")  
            if cls.DISABLE_GROUND_COLLISION: active_flags.append("No Ground Collision")
            if cls.DISABLE_OBSTACLE_COLLISION: active_flags.append("No Obstacle Collision")
            if cls.DISABLE_RANGE_LIMITS: active_flags.append("No Range Limits")
            if cls.DISABLE_BATTERY_DRAIN: active_flags.append("Infinite Battery")
            if cls.EMPTY_ENVIRONMENT: active_flags.append("Empty Environment")
            
            print(f"Active: {', '.join(active_flags)}")
            print("=== Change flags in config.py ===")
        else:
            print("Debug mode: OFF - Full simulation active")

    @classmethod
    def print_research_status(cls):
        """Print research configuration status"""
        print("=== EMG RESEARCH MODE ===")
        print("BioAmp EXG Pill + Arduino Uno R4")
        print("Focus: EMG signal validation and flight control")
        print("Environment: Empty (obstacles removed)")
        print("Challenges: Ground collision, navigation, battery management")
        print("Data Collection: EMG signals + flight performance")
        print("=============================")
        
class PhysicsConfig:
    """Physics tuning constants - easy to modify for testing"""
    
    # Drag values for different testing scenarios
    RACING_DRAG = 0.985      # Low drag for high speed
    REALISTIC_DRAG = 0.95    # More realistic drag
    HIGH_DRAG = 0.90         # High drag for stability testing
    
    # Thrust values
    RACING_THRUST = 2.5      # High performance racing
    NORMAL_THRUST = 1.5      # Balanced performance  
    LOW_THRUST = 0.8         # Conservative thrust
    
    # Currently active values (change these for testing)
    ACTIVE_DRAG = RACING_DRAG
    ACTIVE_THRUST = RACING_THRUST
    
    # Ground collision altitude (world Y coordinate)
    GROUND_COLLISION_Y = 590  # Crash when Y >= this value

class EMGConfig:
    """EMG-specific configuration for BioAmp EXG Pill"""
    
    # === HARDWARE SETTINGS ===
    ARDUINO_PORT = 'COM3'            # Update for your system
    BAUD_RATE = 115200               # BioAmp EXG Pill standard rate
    SAMPLE_RATE = 500                # Hz - Arduino sampling rate
    
    # === EMG PROCESSING ===
    NOISE_THRESHOLD = 25             # Minimum signal for intentional control
    EMG_MAX_VALUE = 100              # Maximum expected EMG amplitude
    CALIBRATION_SAMPLES = 1000       # Samples for baseline calibration
    
    # === CHANNEL MAPPING ===
    # BioAmp EXG Pill 4-channel configuration
    THROTTLE_CHANNEL = 0             # A0 - Forearm flexor
    YAW_CHANNEL = 1                  # A1 - Forearm extensor  
    PITCH_CHANNEL = 2                # A2 - Bicep brachii
    ROLL_CHANNEL = 3                 # A3 - Tricep brachii
    
    # === SIGNAL QUALITY METRICS ===
    MIN_SNR_DB = 20                  # Minimum signal-to-noise ratio
    MAX_CROSSTALK_PERCENT = 10       # Maximum inter-channel interference
    TARGET_RESPONSE_MS = 100         # Target system response time
    
    # === EVALUATION CRITERIA ===
    CONTROL_ACCURACY_TARGET = 95     # Target control accuracy percentage
    FATIGUE_THRESHOLD_PERCENT = 20   # Maximum acceptable performance degradation
    
    # === DISPLAY SETTINGS ===
    SHOW_EMG_SIGNALS = True          # Show real-time EMG values
    SHOW_SIGNAL_QUALITY = True       # Show SNR and signal quality metrics