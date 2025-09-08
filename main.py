import sys
import pygame
import math
import random
import threading
import time
import os
from dataclasses import dataclass
from typing import List, Tuple

#import custom class
from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone
from vector3 import Vector3
from drone import FPVDrone
from obstacles import EnvironmentGenerator, ObstacleRenderer


# Hardware control toggle
ARDUINO_MODE = False

# Arduino setup (disabled for now)
ser = None
if ARDUINO_MODE:
    import serial
    arduino_port = 'COM3'
    baud_rate = 115200
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)

# EMG signal storage
emg_signals = [0.0, 0.0, 0.0, 0.0]  # throttle, yaw, pitch, roll
breaking_case = False

def arduino_data():
    """Continuously fetch EMG data from Arduino"""
    global emg_signals, breaking_case
    while not breaking_case and ARDUINO_MODE:
        try:
            ser_out = ser.readline().decode().strip().split(',')
            if len(ser_out) == 4:
                emg_signals = [float(x) for x in ser_out]
        except Exception as e:
            print(f"Arduino error: {e}")
            emg_signals = [0.0, 0.0, 0.0, 0.0]

if ARDUINO_MODE:
    arduino_thread = threading.Thread(target=arduino_data, daemon=True)
    arduino_thread.start()


class TrainingScenario:
    def __init__(self, name, description, obstacles, targets, time_limit=60):
        self.name = name
        self.description = description
        self.obstacles = obstacles
        self.targets = targets
        self.time_limit = time_limit
        self.completed = False
        self.start_time = time.time()
        
    def check_completion(self, drone):
        """Check if scenario objectives are met"""
        return len([t for t in self.targets if not t.collected]) == 0 and not drone.crashed

class FPVSimulator:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG FPV Drone Training Simulator - Configuration")

        # Initialize HUD system AFTER WIDTH/HEIGHT are defined
        self.hud_system = FPVHUDSystem(self.WIDTH, self.HEIGHT)
        
        # Initialize enhanced obstacle renderer
        self.obstacle_renderer = ObstacleRenderer(self.WIDTH, self.HEIGHT)

        # Load all required images
        self.load_images()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 100, 255)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        self.ORANGE = (255, 165, 0)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Game state
        self.game_state = "CONFIGURATION"  # "CONFIGURATION", "FLYING"
        self.drone = None
        self.current_scenario = None
        self.score = 0
        
        # User-configurable parameters
        self.max_speed_kmh = 180  # Default professional racing speed
        self.max_range_km = 5     # Default 5km range
        self.environment_type = "buildings"  # "buildings", "forest", "hybrid"
        
        # Control mapping thresholds
        self.emg_threshold = 30.0
        self.emg_max = 100.0
        
        # First-person camera
        self.camera_position = Vector3(0, 0, 0)
        self.camera_rotation = Vector3(0, 0, 0)
        
        # Debug logging
        self.debug_file = open("drone_debug.txt", "w")
        self.debug_file.write("Time,Throttle,Speed_kmh,Altitude,Drone_Y,Crashed,Pitch,Roll,Yaw\n")
        self.debug_frame_counter = 0

    def load_images(self):
        """Load all required FPV drone and environment images"""
        self.images = {}
        
        # Required image files for FPV simulator
        required_images = {
            'sky_background': 'images/sky_background.png',
            'ground_texture': 'images/ground_texture.png',
            'building': 'images/building.png',
            'checkpoint': 'images/checkpoint.png',
            'hud_overlay': 'images/hud_overlay.png'
        }
        
        print("Loading FPV drone simulator assets...")
        missing_files = []
        
        for key, filename in required_images.items():
            try:
                if os.path.exists(filename):
                    self.images[key] = pygame.image.load(filename)
                    print(f"Loaded {filename}")
                else:
                    missing_files.append(filename)
                    self.images[key] = None
            except pygame.error as e:
                print(f"Error loading {filename}: {e}")
                self.images[key] = None
                missing_files.append(filename)
        
        if missing_files:
            print("\nMissing image files:")
            for file in missing_files:
                print(f"   - {file}")
            print("The simulator will create placeholder graphics for missing assets\n")
        
    def draw_configuration_screen(self):
        """Draw enhanced drone configuration screen with environment selection"""
        self.screen.fill((20, 30, 60))  # Dark blue background
        
        # Title
        title = self.font_large.render("EMG FPV Drone Training Simulator", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH//2, 60))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Configure Drone Performance & Environment", True, self.YELLOW)
        subtitle_rect = subtitle.get_rect(center=(self.WIDTH//2, 90))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Configuration sections
        left_col_x = 50
        right_col_x = 650
        section_y = 140
        
        # === LEFT COLUMN: PERFORMANCE ===
        # Speed Configuration
        speed_title = self.font_medium.render("Speed Configuration", True, self.WHITE)
        self.screen.blit(speed_title, (left_col_x, section_y))
        
        speed_options = [
            ("1 - Racing (180 km/h)", 180, "Professional FPV racing"),
            ("2 - Sport (120 km/h)", 120, "Recreational flying"),
            ("3 - Custom (200 km/h)", 200, "High-performance setup")
        ]
        
        for i, (option, speed, desc) in enumerate(speed_options):
            y_pos = section_y + 35 + i * 40
            color = self.GREEN if speed == self.max_speed_kmh else self.WHITE
            option_text = self.font_small.render(option, True, color)
            self.screen.blit(option_text, (left_col_x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            self.screen.blit(desc_text, (left_col_x + 20, y_pos + 18))
        
        # Range Configuration
        range_y = section_y + 170
        range_title = self.font_medium.render("Range Configuration", True, self.WHITE)
        self.screen.blit(range_title, (left_col_x, range_y))
        
        range_options = [
            ("4 - Short (2 km)", 2, "Close operations"),
            ("5 - Medium (5 km)", 5, "Standard range"),
            ("6 - Long (10 km)", 10, "Extended range")
        ]
        
        for i, (option, range_val, desc) in enumerate(range_options):
            y_pos = range_y + 35 + i * 40
            color = self.GREEN if range_val == self.max_range_km else self.WHITE
            option_text = self.font_small.render(option, True, color)
            self.screen.blit(option_text, (left_col_x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            self.screen.blit(desc_text, (left_col_x + 20, y_pos + 18))
        
        # === RIGHT COLUMN: ENVIRONMENT ===
        env_title = self.font_medium.render("Environment Selection", True, self.WHITE)
        self.screen.blit(env_title, (right_col_x, section_y))
        
        env_options = [
            ("7 - Urban Buildings", "buildings", "Skyscrapers and city structures", "Navigate between tall buildings"),
            ("8 - Natural Forest", "forest", "Trees and organic obstacles", "Slalom through forest terrain"),
            ("9 - Hybrid Course", "hybrid", "Mixed urban and nature", "Varied environment challenges")
        ]
        
        for i, (option, env_type, desc, detail) in enumerate(env_options):
            y_pos = section_y + 35 + i * 65
            color = self.GREEN if env_type == self.environment_type else self.WHITE
            option_text = self.font_small.render(option, True, color)
            self.screen.blit(option_text, (right_col_x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            self.screen.blit(desc_text, (right_col_x + 20, y_pos + 18))
            
            detail_text = self.font_small.render(detail, True, (150, 150, 150))
            self.screen.blit(detail_text, (right_col_x + 20, y_pos + 36))
        
        # Environment Preview (small visualization)
        preview_y = section_y + 250
        preview_title = self.font_small.render("Environment Preview:", True, self.YELLOW)
        self.screen.blit(preview_title, (right_col_x, preview_y))
        
        # Draw mini preview based on selected environment
        preview_rect = pygame.Rect(right_col_x + 20, preview_y + 25, 200, 100)
        pygame.draw.rect(self.screen, (40, 40, 60), preview_rect)
        pygame.draw.rect(self.screen, self.WHITE, preview_rect, 2)
        
        self.draw_environment_preview(preview_rect)
        
        # === BOTTOM: CURRENT CONFIG & START ===
        config_y = 580
        config_display = self.font_medium.render("Current Configuration:", True, self.YELLOW)
        self.screen.blit(config_display, (left_col_x, config_y))
        
        config_items = [
            f"Max Speed: {self.max_speed_kmh} km/h",
            f"Max Range: {self.max_range_km} km",
            f"Environment: {self.environment_type.title()}"
        ]
        
        for i, item in enumerate(config_items):
            item_text = self.font_small.render(item, True, self.WHITE)
            self.screen.blit(item_text, (left_col_x + 20, config_y + 30 + i * 20))
        
        # Start button
        start_text = self.font_medium.render("Press ENTER to Start Flight Simulation", True, self.GREEN)
        start_rect = start_text.get_rect(center=(self.WIDTH//2, 700))
        self.screen.blit(start_text, start_rect)
        
        # Control mode indicator
        control_info = self.font_small.render(
            f"Control: {'EMG Hardware' if ARDUINO_MODE else 'Keyboard (WASD + Space + QE)'}", 
            True, self.GRAY
        )
        control_rect = control_info.get_rect(center=(self.WIDTH//2, 730))
        self.screen.blit(control_info, control_rect)
        
        # Help text
        help_text = self.font_small.render("R = Reset | ESC = Config | Space = Quick Restart", True, self.GRAY)
        help_rect = help_text.get_rect(center=(self.WIDTH//2, 750))
        self.screen.blit(help_text, help_rect)
    
    def draw_environment_preview(self, preview_rect):
        """Draw a small preview of the selected environment"""
        center_x = preview_rect.centerx
        center_y = preview_rect.centery
        
        if self.environment_type == "buildings":
            # Draw mini buildings
            for i, (x_offset, height) in enumerate([(-60, 40), (-20, 60), (20, 35), (60, 50)]):
                building_x = center_x + x_offset
                building_bottom = center_y + 30
                pygame.draw.rect(self.screen, (139, 69, 19), 
                               (building_x - 8, building_bottom - height, 16, height))
                # 3D effect
                pygame.draw.polygon(self.screen, (80, 40, 10), [
                    (building_x + 8, building_bottom - height),
                    (building_x + 12, building_bottom - height - 4),
                    (building_x + 12, building_bottom - 4),
                    (building_x + 8, building_bottom)
                ])
                
        elif self.environment_type == "forest":
            # Draw mini trees
            for i, x_offset in enumerate([-50, -15, 15, 50]):
                tree_x = center_x + x_offset
                tree_bottom = center_y + 25
                
                # Tree trunk
                pygame.draw.rect(self.screen, (101, 67, 33),
                               (tree_x - 2, tree_bottom - 10, 4, 10))
                
                # Tree crown
                pygame.draw.circle(self.screen, (34, 139, 34),
                                 (tree_x, tree_bottom - 15), 8)
                
        else:  # hybrid
            # Draw mixed elements
            # Building
            pygame.draw.rect(self.screen, (139, 69, 19),
                           (center_x - 60, center_y + 5, 12, 25))
            
            # Tree
            pygame.draw.rect(self.screen, (101, 67, 33),
                           (center_x - 15, center_y + 20, 3, 8))
            pygame.draw.circle(self.screen, (34, 139, 34),
                             (center_x - 14, center_y + 15), 6)
            
            # Another building
            pygame.draw.rect(self.screen, (105, 105, 105),
                           (center_x + 20, center_y - 5, 14, 35))
            
            # Another tree
            pygame.draw.rect(self.screen, (101, 67, 33),
                           (center_x + 50, center_y + 18, 3, 10))
            pygame.draw.circle(self.screen, (0, 100, 0),
                             (center_x + 51, center_y + 12), 7)

    def handle_configuration_input(self, key):
        """Handle user input for enhanced configuration"""
        if key == pygame.K_1:
            self.max_speed_kmh = 180
        elif key == pygame.K_2:
            self.max_speed_kmh = 120
        elif key == pygame.K_3:
            self.max_speed_kmh = 200
        elif key == pygame.K_4:
            self.max_range_km = 2
        elif key == pygame.K_5:
            self.max_range_km = 5
        elif key == pygame.K_6:
            self.max_range_km = 10
        elif key == pygame.K_7:
            self.environment_type = "buildings"
        elif key == pygame.K_8:
            self.environment_type = "forest"
        elif key == pygame.K_9:
            self.environment_type = "hybrid"
        elif key == pygame.K_RETURN:
            # Start simulation with configured parameters
            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
            self.current_scenario = self.create_scenario_by_environment()
            self.game_state = "FLYING"
            print(f"Starting FPV simulation:")
            print(f"  Environment: {self.environment_type.title()}")
            print(f"  Max Speed: {self.max_speed_kmh} km/h")
            print(f"  Max Range: {self.max_range_km} km")

    def create_scenario_by_environment(self):
        """Create scenario based on selected environment type"""
        if self.environment_type == "buildings":
            obstacles, targets, name = EnvironmentGenerator.create_building_course()
        elif self.environment_type == "forest":
            obstacles, targets, name = EnvironmentGenerator.create_forest_course()
        else:  # hybrid
            obstacles, targets, name = EnvironmentGenerator.create_hybrid_course()
        
        return TrainingScenario(
            name,
            f"Navigate through {self.environment_type} environment at speeds up to {self.max_speed_kmh} km/h",
            obstacles,
            targets,
            90  # Time limit
        )

    def process_emg_controls(self):
        """Process EMG signals into drone controls"""
        if ARDUINO_MODE:
            # Map EMG signals to control values (-1 to 1)
            throttle = max(0, (emg_signals[0] - self.emg_threshold) / (self.emg_max - self.emg_threshold))
            yaw = (emg_signals[1] - self.emg_threshold) / (self.emg_max - self.emg_threshold)
            pitch = (emg_signals[2] - self.emg_threshold) / (self.emg_max - self.emg_threshold)
            roll = (emg_signals[3] - self.emg_threshold) / (self.emg_max - self.emg_threshold)
            
            # Clamp values
            throttle = max(0, min(1, throttle))
            yaw = max(-1, min(1, yaw))
            pitch = max(-1, min(1, pitch))
            roll = max(-1, min(1, roll))
            
            return throttle, yaw, pitch, roll
        else:
            # Keyboard controls for testing
            keys = pygame.key.get_pressed()
            # Only allow throttle if drone is not crashed
            throttle = 1.0 if (keys[pygame.K_SPACE] and not self.drone.crashed) else 0.0
            yaw = (-0.5 if keys[pygame.K_q] else 0.0) + (0.5 if keys[pygame.K_e] else 0.0)
            
            # FIXED: Inverted pitch control for intuitive flight
            pitch = (0.5 if keys[pygame.K_w] else 0.0) + (-0.5 if keys[pygame.K_s] else 0.0)  # W=nose up, S=nose down
            
            roll = (-0.5 if keys[pygame.K_a] else 0.0) + (0.5 if keys[pygame.K_d] else 0.0)
            
            return throttle, yaw, pitch, roll

    def draw_hud(self):
        """Draw HUD using the proper integration function with mission data"""
        # Calculate dynamic mission data
        targets_remaining = len([t for t in self.current_scenario.targets if not t.collected])
        elapsed_time = time.time() - self.current_scenario.start_time
        time_left = max(0, self.current_scenario.time_limit - elapsed_time)
        
        # Prepare mission data for HUD integration
        mission_data = {
            'mission_name': self.current_scenario.name,
            'targets_remaining': targets_remaining,
            'time_left': time_left
        }
        
        # Use the proper integration function with mission data
        integrate_hud_with_drone(self.drone, self.hud_system, self.screen, mission_data)

    def calculate_camera_transform(self):
        """Calculate camera transformation based on drone's position and rotation"""
        # Camera position is at drone position
        camera_pos = self.drone.position
        
        # Calculate forward direction based on drone's yaw (heading)
        yaw_rad = math.radians(self.drone.rotation.y)
        pitch_rad = math.radians(self.drone.rotation.x)
        
        # Forward vector (where drone is looking)
        forward = Vector3(
            math.sin(yaw_rad) * math.cos(pitch_rad),
            -math.sin(pitch_rad),  # Negative because up is negative Y
            math.cos(yaw_rad) * math.cos(pitch_rad)
        )
        
        # Up vector affected by roll
        roll_rad = math.radians(self.drone.rotation.z)
        up = Vector3(
            math.sin(roll_rad),
            math.cos(roll_rad),
            0
        )
        
        # Right vector (cross product of forward and up)
        right = Vector3(
            forward.z * up.y - forward.y * up.z,
            forward.x * up.z - forward.z * up.x,
            forward.y * up.x - forward.x * up.y
        )
        
        return camera_pos, forward, up, right

    def project_3d_to_fpv(self, world_pos):
        """Project 3D world position to first-person view screen coordinates"""
        camera_pos, forward, up, right = self.calculate_camera_transform()
        
        # Translate world position relative to camera
        relative_pos = Vector3(
            world_pos.x - camera_pos.x,
            world_pos.y - camera_pos.y,
            world_pos.z - camera_pos.z
        )
        
        # Project onto camera's local coordinate system
        x_cam = relative_pos.x * right.x + relative_pos.y * right.y + relative_pos.z * right.z
        y_cam = relative_pos.x * up.x + relative_pos.y * up.y + relative_pos.z * up.z
        z_cam = relative_pos.x * forward.x + relative_pos.y * forward.y + relative_pos.z * forward.z
        
        # Perspective projection (avoid division by zero)
        if z_cam <= 0.1:
            return None  # Object is behind camera or too close
        
        # Field of view settings - make consistent with HUD expectations
        fov = 90  # degrees
        fov_rad = math.radians(fov)
        focal_length = self.WIDTH / (2 * math.tan(fov_rad / 2))
        
        # Project to screen coordinates
        screen_x = self.WIDTH // 2 + (x_cam * focal_length / z_cam)
        screen_y = self.HEIGHT // 2 - (y_cam * focal_length / z_cam)
        
        return int(screen_x), int(screen_y), z_cam

    def check_fpv_collision(self):
        """Check collision in first-person view using crosshair"""
        # DISABLED FOR TESTING - uncomment when needed
        """
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        
        for obstacle in self.current_scenario.obstacles:
            projection = self.project_3d_to_fpv(obstacle.position)
            if projection is None:
                continue
                
            screen_x, screen_y, depth = projection
            
            # Only check collision if obstacle is reasonably close
            if depth > 100:  # Ignore distant obstacles
                continue
            
            # Check if obstacle is close to crosshair
            distance_to_crosshair = math.sqrt((screen_x - center_x)**2 + (screen_y - center_y)**2)
            
            # Much smaller collision radius - only crash if very close to crosshair center
            collision_radius = 20  # Fixed small radius instead of scaling
            
            # Also check 3D distance to drone
            actual_3d_distance = math.sqrt(
                (self.drone.position.x - obstacle.position.x)**2 + 
                (self.drone.position.y - obstacle.position.y)**2 + 
                (self.drone.position.z - obstacle.position.z)**2
            )
            
            # Collision only if BOTH conditions are met:
            # 1. Obstacle appears very close to crosshair center
            # 2. Drone is actually close to obstacle in 3D space
            if distance_to_crosshair < collision_radius and actual_3d_distance < 40:
                return True
        """        
        return False

    def check_fpv_target_collection(self):
        """Check target collection in first-person view"""
        center_x, center_y = self.WIDTH // 2, self.HEIGHT // 2
        
        for target in self.current_scenario.targets:
            if target.collected:
                continue
                
            projection = self.project_3d_to_fpv(target.position)
            if projection is None:
                continue
                
            screen_x, screen_y, depth = projection
            
            # Check if target is close to crosshair
            distance_to_crosshair = math.sqrt((screen_x - center_x)**2 + (screen_y - center_y)**2)
            
            # Scale collection radius based on distance
            scale_factor = max(0.2, 100.0 / depth) if depth > 0 else 0
            collection_radius = target.radius * scale_factor
            
            # Collection if target is centered in crosshair AND close enough
            if distance_to_crosshair < collection_radius and depth < 30:
                target.collected = True
                return target
                
        return None

    def draw_fpv_ground(self):
        """Draw ground plane in first-person view with proper altitude consideration"""
        # Calculate actual altitude (distance from ground)
        actual_altitude = max(0, 600 - self.drone.position.y)
        
        # Base horizon position from pitch
        pitch_offset = int(self.drone.rotation.x * 5)
        
        # FIXED: Much stronger altitude effect
        # At 800m altitude, ground should be barely visible
        # At ground level (altitude=0), ground fills most of screen
        altitude_factor = actual_altitude / 100.0  # More sensitive to altitude changes
        altitude_offset = int(altitude_factor * 150)  # Stronger offset effect
        
        # Combined horizon calculation
        horizon_y = (self.HEIGHT // 2) + pitch_offset + altitude_offset
        
        # CRITICAL: Ensure horizon moves dramatically with altitude
        # At 800m, horizon should be near bottom of screen
        # At 0m, horizon should be in middle/upper area
        if actual_altitude > 400:  # High altitude
            horizon_y = max(self.HEIGHT - 100, horizon_y)  # Force ground to bottom
        elif actual_altitude < 50:  # Very low altitude
            horizon_y = min(self.HEIGHT // 3, horizon_y)  # Force ground higher up
        
        # Ensure horizon stays within bounds but allow more extreme positions
        horizon_y = max(50, min(self.HEIGHT - 10, horizon_y))
        
        # Sky (above horizon) - gradient gets more visible at higher altitudes
        if horizon_y > 0:
            for y in range(min(horizon_y, self.HEIGHT)):
                # Sky gradient - deeper blue at higher altitudes
                altitude_intensity = min(actual_altitude / 300.0, 1.0)
                color_ratio = y / max(1, horizon_y)
                
                # Base sky color gets deeper with altitude
                base_r = int(135 - (altitude_intensity * 50))
                base_g = int(206 - (altitude_intensity * 30))
                base_b = int(235 - (altitude_intensity * 20))
                
                r = int(base_r + (25 * color_ratio))
                g = int(base_g + (25 * color_ratio))
                b = int(base_b + (20 * color_ratio))
                
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                
                pygame.draw.line(self.screen, (r, g, b), (0, y), (self.WIDTH, y))
        
        # Ground (below horizon) - only draw if visible
        if horizon_y < self.HEIGHT:
            ground_rect = pygame.Rect(0, max(0, horizon_y), self.WIDTH, self.HEIGHT - max(0, horizon_y))
            
            # Ground color varies with distance/altitude
            if actual_altitude < 50:  # Very low altitude - bright green
                ground_color = (34, 139, 34)
            elif actual_altitude < 150:  # Medium altitude - darker green
                ground_color = (20, 100, 20)
            else:  # High altitude - very dark, distant ground
                ground_color = (10, 60, 10)
                
            pygame.draw.rect(self.screen, ground_color, ground_rect)
            
            # Add subtle texture for ground at low altitudes
            if actual_altitude < 100 and horizon_y < self.HEIGHT - 20:
                for i in range(0, self.WIDTH, 40):
                    texture_y = horizon_y + 20 + (i % 3) * 5
                    if texture_y < self.HEIGHT:
                        pygame.draw.line(self.screen, (25, 90, 25), 
                                    (i, texture_y), (i + 20, texture_y), 1)

    def draw_fpv_obstacles(self):
        """Draw obstacles in first-person view"""
        # DISABLED FOR TESTING - uncomment when needed  
        """
        for obstacle in self.current_scenario.obstacles:
            projection = self.project_3d_to_fpv(obstacle.position)
            if projection is None:
                continue
                
            screen_x, screen_y, depth = projection
            
            # Skip if off-screen
            if screen_x < -100 or screen_x > self.WIDTH + 100 or screen_y < -100 or screen_y > self.HEIGHT + 100:
                continue
                
            # Scale based on distance
            if depth <= 0:
                continue
                
            scale_factor = max(0.1, 200.0 / depth)
            width = max(1, int(obstacle.width * scale_factor))
            height = max(1, int(obstacle.height * scale_factor))
            
            # Skip tiny distant objects
            if width < 2 or height < 2:
                continue
                
            # Draw obstacle
            obstacle_rect = pygame.Rect(screen_x - width//2, screen_y - height//2, width, height)
            if obstacle_rect.colliderect(pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)):
                pygame.draw.rect(self.screen, obstacle.color, obstacle_rect)
        """
        pass

    def draw_fpv_targets(self):
        """Draw targets in first-person view"""
        for target in self.current_scenario.targets:
            if target.collected:
                continue
                
            projection = self.project_3d_to_fpv(target.position)
            if projection is None:
                continue
                
            screen_x, screen_y, depth = projection
            
            # Skip if off-screen
            if screen_x < -50 or screen_x > self.WIDTH + 50 or screen_y < -50 or screen_y > self.HEIGHT + 50:
                continue
                
            # Scale based on distance
            if depth <= 0:
                continue
                
            scale_factor = max(0.2, 100.0 / depth)
            radius = max(3, int(target.radius * scale_factor))
            
            # Draw target
            pygame.draw.circle(self.screen, target.color, (screen_x, screen_y), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), radius, 2)
    
    def check_ground_collision(self):
        """Check ground collision using consistent coordinate system"""
        # Ground is at Y=600, crash slightly above at Y=590
        if self.drone.position.y >= 590:
            return True
        return False

    def log_debug_data(self, throttle):
        """Log debug data to file for analysis - every 10th frame only"""
        self.debug_frame_counter += 1
        
        # Only log every 10th frame to reduce file size
        if self.debug_frame_counter % 10 == 0:
            current_time = time.time() - self.current_scenario.start_time
            actual_altitude = max(0, 600 - self.drone.position.y)
            
            debug_line = f"{current_time:.2f},{throttle:.2f},{self.drone.get_speed_kmh():.1f},{actual_altitude:.1f},{self.drone.position.y:.1f},{self.drone.crashed},{self.drone.rotation.x:.1f},{self.drone.rotation.z:.1f},{self.drone.rotation.y:.1f}\n"
            self.debug_file.write(debug_line)
            self.debug_file.flush()

    def run(self):
        """Main game loop for FPV simulator with configuration"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG FPV Drone Training Simulator ===")
        print("Research Platform for HardwareX Journal")
        print("Hardware: BioAmp EXG Pill + Arduino Uno R4")
        print(f"Control Mode: {'EMG Hardware' if ARDUINO_MODE else 'Keyboard Testing'}")
        print("Configure drone parameters before starting simulation")
        print("Debug data will be logged to drone_debug.txt")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == "CONFIGURATION":
                        self.handle_configuration_input(event.key)
                        
                    elif self.game_state == "FLYING":
                        if event.key == pygame.K_r:
                            # Reset current scenario
                            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
                            self.current_scenario = self.create_scenario_by_environment()
                            self.score = 0
                            print(f"FPV scenario reset - Environment: {self.environment_type.title()}")
                            
                        elif event.key == pygame.K_ESCAPE:
                            # Return to configuration
                            self.game_state = "CONFIGURATION"
                            print("Returning to configuration screen")
                            
                        elif event.key == pygame.K_SPACE and self.drone.crashed:
                            # FIXED: Only restart when crashed
                            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
                            self.current_scenario = self.create_scenario_by_environment()
                            self.score = 0
                            print("Quick restart - drone respawned")
            
            if self.game_state == "CONFIGURATION":
                self.draw_configuration_screen()
                
            elif self.game_state == "FLYING":
                # Process controls and update physics
                throttle, yaw, pitch, roll = self.process_emg_controls()
                self.drone.update_physics(throttle, yaw, pitch, roll, emg_signals)
                
                # Log debug data every frame
                self.log_debug_data(throttle)
                
                # Update first-person camera
                self.camera_position = self.drone.position
                self.camera_rotation = self.drone.rotation
                
                # Check collisions using TRUE FPV collision detection
                if self.check_fpv_collision():
                    self.drone.crashed = True
                    print("CRASH: Flew into obstacle!")
                
                # Check ground collision using consistent coordinate system
                if self.check_ground_collision():
                    self.drone.crashed = True
                    print("CRASH: Hit the ground!")
                
                # Check target collection using TRUE FPV detection
                collected_target = self.check_fpv_target_collection()
                if collected_target:
                    self.score += 10
                    print(f"Checkpoint collected at {self.drone.get_speed_kmh():.0f} km/h! Score: {self.score}")
                
                # Check scenario completion
                if self.current_scenario.check_completion(self.drone):
                    print(f"Mission completed! Final score: {self.score}")
                    print(f"Environment: {self.environment_type.title()}")
                    if hasattr(self.drone, 'max_speed_achieved'):
                        print(f"Maximum speed achieved: {self.drone.max_speed_achieved:.0f} km/h")
                    if hasattr(self.drone, 'get_total_distance_km'):
                        print(f"Total distance traveled: {self.drone.get_total_distance_km():.2f} km")
                
                # Check mission failure conditions
                elapsed_time = time.time() - self.current_scenario.start_time
                if elapsed_time > self.current_scenario.time_limit or self.drone.battery <= 0:
                    if not self.drone.crashed:
                        self.drone.crashed = True
                        print("Mission failed: Time/battery exhausted")
                
                # Check range limit
                if hasattr(self.drone, 'get_range_from_start_km'):
                    range_percentage = (self.drone.get_range_from_start_km() / self.drone.max_range_km) * 100
                    if range_percentage > 95:
                        if not self.drone.crashed:
                            self.drone.crashed = True
                            print("Mission failed: Maximum range exceeded")
                
                # Draw TRUE FIRST-PERSON VIEW
                self.screen.fill(self.BLACK)
                self.draw_fpv_ground()        # Ground with horizon based on drone pitch
                self.draw_fpv_obstacles()     # Obstacles with true perspective
                self.draw_fpv_targets()       # Targets with proper distance scaling
                self.draw_hud()               # HUD overlay
            
            pygame.display.flip()
            clock.tick(60)
        
        # Cleanup
        global breaking_case
        breaking_case = True
        if ARDUINO_MODE and ser:
            ser.close()
            print("Arduino connection closed")
        
        # Close debug file
        if hasattr(self, 'debug_file'):
            self.debug_file.close()
            print("Debug data saved to drone_debug.txt")
        
        pygame.quit()

if __name__ == "__main__":
    simulator = FPVSimulator()
    simulator.run()