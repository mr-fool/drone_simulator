# config.py - Core Systems Configuration
"""
Core configuration for physics, drone, and HUD systems.
Focused on essential flight simulation parameters.
"""

class DebugConfig:
    """Basic debug configuration for core systems"""
    
    # === PHYSICS TESTING ===
    DISABLE_OBSTACLES = True           # Remove all obstacles for speed testing
    DISABLE_TARGETS = False            # Keep simple waypoints for navigation tasks
    DISABLE_GROUND_COLLISION = False   # Keep ground crash detection
    DISABLE_OBSTACLE_COLLISION = True  # Disable obstacle crash detection
    DISABLE_RANGE_LIMITS = False       # Keep range limits for realistic operation
    DISABLE_BATTERY_DRAIN = False      # Keep battery for realistic flight time
    
    # === SPAWN CONFIGURATION ===
    SAFE_SPAWN_ALTITUDE = 200          # Spawn at Y=200 for testing
    
    # === VISUAL DEBUG ===
    SHOW_SPEED_DEBUG = True            # Show speed info on screen
    SHOW_POSITION_DEBUG = True         # Show position coordinates
    SHOW_PHYSICS_DEBUG = True          # Show physics values (thrust, drag, etc.)
    VERBOSE_CONSOLE_OUTPUT = True      # Extra console logging
    
    # === ENVIRONMENT ===
    EMPTY_ENVIRONMENT = True           # Force empty environment
    
    @classmethod
    def is_testing_mode(cls):
        """Returns True if any testing flags are enabled"""
        return (cls.DISABLE_OBSTACLES or cls.DISABLE_GROUND_COLLISION or 
                cls.DISABLE_OBSTACLE_COLLISION or cls.EMPTY_ENVIRONMENT)
    
    @classmethod
    def print_research_status(cls):
        """Print core systems status"""
        print("=== CORE SYSTEMS ACTIVE ===")
        print("Physics: Enabled")
        print("Ground Collision: Enabled")
        print("Obstacles: Disabled")
        print("============================")


class PhysicsConfig:
    """Physics tuning constants for core systems"""
    
    # Drag values for different scenarios
    RACING_DRAG = 0.985      # Low drag for high speed
    REALISTIC_DRAG = 0.95    # More realistic drag
    HIGH_DRAG = 0.90         # High drag for stability
    
    # Thrust values
    RACING_THRUST = 2.5      # High performance racing
    NORMAL_THRUST = 1.5      # Balanced performance  
    LOW_THRUST = 0.8         # Conservative thrust
    
    # Research optimized values
    RESEARCH_DRAG = 0.985    # Optimized for smooth flight
    RESEARCH_THRUST = 1.8    # Balanced thrust for EMG control
    
    # Currently active values
    ACTIVE_DRAG = RESEARCH_DRAG
    ACTIVE_THRUST = RESEARCH_THRUST
    
    # Ground collision altitude (world Y coordinate)
    GROUND_COLLISION_Y = 590  # Crash when Y >= this value

# Add this to core_systems/config.py at the end

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