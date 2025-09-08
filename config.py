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