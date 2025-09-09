import math
from vector3 import Vector3

class PhysicsManager:
    """Centralized physics and coordinate system management for FPV drone simulator"""
    
    def __init__(self, screen_width=1200, screen_height=800):
        # Display constants
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        
        # CRITICAL: Unified coordinate system constants
        self.GROUND_LEVEL = 600.0  # World Y coordinate where ground is located
        self.CRASH_THRESHOLD = 590.0  # Crash slightly above ground
        self.FLIGHT_CEILING = 500.0  # Maximum altitude above starting position
        self.STARTING_ALTITUDE = 300.0  # Default drone starting Y position
        
        # World boundaries
        self.WORLD_MIN_X = -400.0
        self.WORLD_MAX_X = 1200.0
        self.WORLD_MIN_Z = -400.0
        self.WORLD_MAX_Z = 400.0
        
        # Physics constants (consistent across all systems)
        self.GRAVITY = 0.08  # Gravity acceleration per frame at 60 FPS
        self.TARGET_FPS = 60.0
        self.FRAME_TIME = 1.0 / self.TARGET_FPS
        
        # Projection constants
        self.FOV_DEGREES = 90.0
        self.FOV_RADIANS = math.radians(self.FOV_DEGREES)
        self.FOCAL_LENGTH = self.SCREEN_WIDTH / (2 * math.tan(self.FOV_RADIANS / 2))
        
        # Collision detection constants
        self.COLLISION_TOLERANCE = 25.0  # Base collision radius
        self.TARGET_COLLECTION_RADIUS = 30.0  # Base target collection radius
        
    def get_altitude_from_world_y(self, world_y):
        """Convert world Y coordinate to altitude above ground"""
        return max(0.0, self.GROUND_LEVEL - world_y)
    
    def get_world_y_from_altitude(self, altitude):
        """Convert altitude above ground to world Y coordinate"""
        return self.GROUND_LEVEL - altitude
    
    def is_ground_collision(self, world_y):
        """Check if position represents ground collision"""
        return world_y >= self.CRASH_THRESHOLD
    
    def is_ceiling_collision(self, world_y):
        """Check if position hits flight ceiling"""
        return world_y <= (self.STARTING_ALTITUDE - self.FLIGHT_CEILING)
    
    def clamp_to_world_bounds(self, position):
        """Clamp position to world boundaries"""
        return Vector3(
            max(self.WORLD_MIN_X, min(self.WORLD_MAX_X, position.x)),
            position.y,  # Y handled separately by collision checks
            max(self.WORLD_MIN_Z, min(self.WORLD_MAX_Z, position.z))
        )
    
    def project_3d_to_screen(self, world_pos, camera_pos, camera_rotation):
        """Unified 3D to 2D projection for all systems"""
        # Calculate camera transform
        yaw_rad = math.radians(camera_rotation.y)
        pitch_rad = math.radians(camera_rotation.x)
        roll_rad = math.radians(camera_rotation.z)
        
        # Forward vector (where camera is looking)
        forward = Vector3(
            math.sin(yaw_rad) * math.cos(pitch_rad),
            -math.sin(pitch_rad),
            math.cos(yaw_rad) * math.cos(pitch_rad)
        )
        
        # Up vector affected by roll
        up = Vector3(
            math.sin(roll_rad),
            math.cos(roll_rad),
            0
        )
        
        # Right vector (cross product)
        right = Vector3(
            forward.z * up.y - forward.y * up.z,
            forward.x * up.z - forward.z * up.x,
            forward.y * up.x - forward.x * up.y
        )
        
        # Transform world position to camera space
        relative_pos = Vector3(
            world_pos.x - camera_pos.x,
            world_pos.y - camera_pos.y,
            world_pos.z - camera_pos.z
        )
        
        # Project onto camera's coordinate system
        x_cam = relative_pos.x * right.x + relative_pos.y * right.y + relative_pos.z * right.z
        y_cam = relative_pos.x * up.x + relative_pos.y * up.y + relative_pos.z * up.z
        z_cam = relative_pos.x * forward.x + relative_pos.y * forward.y + relative_pos.z * forward.z
        
        # Check if behind camera
        if z_cam <= 0.1:
            return None
        
        # Perspective projection
        screen_x = self.SCREEN_WIDTH // 2 + (x_cam * self.FOCAL_LENGTH / z_cam)
        screen_y = self.SCREEN_HEIGHT // 2 - (y_cam * self.FOCAL_LENGTH / z_cam)
        
        return int(screen_x), int(screen_y), z_cam
    
    def project_3d_to_isometric(self, world_pos):
        """Isometric projection for top-down/tactical views"""
        screen_x = self.SCREEN_WIDTH // 2 + (world_pos.x - world_pos.z * 0.5) * 0.8
        screen_y = self.SCREEN_HEIGHT // 2 + (world_pos.y + (world_pos.x + world_pos.z) * 0.2) * 0.6
        return int(screen_x), int(screen_y)
    
    def check_3d_collision(self, pos1, pos2, radius1, radius2):
        """3D collision detection between two objects"""
        distance = math.sqrt(
            (pos1.x - pos2.x)**2 + 
            (pos1.y - pos2.y)**2 + 
            (pos1.z - pos2.z)**2
        )
        return distance < (radius1 + radius2)
    
    def check_screen_space_collision(self, obj1_screen, obj2_screen, threshold_distance):
        """2D screen space collision for FPV view"""
        if obj1_screen is None or obj2_screen is None:
            return False
        
        screen_distance = math.sqrt(
            (obj1_screen[0] - obj2_screen[0])**2 + 
            (obj1_screen[1] - obj2_screen[1])**2
        )
        return screen_distance < threshold_distance
    
    def check_crosshair_alignment(self, screen_pos, tolerance=40):
        """Check if screen position is aligned with center crosshair"""
        if screen_pos is None:
            return False
        
        center_x = self.SCREEN_WIDTH // 2
        center_y = self.SCREEN_HEIGHT // 2
        
        distance = math.sqrt(
            (screen_pos[0] - center_x)**2 + 
            (screen_pos[1] - center_y)**2
        )
        return distance < tolerance
    
    def calculate_horizon_position(self, camera_pitch, camera_altitude):
        """Calculate horizon Y position for ground rendering"""
        # Base horizon from pitch
        pitch_offset = int(camera_pitch * 5)
        
        # Altitude effect - more dramatic for better visual feedback
        altitude_factor = camera_altitude / 100.0
        altitude_offset = int(altitude_factor * 150)
        
        # Combined horizon calculation
        horizon_y = (self.SCREEN_HEIGHT // 2) + pitch_offset + altitude_offset
        
        # Ensure extreme positions for better altitude visualization
        if camera_altitude > 400:  # High altitude
            horizon_y = max(self.SCREEN_HEIGHT - 100, horizon_y)
        elif camera_altitude < 50:  # Very low altitude
            horizon_y = min(self.SCREEN_HEIGHT // 3, horizon_y)
        
        # Clamp to reasonable bounds
        return max(50, min(self.SCREEN_HEIGHT - 10, horizon_y))
    
    def apply_frame_rate_compensation(self, value, target_fps=None):
        """Apply frame rate compensation to physics values"""
        if target_fps is None:
            target_fps = self.TARGET_FPS
        return value * (target_fps / self.TARGET_FPS)
    
    def get_distance_scale_factor(self, distance, base_distance=100.0):
        """Get scaling factor based on distance for rendering"""
        if distance <= 0:
            return 0
        return max(0.1, base_distance / distance)
    
    def normalize_control_input(self, input_value, deadzone=0.05):
        """Normalize and apply deadzone to control inputs"""
        if abs(input_value) < deadzone:
            return 0.0
        
        # Apply deadzone and renormalize
        sign = 1 if input_value > 0 else -1
        normalized = (abs(input_value) - deadzone) / (1.0 - deadzone)
        return sign * max(0.0, min(1.0, normalized))

class CollisionManager:
    """Specialized collision detection using PhysicsManager"""
    
    def __init__(self, physics_manager):
        self.physics = physics_manager
    
    def check_drone_obstacle_collision(self, drone, obstacles):
        """Check drone collision with obstacles using unified physics"""
        for obstacle in obstacles:
            # 3D collision check
            if self.physics.check_3d_collision(
                drone.position, 
                obstacle.position,
                drone.size / 2,
                max(obstacle.width, obstacle.height, obstacle.depth) / 2
            ):
                return obstacle
        return None
    
    def check_drone_ground_collision(self, drone):
        """Check ground collision using unified coordinate system"""
        return self.physics.is_ground_collision(drone.position.y)
    
    def check_target_collection(self, drone, targets, camera_rotation=None):
        """Check target collection with both 3D and screen space options"""
        for target in targets:
            if target.collected:
                continue
            
            # Primary: 3D proximity check
            if self.physics.check_3d_collision(
                drone.position,
                target.position,
                drone.size / 2,
                target.radius
            ):
                target.collected = True
                return target
            
            # Secondary: Screen space crosshair alignment (if camera provided)
            if camera_rotation is not None:
                target_screen = self.physics.project_3d_to_screen(
                    target.position, drone.position, camera_rotation
                )
                if self.physics.check_crosshair_alignment(target_screen, 50):
                    # Also check reasonable 3D distance
                    distance_3d = math.sqrt(
                        (drone.position.x - target.position.x)**2 + 
                        (drone.position.y - target.position.y)**2 + 
                        (drone.position.z - target.position.z)**2
                    )
                    if distance_3d < 60:  # Close enough for collection
                        target.collected = True
                        return target
        
        return None

# Global instance for easy access
physics_manager = PhysicsManager()
collision_manager = CollisionManager(physics_manager)