# SOLUTION: Create a single unified config.py file
# Replace BOTH existing config.py files with this single version

# config.py - Unified Configuration for EMG Research Platform
"""
Single configuration file for the entire EMG research platform.
Contains core systems, physics, debug, and EMG-specific settings.
"""

class DebugConfig:
    """Debug and testing configuration flags"""
    
    # === RESEARCH MODE SETTINGS ===
    RESEARCH_MODE = True               # Force research-focused configuration
    EMPTY_ENVIRONMENT = True           # Force empty environment
    DISABLE_OBSTACLES = True           # Remove all obstacles for EMG focus
    
    # === PHYSICS TESTING ===
    DISABLE_TARGETS = False            # Keep targets for navigation research
    DISABLE_GROUND_COLLISION = False   # KEEP ground collision (primary challenge)
    DISABLE_OBSTACLE_COLLISION = True  # Disable obstacle collision (no obstacles)
    DISABLE_RANGE_LIMITS = False       # Keep range limits for realistic operation
    DISABLE_BATTERY_DRAIN = False      # Keep battery for realistic flight time
    
    # === SPAWN CONFIGURATION ===
    SAFE_SPAWN_ALTITUDE = 200          # Spawn at Y=200 for research
    
    # === VISUAL DEBUG ===
    SHOW_SPEED_DEBUG = True            # Show speed info on screen
    SHOW_POSITION_DEBUG = False        # Hide position for cleaner research UI
    SHOW_PHYSICS_DEBUG = False         # Hide physics debug for research
    VERBOSE_CONSOLE_OUTPUT = False     # Reduced console output for research
    
    # === ENVIRONMENT ===
    FORCE_RESEARCH_ENV = True          # Always use research environment
    
    @classmethod
    def is_testing_mode(cls):
        """Returns True if any testing flags are enabled"""
        return (cls.DISABLE_OBSTACLES or cls.DISABLE_GROUND_COLLISION or 
                cls.DISABLE_OBSTACLE_COLLISION or cls.EMPTY_ENVIRONMENT)
    
    @classmethod
    def print_research_status(cls):
        """Print research configuration status"""
        print("=== EMG FLIGHT CONTROL RESEARCH PLATFORM ===")
        print("Hardware: BioAmp EXG Pill + Arduino Uno R4")
        print("Research Focus: EMG signal validation and flight control")
        print("Environment: Obstacle-free (pure flight dynamics)")
        print("Primary Challenge: Ground collision detection")
        print("Data Collection: EMG signals + flight performance")
        print("Publication Target: HardwareX Journal")
        print("=" * 50)


class PhysicsConfig:
    """Physics tuning constants optimized for EMG research"""
    
    # Research-optimized drag values
    GENTLE_DRAG = 0.98       # Very smooth flight for EMG learning
    RESEARCH_DRAG = 0.985    # Balanced for EMG control research  
    REALISTIC_DRAG = 0.95    # Standard realistic physics
    HIGH_DRAG = 0.90         # High drag for stability
    
    # Research-optimized thrust values
    GENTLE_THRUST = 0.8      # Gentle for initial EMG calibration
    RESEARCH_THRUST = 1.2    # Balanced for research (REDUCED from 1.8)
    NORMAL_THRUST = 1.5      # Standard performance
    RACING_THRUST = 2.5      # High performance racing
    
    # ACTIVE VALUES - Optimized for EMG research
    ACTIVE_DRAG = RESEARCH_DRAG
    ACTIVE_THRUST = RESEARCH_THRUST  # Gentler thrust for better EMG control
    
    # Ground collision altitude (world Y coordinate)
    GROUND_COLLISION_Y = 590  # Crash when Y >= this value


class EMGConfig:
    """EMG-specific configuration for BioAmp EXG Pill research"""
    
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
    THROTTLE_CHANNEL = 0             # A0 - Forearm flexor (wrist flexion)
    YAW_CHANNEL = 1                  # A1 - Forearm extensor (wrist extension)
    PITCH_CHANNEL = 2                # A2 - Bicep brachii (elbow flexion)
    ROLL_CHANNEL = 3                 # A3 - Tricep brachii (elbow extension)
    
    # === MUSCLE GROUPS ===
    MUSCLE_MAPPING = {
        'throttle': 'Forearm Flexor (Wrist Flexion)',
        'yaw': 'Forearm Extensor (Wrist Extension)', 
        'pitch': 'Bicep Brachii (Elbow Flexion)',
        'roll': 'Tricep Brachii (Elbow Extension)'
    }
    
    # === SIGNAL QUALITY METRICS ===
    MIN_SNR_DB = 15                  # Minimum acceptable signal-to-noise ratio
    MAX_CROSSTALK_PERCENT = 25       # Maximum acceptable inter-channel interference
    TARGET_RESPONSE_MS = 100         # Target system response time
    
    # === EVALUATION CRITERIA ===
    CONTROL_ACCURACY_TARGET = 85     # Realistic target control accuracy percentage
    FATIGUE_THRESHOLD_PERCENT = 30   # Maximum acceptable performance degradation
    
    # === DISPLAY SETTINGS ===
    SHOW_EMG_SIGNALS = True          # Show real-time EMG values
    SHOW_SIGNAL_QUALITY = True       # Show SNR and signal quality metrics
    SHOW_EMG_HUD = True              # Show EMG evaluation HUD
    EMG_HUD_POSITION = "top_right"   # Position: "top_left", "top_right", "bottom_left", "bottom_right"
    
    # === RESEARCH PARAMETERS ===
    SESSION_DURATION_MINUTES = 10    # Target research session length
    CALIBRATION_REQUIRED = True      # Require calibration before flight
    AUTO_SAVE_DATA = True            # Automatically save research data
    
    # === CONTROL SENSITIVITY ===
    THROTTLE_SENSITIVITY = 0.3       # Reduced throttle sensitivity for gentle takeoff
    YAW_SENSITIVITY = 0.5            # Yaw control sensitivity
    PITCH_SENSITIVITY = 0.5          # Pitch control sensitivity  
    ROLL_SENSITIVITY = 0.5           # Roll control sensitivity


class UIConfig:
    """User interface configuration for research platform"""
    
    # === SCREEN LAYOUT ===
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 800
    
    # === HUD POSITIONING ===
    EMG_PANEL_WIDTH = 280
    EMG_PANEL_HEIGHT = 350
    EMG_PANEL_X = SCREEN_WIDTH - EMG_PANEL_WIDTH - 10  # Top-right position
    EMG_PANEL_Y = 10
    
    # === COLORS ===
    EMG_PANEL_BG = (0, 0, 0, 180)    # Semi-transparent black
    SUCCESS_COLOR = (0, 255, 0)       # Green
    WARNING_COLOR = (255, 255, 0)     # Yellow  
    ERROR_COLOR = (255, 0, 0)         # Red
    INFO_COLOR = (0, 150, 255)        # Blue
    
    # === FONTS ===
    FONT_LARGE_SIZE = 32
    FONT_MEDIUM_SIZE = 24
    FONT_SMALL_SIZE = 18


class DataConfig:
    """Data logging and research output configuration"""
    
    # === DIRECTORY STRUCTURE ===
    BASE_DATA_DIR = "data_output"
    DEBUG_LOGS_DIR = f"{BASE_DATA_DIR}/debug_logs"
    EMG_DATA_DIR = f"{BASE_DATA_DIR}/emg_data"
    REPORTS_DIR = f"{BASE_DATA_DIR}/reports"
    
    # === LOGGING SETTINGS ===
    LOG_EMG_SIGNALS = True           # Log raw EMG signals
    LOG_PROCESSED_SIGNALS = True     # Log processed EMG signals
    LOG_FLIGHT_DATA = True           # Log drone position/velocity/rotation
    LOG_PERFORMANCE_METRICS = True   # Log control accuracy, fatigue, etc.
    
    # === FILE FORMATS ===
    EMG_LOG_FORMAT = "csv"           # CSV for easy analysis
    REPORT_FORMAT = "json"           # JSON for structured data
    DEBUG_LOG_FORMAT = "txt"         # Text for human reading
    
    # === RESEARCH METADATA ===
    RESEARCH_VERSION = "1.0"
    PLATFORM_NAME = "EMG-FPV-Research"
    HARDWARE_CONFIG = "BioAmp_EXG_Pill_Arduino_R4"


# === VALIDATION FUNCTIONS ===

def validate_configuration():
    """Validate configuration settings for research platform"""
    issues = []
    
    # Check EMG configuration
    if EMGConfig.THROTTLE_SENSITIVITY > 1.0:
        issues.append("EMG throttle sensitivity too high - risk of sudden takeoff")
    
    if not DebugConfig.DISABLE_GROUND_COLLISION:
        print("✓ Ground collision enabled - primary research challenge active")
    else:
        issues.append("Ground collision disabled - remove this for research")
    
    if DebugConfig.DISABLE_OBSTACLES:
        print("✓ Obstacles disabled - clean research environment")
    
    # Check physics
    if PhysicsConfig.ACTIVE_THRUST > 2.0:
        issues.append("Thrust too high - may cause control difficulties")
    
    if issues:
        print("⚠️  Configuration Issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✓ Configuration validated - ready for research")
        return True


def print_current_configuration():
    """Print current configuration summary"""
    print("\n" + "=" * 60)
    print("CURRENT RESEARCH PLATFORM CONFIGURATION")
    print("=" * 60)
    
    print(f"Research Mode: {'ENABLED' if DebugConfig.RESEARCH_MODE else 'DISABLED'}")
    print(f"EMG Hardware: BioAmp EXG Pill @ {EMGConfig.BAUD_RATE} baud")
    print(f"Sampling Rate: {EMGConfig.SAMPLE_RATE} Hz")
    print(f"Throttle Sensitivity: {EMGConfig.THROTTLE_SENSITIVITY}")
    print(f"Active Thrust: {PhysicsConfig.ACTIVE_THRUST}")
    print(f"Active Drag: {PhysicsConfig.ACTIVE_DRAG}")
    print(f"Ground Collision: {'ENABLED' if not DebugConfig.DISABLE_GROUND_COLLISION else 'DISABLED'}")
    print(f"EMG HUD: {'ENABLED' if EMGConfig.SHOW_EMG_HUD else 'DISABLED'}")
    print(f"Data Logging: {'ENABLED' if DataConfig.LOG_EMG_SIGNALS else 'DISABLED'}")
    
    print("=" * 60)
    
    return validate_configuration()


# === INITIALIZATION ===
if __name__ == "__main__":
    # Run configuration validation when imported
    print_current_configuration()