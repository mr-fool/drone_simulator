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
            throttle = 1.0 if keys[pygame.K_SPACE] else 0.0
            yaw = (-0.5 if keys[pygame.K_q] else 0.0) + (0.5 if keys[pygame.K_e] else 0.0)
            pitch = (-0.5 if keys[pygame.K_w] else 0.0) + (0.5 if keys[pygame.K_s] else 0.0)
            roll = (-0.5 if keys[pygame.K_a] else 0.0) + (0.5 if keys[pygame.K_d] else 0.0)
            
            return throttle, yaw, pitch, roll

    def draw_obstacles(self):
        """Draw obstacles using enhanced renderer"""
        for obstacle in self.current_scenario.obstacles:
            pos_2d = self.obstacle_renderer.project_3d_to_2d(obstacle.position)
            
            if obstacle.obstacle_type in ["building", "skyscraper", "tower", "warehouse"]:
                self.obstacle_renderer.draw_building(self.screen, obstacle, pos_2d)
            elif obstacle.obstacle_type in ["tree", "pine"]:
                self.obstacle_renderer.draw_tree(self.screen, obstacle, pos_2d)
            else:
                # Fallback for any custom obstacle types
                width_2d = int(obstacle.width * 0.7)
                height_2d = int(obstacle.height * 0.7)
                pygame.draw.rect(self.screen, obstacle.color,
                               (pos_2d[0] - width_2d//2, pos_2d[1] - height_2d//2,
                                width_2d, height_2d))

    def draw_targets(self):
        """Draw targets using enhanced renderer"""
        for target in self.current_scenario.targets:
            if not target.collected:
                pos_2d = self.obstacle_renderer.project_3d_to_2d(target.position)
                self.obstacle_renderer.draw_target(self.screen, target, pos_2d)

    def project_3d_to_2d(self, pos):
        """Convert 3D position to 2D screen coordinates (delegates to renderer)"""
        return self.obstacle_renderer.project_3d_to_2d(pos)

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
                            # Quick restart when crashed
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