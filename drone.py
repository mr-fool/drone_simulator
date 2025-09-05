from vector3 import Vector3
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
        
        # FPV Racing Drone characteristics
        self.battery = 100.0
        self.drag = 0.92  # Air resistance
        self.gravity = 0.15  # Gravity effect
        self.thrust_power = 0.5  # High thrust-to-weight ratio
        self.rotation_speed = 4.0  # Very agile rotation
        self.flight_ceiling = 500  # High altitude capability
        
        # Performance tracking
        self.max_speed_achieved = 0.0
        self.total_distance_traveled = 0.0
        self.previous_position = Vector3(x, y, z)

    def update_physics(self, throttle, yaw, pitch, roll, emg_signals=None):
        """Update FPV drone physics with user-configurable limits"""
        if self.crashed:
            return
            
        # Store previous position for distance tracking
        self.previous_position = Vector3(self.position.x, self.position.y, self.position.z)
            
        # Apply gravity
        self.velocity.y += self.gravity
        
        # Throttle provides direct upward thrust
        if throttle > 0:
            thrust_force = throttle * self.thrust_power
            self.velocity.y -= thrust_force
            
        # Apply rotational movements (very responsive for racing)
        self.rotation.x += pitch * self.rotation_speed  # pitch
        self.rotation.z += roll * self.rotation_speed   # roll
        
        # Convert rotation to movement (acrobatic capabilities)
        # Use roll for main turning (like real aircraft)
        heading_rad = math.radians(self.rotation.y)
        forward_speed = -pitch * 0.15  # High forward speed capability
        
        # Roll creates turning by banking the aircraft
        if abs(roll) > 0.1:
            # When rolling, change heading (yaw) and create turning motion
            self.rotation.y = (self.rotation.y + roll * self.rotation_speed * 0.5) % 360  # Roll affects heading
            
            # Banking creates coordinated turn
            side_speed = roll * 0.15
            self.velocity.x += math.sin(heading_rad) * forward_speed + math.cos(heading_rad) * side_speed
            self.velocity.z += math.cos(heading_rad) * forward_speed - math.sin(heading_rad) * side_speed
        else:
            # No roll - straight flight
            self.velocity.x += math.sin(heading_rad) * forward_speed
            self.velocity.z += math.cos(heading_rad) * forward_speed
        
        # Yaw provides additional turning control (like rudder)
        if abs(yaw) > 0.1:
            self.rotation.y = (self.rotation.y + yaw * self.rotation_speed * 0.3) % 360  # Less effect than roll
        
        # Apply drag
        self.velocity = self.velocity * self.drag
        
        # Limit maximum speed to user-configured value
        speed = self.velocity.magnitude()
        if speed > self.max_speed_ms:
            self.velocity = self.velocity * (self.max_speed_ms / speed)
            
        # Update position
        self.position = self.position + self.velocity
        
        # Track performance metrics
        current_speed_kmh = self.get_speed_kmh()
        if current_speed_kmh > self.max_speed_achieved:
            self.max_speed_achieved = current_speed_kmh
            
        # Calculate distance traveled this frame
        distance_delta = math.sqrt((self.position.x - self.previous_position.x)**2 + 
                                 (self.position.y - self.previous_position.y)**2 + 
                                 (self.position.z - self.previous_position.z)**2)
        self.total_distance_traveled += distance_delta
        
        # Battery consumption (realistic for FPV drones: 10-30 min flight time)
        # At 60 FPS, 15 minutes = 54,000 frames
        # Target: 100% battery should last ~15 minutes of moderate flying
        
        # Base power consumption (always draining, like hover power)
        base_power_per_frame = 100.0 / (15 * 60 * 60)  # 15 minutes at 60 FPS
        
        # Control activity power (aggressive flying uses more power)
        if emg_signals:
            control_activity = (abs(emg_signals[0]) + abs(emg_signals[1]) + 
                               abs(emg_signals[2]) + abs(emg_signals[3])) / 4.0  # Average activity 0-1
        else:
            # Fallback to using current control inputs
            control_activity = (abs(throttle) + abs(yaw) + abs(pitch) + abs(roll)) / 4.0
        
        # Activity multiplier: gentle flying = 1x, aggressive = 2x power consumption
        activity_multiplier = 1.0 + control_activity
        
        # Speed power penalty (high speed = more drag = more power)
        speed_ratio = speed / self.max_speed_ms
        speed_multiplier = 1.0 + (speed_ratio * 0.5)  # Up to 50% more power at max speed
        
        # Total power consumption per frame
        total_power_drain = base_power_per_frame * activity_multiplier * speed_multiplier
        
        # Apply battery drain
        self.battery = max(0, self.battery - total_power_drain)
        
        # Check range limit
        distance_from_start = math.sqrt((self.position.x - self.start_position.x)**2 + 
                                      (self.position.y - self.start_position.y)**2 + 
                                      (self.position.z - self.start_position.z)**2)
        
        if distance_from_start > self.max_range_m:
            # Force return to within range (simulates range limitation)
            direction_to_start = Vector3(
                self.start_position.x - self.position.x,
                self.start_position.y - self.position.y, 
                self.start_position.z - self.position.z
            )
            direction_length = direction_to_start.magnitude()
            if direction_length > 0:
                # Normalize and scale to bring back within range
                direction_normalized = direction_to_start * (1.0 / direction_length)
                # Push back towards start position
                self.position = self.position + (direction_normalized * 2.0)
        
        # Ground collision
        if self.position.y > 580:
            self.position.y = 580
            self.crashed = True
            
        # Flight ceiling
        if self.position.y < (300 - self.flight_ceiling):
            self.position.y = 300 - self.flight_ceiling
            
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