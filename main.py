import sys
import pygame
import math
import random
import threading
import time
import os
from dataclasses import dataclass
from typing import List, Tuple
from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone

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

@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

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

    def update_physics(self, throttle, yaw, pitch, roll):
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
        
        # Battery consumption (scales with speed and power usage)
        base_power_usage = (abs(emg_signals[0]) + abs(emg_signals[1]) + 
                           abs(emg_signals[2]) + abs(emg_signals[3])) * 0.008
        # Additional power consumption at high speeds
        speed_power = (speed / self.max_speed_ms) * 0.012
        self.battery = max(0, self.battery - base_power_usage - speed_power)
        
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

class Obstacle:
    def __init__(self, x, y, z, width, height, depth):
        self.position = Vector3(x, y, z)
        self.width = width
        self.height = height  
        self.depth = depth
        self.color = (139, 69, 19)  # Brown
        
    def check_collision(self, drone):
        """Check if drone collides with this obstacle"""
        dx = abs(drone.position.x - self.position.x)
        dy = abs(drone.position.y - self.position.y)
        dz = abs(drone.position.z - self.position.z)
        
        return (dx < (self.width/2 + drone.size/2) and 
                dy < (self.height/2 + drone.size/2) and
                dz < (self.depth/2 + drone.size/2))

class Target:
    def __init__(self, x, y, z, radius=15):
        self.position = Vector3(x, y, z)
        self.radius = radius
        self.collected = False
        self.color = (0, 255, 0)  # Green
        
    def check_collection(self, drone):
        """Check if drone has collected this target"""
        if self.collected:
            return False
            
        distance = math.sqrt((drone.position.x - self.position.x)**2 + 
                           (drone.position.y - self.position.y)**2 + 
                           (drone.position.z - self.position.z)**2)
        
        if distance < (self.radius + drone.size/2):
            self.collected = True
            return True
        return False

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
        
        # Control mapping thresholds
        self.emg_threshold = 30.0
        self.emg_max = 100.0
        
        # First-person camera
        self.camera_position = Vector3(0, 0, 0)
        self.camera_rotation = Vector3(0, 0, 0)
        
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
                    print(f"✓ Loaded {filename}")
                else:
                    missing_files.append(filename)
                    self.images[key] = None
            except pygame.error as e:
                print(f"✗ Error loading {filename}: {e}")
                self.images[key] = None
                missing_files.append(filename)
        
        if missing_files:
            print("\n⚠️  Missing image files:")
            for file in missing_files:
                print(f"   - {file}")
            print("The simulator will create placeholder graphics for missing assets\n")
        
    def draw_configuration_screen(self):
        """Draw drone configuration screen"""
        self.screen.fill((20, 30, 60))  # Dark blue background
        
        # Title
        title = self.font_large.render("EMG FPV Drone Configuration", True, self.WHITE)
        title_rect = title.get_rect(center=(self.WIDTH//2, 80))
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Configure Drone Performance Parameters", True, self.YELLOW)
        subtitle_rect = subtitle.get_rect(center=(self.WIDTH//2, 120))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Configuration options
        config_y = 200
        
        # Maximum Speed Configuration
        speed_title = self.font_medium.render("Maximum Speed Configuration", True, self.WHITE)
        self.screen.blit(speed_title, (50, config_y))
        
        speed_options = [
            ("1 - Racing (180 km/h)", 180, "Professional FPV racing speed"),
            ("2 - Sport (120 km/h)", 120, "Recreational sport flying"),
            ("3 - Custom Speed", "custom", "Enter your own maximum speed")
        ]
        
        for i, (option, speed, desc) in enumerate(speed_options):
            y_pos = config_y + 40 + i * 50
            color = self.GREEN if speed == self.max_speed_kmh else self.WHITE
            option_text = self.font_small.render(option, True, color)
            self.screen.blit(option_text, (70, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            self.screen.blit(desc_text, (70, y_pos + 20))
        
        # Range Configuration
        range_y = config_y + 200
        range_title = self.font_medium.render("Maximum Range Configuration", True, self.WHITE)
        self.screen.blit(range_title, (50, range_y))
        
        range_options = [
            ("4 - Short Range (2 km)", 2, "Close proximity operations"),
            ("5 - Medium Range (5 km)", 5, "Standard operational range"),
            ("6 - Long Range (10 km)", 10, "Extended range operations"),
            ("7 - Custom Range", "custom", "Enter your own maximum range")
        ]
        
        for i, (option, range_val, desc) in enumerate(range_options):
            y_pos = range_y + 40 + i * 50
            color = self.GREEN if range_val == self.max_range_km else self.WHITE
            option_text = self.font_small.render(option, True, color)
            self.screen.blit(option_text, (70, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            self.screen.blit(desc_text, (70, y_pos + 20))
        
        # Current Configuration Display - moved down to avoid overlap
        current_config_y = 650
        config_display = self.font_medium.render("Current Configuration:", True, self.YELLOW)
        self.screen.blit(config_display, (50, current_config_y))
        
        speed_display = self.font_small.render(f"Max Speed: {self.max_speed_kmh} km/h", True, self.WHITE)
        self.screen.blit(speed_display, (70, current_config_y + 30))
        
        range_display = self.font_small.render(f"Max Range: {self.max_range_km} km", True, self.WHITE)
        self.screen.blit(range_display, (70, current_config_y + 50))
        
        # Start button - moved down
        start_text = self.font_medium.render("Press ENTER to Start Flight Simulation", True, self.GREEN)
        start_rect = start_text.get_rect(center=(self.WIDTH//2, 740))
        self.screen.blit(start_text, start_rect)
        
        # Control mode indicator - moved down
        control_info = self.font_small.render(
            f"Control Mode: {'EMG Hardware' if ARDUINO_MODE else 'Keyboard (WASD + Space + QE)'}", 
            True, self.GRAY
        )
        control_rect = control_info.get_rect(center=(self.WIDTH//2, 770))
        self.screen.blit(control_info, control_rect)
        
    def handle_configuration_input(self, key):
        """Handle user input for configuration"""
        if key == pygame.K_1:
            self.max_speed_kmh = 180
        elif key == pygame.K_2:
            self.max_speed_kmh = 120
        elif key == pygame.K_3:
            # Custom speed input (simplified - you could add text input here)
            print("Custom speed selected. Using 200 km/h for demonstration.")
            self.max_speed_kmh = 200
        elif key == pygame.K_4:
            self.max_range_km = 2
        elif key == pygame.K_5:
            self.max_range_km = 5
        elif key == pygame.K_6:
            self.max_range_km = 10
        elif key == pygame.K_7:
            # Custom range input (simplified - you could add text input here)
            print("Custom range selected. Using 15 km for demonstration.")
            self.max_range_km = 15
        elif key == pygame.K_RETURN:
            # Start simulation with configured parameters
            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
            self.current_scenario = self.create_high_speed_scenario()
            self.game_state = "FLYING"
            print(f"Starting FPV simulation - Max Speed: {self.max_speed_kmh} km/h, Max Range: {self.max_range_km} km")

    def create_high_speed_scenario(self):
        """Create high-speed FPV racing scenario"""
        obstacles = [
            # Racing obstacles and buildings
            Obstacle(250, 400, 0, 30, 120, 30),
            Obstacle(400, 320, 40, 35, 140, 30),
            Obstacle(550, 450, -40, 30, 130, 30),
            Obstacle(700, 350, 30, 40, 150, 30),
            Obstacle(850, 380, -20, 35, 120, 30),
        ]
        
        targets = [
            # High-speed racing checkpoints
            Target(180, 200, 0, 15),
            Target(320, 180, 25, 15),
            Target(480, 220, -15, 15),
            Target(640, 160, 35, 15),
            Target(800, 190, -10, 15),
            Target(950, 200, 0, 15),
        ]
        
        return TrainingScenario(
            "High-Speed FPV Racing Course",
            f"Navigate through checkpoints at maximum speed up to {self.max_speed_kmh} km/h",
            obstacles,
            targets,
            90  # High-speed racing scenario
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
            throttle = 1.0 if keys[pygame.K_SPACE] else 0.0
            yaw = (-0.5 if keys[pygame.K_q] else 0.0) + (0.5 if keys[pygame.K_e] else 0.0)
            pitch = (-0.5 if keys[pygame.K_w] else 0.0) + (0.5 if keys[pygame.K_s] else 0.0)
            roll = (-0.5 if keys[pygame.K_a] else 0.0) + (0.5 if keys[pygame.K_d] else 0.0)
            
            return throttle, yaw, pitch, roll
    
    def project_3d_to_2d(self, pos):
        """Convert 3D position to 2D screen coordinates"""
        # Isometric projection
        screen_x = self.WIDTH // 2 + (pos.x - pos.z) * 0.6
        screen_y = self.HEIGHT // 2 + (pos.y + (pos.x + pos.z) * 0.3) * 0.8
        return int(screen_x), int(screen_y)
    
    def draw_background(self):
        """Draw background sky"""
        if self.images['sky_background']:
            bg_scaled = pygame.transform.scale(self.images['sky_background'], (self.WIDTH, self.HEIGHT))
            self.screen.blit(bg_scaled, (0, 0))
        else:
            # Fallback gradient sky
            for y in range(self.HEIGHT//2):
                color_ratio = y / (self.HEIGHT//2)
                r = int(135 + (25 * color_ratio))
                g = int(206 + (25 * color_ratio))
                b = int(235 + (20 * color_ratio))
                pygame.draw.line(self.screen, (r, g, b), (0, y), (self.WIDTH, y))
    
    def draw_ground(self):
        """Draw ground with texture"""
        ground_y = self.project_3d_to_2d(Vector3(0, 600, 0))[1]
        
        if self.images['ground_texture']:
            # Tile ground texture
            ground_img = self.images['ground_texture']
            tile_width = ground_img.get_width()
            tile_height = ground_img.get_height()
            
            for x in range(0, self.WIDTH, tile_width):
                for y in range(ground_y, self.HEIGHT, tile_height):
                    self.screen.blit(ground_img, (x, y))
        else:
            # Fallback solid ground with grid
            pygame.draw.rect(self.screen, (34, 139, 34), (0, ground_y, self.WIDTH, self.HEIGHT - ground_y))
            
            # Grid lines
            for x in range(-500, 1000, 50):
                start_3d = Vector3(x, 600, -200)
                end_3d = Vector3(x, 600, 200)
                start_2d = self.project_3d_to_2d(start_3d)
                end_2d = self.project_3d_to_2d(end_3d)
                pygame.draw.line(self.screen, (0, 100, 0), start_2d, end_2d, 1)
    
    def draw_obstacles(self):
        """Draw obstacles with building images"""
        for obstacle in self.current_scenario.obstacles:
            pos_2d = self.project_3d_to_2d(obstacle.position)
            
            if self.images['building']:
                building_img = pygame.transform.scale(self.images['building'], 
                                                    (int(obstacle.width * 0.8), int(obstacle.height * 0.8)))
                building_rect = building_img.get_rect(center=pos_2d)
                self.screen.blit(building_img, building_rect)
            else:
                # Fallback 3D building
                width_2d = int(obstacle.width * 0.8)
                height_2d = int(obstacle.height * 0.8)
                
                pygame.draw.rect(self.screen, obstacle.color,
                               (pos_2d[0] - width_2d//2, pos_2d[1] - height_2d//2,
                                width_2d, height_2d))
                
                # 3D depth effect
                depth_offset = 8
                points = [
                    (pos_2d[0] + width_2d//2, pos_2d[1] - height_2d//2),
                    (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] - height_2d//2 - depth_offset),
                    (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] + height_2d//2 - depth_offset),
                    (pos_2d[0] + width_2d//2, pos_2d[1] + height_2d//2)
                ]
                pygame.draw.polygon(self.screen, (obstacle.color[0]//2, obstacle.color[1]//2, obstacle.color[2]//2), points)
    
    def draw_targets(self):
        """Draw targets with checkpoint images"""
        for target in self.current_scenario.targets:
            if not target.collected:
                pos_2d = self.project_3d_to_2d(target.position)
                
                if self.images['checkpoint']:
                    pulse = math.sin(time.time() * 4) * 0.2 + 1.0
                    target_size = int(target.radius * 2.5 * pulse)
                    checkpoint_img = pygame.transform.scale(self.images['checkpoint'], 
                                                          (target_size, target_size))
                    checkpoint_rect = checkpoint_img.get_rect(center=pos_2d)
                    self.screen.blit(checkpoint_img, checkpoint_rect)
                else:
                    # Fallback animated target
                    pulse = math.sin(time.time() * 4) * 0.3 + 1.0
                    outer_radius = int(target.radius * pulse)
                    
                    pygame.draw.circle(self.screen, (0, 255, 0, 100), pos_2d, outer_radius, 3)
                    pygame.draw.circle(self.screen, target.color, pos_2d, target.radius)
                    pygame.draw.circle(self.screen, self.WHITE, pos_2d, target.radius, 2)
    
    def draw_hud(self):
        """Draw advanced FPV HUD system with dynamic mission data"""
        # Calculate dynamic mission data
        targets_remaining = len([t for t in self.current_scenario.targets if not t.collected])
        elapsed_time = time.time() - self.current_scenario.start_time
        time_left = max(0, self.current_scenario.time_limit - elapsed_time)
        
        # Get current heading and add debug output
        current_heading = self.drone.rotation.y % 360
        
        # Debug: Print heading value occasionally to console
        if int(time.time()) % 5 == 0:  # Print every 5 seconds
            print(f"Debug - Drone heading: {current_heading:.1f}°, Yaw rotation: {self.drone.rotation.y:.1f}")
        
        # Create enhanced drone data with mission info
        drone_data = {
            'heading': current_heading,
            'pitch': self.drone.rotation.x,
            'roll': self.drone.rotation.z,
            'speed': self.drone.get_speed_kmh(),
            'max_speed': self.drone.max_speed_kmh,
            'altitude': max(0, 600 - self.drone.position.y),
            'battery': self.drone.battery,
            'voltage': 3.7 * (self.drone.battery / 100),
            'range': self.drone.get_range_from_start_km(),
            'max_range': self.drone.max_range_km,
            'flight_mode': 'FPV' if not self.drone.crashed else 'CRASH',
            'armed': not self.drone.crashed,
            'mission_name': self.current_scenario.name,
            'targets_remaining': targets_remaining,
            'time_left': time_left
        }
        
        # Draw the complete HUD
        self.hud_system.draw_complete_hud(self.screen, drone_data)
    
    def run(self):
        """Main game loop for FPV simulator with configuration"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG FPV Drone Training Simulator ===")
        print("Research Platform for HardwareX Journal")
        print("Hardware: BioAmp EXG Pill + Arduino Uno R4")
        print(f"Control Mode: {'EMG Hardware' if ARDUINO_MODE else 'Keyboard Testing'}")
        print("Configure drone parameters before starting simulation")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == "CONFIGURATION":
                        self.handle_configuration_input(event.key)
                        
                    elif self.game_state == "FLYING":
                        if event.key == pygame.K_r:
                            # Reset current scenario (works even if crashed)
                            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
                            self.current_scenario = self.create_high_speed_scenario()
                            self.score = 0  # Reset score
                            print(f"FPV scenario reset - Max Speed: {self.max_speed_kmh} km/h, Max Range: {self.max_range_km} km")
                            
                        elif event.key == pygame.K_ESCAPE:
                            # Return to configuration
                            self.game_state = "CONFIGURATION"
                            print("Returning to configuration screen")
                            
                        elif event.key == pygame.K_SPACE and self.drone.crashed:
                            # Quick restart when crashed - just press spacebar
                            self.drone = FPVDrone(100, 300, 0, self.max_speed_kmh, self.max_range_km)
                            self.current_scenario = self.create_high_speed_scenario()
                            self.score = 0
                            print("Quick restart - Press SPACE when crashed to restart instantly")
            
            if self.game_state == "CONFIGURATION":
                self.draw_configuration_screen()
                
            elif self.game_state == "FLYING":
                # Process controls and update physics
                throttle, yaw, pitch, roll = self.process_emg_controls()
                self.drone.update_physics(throttle, yaw, pitch, roll)
                
                # Update first-person camera
                self.camera_position = self.drone.position
                self.camera_rotation = self.drone.rotation
                
                # Check collisions with obstacles
                for obstacle in self.current_scenario.obstacles:
                    if obstacle.check_collision(self.drone):
                        self.drone.crashed = True
                
                # Check target collection
                for target in self.current_scenario.targets:
                    if target.check_collection(self.drone):
                        self.score += 10
                        print(f"Checkpoint collected at {self.drone.get_speed_kmh():.0f} km/h! Score: {self.score}")
                
                # Check scenario completion
                if self.current_scenario.check_completion(self.drone):
                    print(f"High-speed mission completed! Final score: {self.score}")
                    print(f"Maximum speed achieved: {self.drone.max_speed_achieved:.0f} km/h")
                    print(f"Total distance traveled: {self.drone.get_total_distance_km():.2f} km")
                
                # Check mission failure conditions
                elapsed_time = time.time() - self.current_scenario.start_time
                if elapsed_time > self.current_scenario.time_limit or self.drone.battery <= 0:
                    if not self.drone.crashed:
                        self.drone.crashed = True
                        print("Mission failed: Time/battery exhausted")
                        print(f"Final statistics - Max Speed: {self.drone.max_speed_achieved:.0f} km/h, Distance: {self.drone.get_total_distance_km():.2f} km")
                
                # Check range limit warning
                range_percentage = (self.drone.get_range_from_start_km() / self.drone.max_range_km) * 100
                if range_percentage > 95:
                    if not self.drone.crashed:
                        self.drone.crashed = True
                        print("Mission failed: Maximum range exceeded")
                
                # Draw first-person view
                self.screen.fill(self.BLACK)
                self.draw_background()
                self.draw_ground()
                self.draw_obstacles()
                self.draw_targets()
                self.draw_hud()
            
            pygame.display.flip()
            clock.tick(60)
        
        # Cleanup
        global breaking_case
        breaking_case = True
        if ARDUINO_MODE and ser:
            ser.close()
            print("Arduino connection closed")
        pygame.quit()

if __name__ == "__main__":
    simulator = FPVSimulator()
    simulator.run()