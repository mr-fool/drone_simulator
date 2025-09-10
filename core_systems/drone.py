from vector3 import Vector3
from physics_manager import physics_manager
from config import DebugConfig, PhysicsConfig


import math

class FPVDrone:
    def __init__(self, x=0, y=300, z=0, max_speed_kmh=180, max_range_km=5):
        self.position = Vector3(x, y, z)
        self.velocity = Vector3(0, 0, 0)
        self.rotation = Vector3(0, 0, 0)  # pitch, yaw, roll
        self.size = 25
        self.crashed = False
        self.start_position = Vector3(x, y, z)  # For range calculation
        
        # User-configurable parameters
        self.max_speed_kmh = max_speed_kmh
        self.max_range_km = max_range_km
        self.max_speed_ms = max_speed_kmh / 3.6  # Convert to m/s for physics
        self.max_range_m = max_range_km * 1000   # Convert to meters
        
        # FIXED: FPV Racing Drone characteristics - properly balanced for high performance
        self.battery = 100.0
        
        # CONFIGURABLE: Physics constants from config file
        self.drag = PhysicsConfig.ACTIVE_DRAG
        self.gravity = 0.08  # Keep gravity constant for now
        self.thrust_power = PhysicsConfig.ACTIVE_THRUST
        
        # Enhanced control responsiveness for FPV racing
        self.rotation_speed = 6.0  # Increased agility
        self.flight_ceiling = 500  # High altitude capability
        
        # Performance tracking
        self.max_speed_achieved = 0.0
        self.total_distance_traveled = 0.0
        self.previous_position = Vector3(x, y, z)
        
        # ADDED: Frame rate compensation
        self.target_fps = 60.0
        self.dt = 1.0 / self.target_fps  # Delta time for physics calculations

    def update_physics(self, throttle, yaw, pitch, roll, emg_signals=None):
        """Update FPV drone physics with FIXED performance characteristics and debug overrides"""
        if self.crashed:
            return
            
        # Store previous position for distance tracking
        self.previous_position = Vector3(self.position.x, self.position.y, self.position.z)
        
        # FIXED: Gravity application - reduced and frame rate independent
        gravity_force = self.gravity * self.dt * 60  # Normalize for 60 FPS
        self.velocity.y += gravity_force
        
        # FIXED: Throttle provides powerful upward thrust for racing performance
        if throttle > 0:
            # FIXED: Much more gradual and realistic throttle response
            base_thrust = 0.25  # Reduced from much higher value
            thrust_force = throttle * base_thrust * self.dt * 60
            
            # Gradual upward acceleration instead of instant launch
            self.velocity.y -= thrust_force  # Upward thrust
            
            # FIXED: Reduced forward momentum from throttle
            heading_rad = math.radians(self.rotation.y)
            forward_thrust = throttle * 0.05 * self.dt * 60  # Much reduced from 0.8
            self.velocity.x += math.sin(heading_rad) * forward_thrust
            self.velocity.z += math.cos(heading_rad) * forward_thrust
        
        # ENHANCED: Much more responsive rotational control for racing
        rotation_factor = self.rotation_speed * self.dt * 60
        
        # Apply rotational movements with proper frame rate compensation
        self.rotation.x += pitch * rotation_factor  # pitch
        self.rotation.z += roll * rotation_factor   # roll
        
        # IMPROVED: Banking and turning physics for realistic flight
        heading_rad = math.radians(self.rotation.y)
        pitch_rad = math.radians(self.rotation.x)
        
        # Roll creates banking turns (main turning mechanism)
        if abs(roll) > 0.05:
            # Banking turn - roll affects heading change
            bank_turn_rate = roll * rotation_factor * 0.8
            self.rotation.y = (self.rotation.y + bank_turn_rate) % 360
            
            # Banking also creates lateral movement
            bank_force = roll * 0.6 * self.dt * 60
            self.velocity.x += math.cos(heading_rad) * bank_force
            self.velocity.z -= math.sin(heading_rad) * bank_force
        
        # Pitch affects forward/backward movement (climbing/diving)
        if abs(pitch) > 0.05:
            pitch_force = pitch * 0.4 * self.dt * 60
            # Forward/backward based on pitch
            self.velocity.x += math.sin(heading_rad) * pitch_force
            self.velocity.z += math.cos(heading_rad) * pitch_force
            # Vertical component from pitch
            self.velocity.y -= pitch * 0.2 * self.dt * 60
        
        # Yaw provides additional turning control (rudder-like)
        if abs(yaw) > 0.05:
            yaw_rate = yaw * rotation_factor * 0.4
            self.rotation.y = (self.rotation.y + yaw_rate) % 360
        
        # FIXED: Much lower drag for high-speed capability
        # Apply drag with proper frame rate compensation
        drag_factor = pow(self.drag, self.dt * 60)  # Exponential drag decay
        self.velocity = self.velocity * drag_factor
        
        # FIXED: Speed limiting - allow much higher speeds
        current_speed = self.velocity.magnitude()
        if current_speed > self.max_speed_ms:
            # Soft speed limiting instead of hard cap
            excess_ratio = current_speed / self.max_speed_ms
            if excess_ratio > 1.1:  # Only limit if significantly over
                self.velocity = self.velocity * (self.max_speed_ms / current_speed)
        
        # ADDED: Speed boost for racing performance at high throttle
        if throttle > 0.8:  # High throttle gives extra performance
            boost_factor = 1.0 + (throttle - 0.8) * 0.5  # Up to 10% boost
            forward_vector = Vector3(
                math.sin(heading_rad),
                0,
                math.cos(heading_rad)
            )
            boost_velocity = forward_vector * (throttle * 2.0 * self.dt * 60)
            self.velocity = self.velocity + boost_velocity
            
        # Update position with frame rate compensation
        position_delta = self.velocity * (self.dt * 60)
        self.position = self.position + position_delta
        
        # Track performance metrics
        current_speed_kmh = self.get_speed_kmh()
        if current_speed_kmh > self.max_speed_achieved:
            self.max_speed_achieved = current_speed_kmh
            
        # Calculate distance traveled this frame
        distance_delta = math.sqrt((self.position.x - self.previous_position.x)**2 + 
                                (self.position.y - self.previous_position.y)**2 + 
                                (self.position.z - self.previous_position.z)**2)
        self.total_distance_traveled += distance_delta
        
        # CONFIGURABLE: Battery consumption with debug override
        if not DebugConfig.DISABLE_BATTERY_DRAIN:
            # Racing drones: 3-8 minutes flight time depending on flying style
            # Target: 100% battery = 5 minutes of aggressive flying
            base_power_per_frame = 100.0 / (5 * 60 * self.target_fps)  # 5 minutes at 60 FPS
            
            # Control activity power calculation
            if emg_signals:
                control_activity = (abs(emg_signals[0]) + abs(emg_signals[1]) + 
                                abs(emg_signals[2]) + abs(emg_signals[3])) / 4.0
            else:
                control_activity = (abs(throttle) + abs(yaw) + abs(pitch) + abs(roll)) / 4.0
            
            # Activity multiplier: gentle = 1x, aggressive = 3x power consumption
            activity_multiplier = 1.0 + (control_activity * 2.0)
            
            # Speed power penalty (realistic for racing drones)
            speed_ratio = current_speed / self.max_speed_ms
            speed_multiplier = 1.0 + (speed_ratio * speed_ratio * 1.0)  # Quadratic power increase
            
            # Total power consumption with frame rate compensation
            total_power_drain = base_power_per_frame * activity_multiplier * speed_multiplier * (self.dt * 60)
            self.battery = max(0, self.battery - total_power_drain)
        
        # CONFIGURABLE: Range limit enforcement with debug override
        if not DebugConfig.DISABLE_RANGE_LIMITS:
            distance_from_start = math.sqrt((self.position.x - self.start_position.x)**2 + 
                                        (self.position.y - self.start_position.y)**2 + 
                                        (self.position.z - self.start_position.z)**2)
            
            if distance_from_start > self.max_range_m:
                # Soft range limitation - gradual pushback
                direction_to_start = Vector3(
                    self.start_position.x - self.position.x,
                    self.start_position.y - self.position.y, 
                    self.start_position.z - self.position.z
                )
                direction_length = direction_to_start.magnitude()
                if direction_length > 0:
                    pushback_strength = (distance_from_start - self.max_range_m) / 100.0
                    direction_normalized = direction_to_start * (1.0 / direction_length)
                    self.velocity = self.velocity + (direction_normalized * pushback_strength)
        
        # Ground collision - use unified coordinate system
        if physics_manager.is_ground_collision(self.position.y):
            self.position.y = physics_manager.CRASH_THRESHOLD
            # Note: Crashed flag is set in main.py collision detection to respect debug flags
            if not DebugConfig.DISABLE_GROUND_COLLISION:
                self.crashed = True
                
        # FIXED: Soft flight ceiling that allows controlled descent
        max_ceiling_y = 300 - self.flight_ceiling  # Y = -200
        if self.position.y < max_ceiling_y:
            # Soft ceiling - apply downward force instead of hard constraint
            ceiling_distance = abs(max_ceiling_y - self.position.y)  # Use abs() for magnitude
            downward_force = ceiling_distance * 0.1  # Gentle push down
            self.velocity.y += downward_force  # This pushes DOWN (positive Y)
            
            # Only hard-limit at extreme altitude
            if self.position.y < max_ceiling_y - 50:  # 50m buffer above ceiling
                self.position.y = max_ceiling_y - 50
            
        # Boundary limits
        self.position.x = max(-400, min(1200, self.position.x))
        self.position.z = max(-400, min(400, self.position.z))
    
    def get_speed_kmh(self):
        """Get current speed in km/h"""
        speed_ms = self.velocity.magnitude()
        return speed_ms * 3.6  # Convert m/s to km/h
        
    def get_range_from_start_km(self):
        """Get current distance from starting position in km"""
        distance_m = math.sqrt((self.position.x - self.start_position.x)**2 + 
                              (self.position.y - self.start_position.y)**2 + 
                              (self.position.z - self.start_position.z)**2)
        return distance_m / 1000.0  # Convert to km
        
    def get_total_distance_km(self):
        """Get total distance traveled in km"""
        return self.total_distance_traveled / 1000.0