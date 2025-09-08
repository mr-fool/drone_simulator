import sys
import pygame
import math
import random
import threading
import time
import os
from dataclasses import dataclass
from typing import List, Tuple

# Import custom classes
from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone
from vector3 import Vector3
from drone import FPVDrone
from obstacles import EnvironmentGenerator, ObstacleRenderer
from physics_manager import physics_manager, collision_manager
from config import DebugConfig, PhysicsConfig
from configuration_ui import ConfigurationUI


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
        
        # Print debug status
        DebugConfig.print_active_flags()

        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG FPV Drone Training Simulator - Configuration")

        # Initialize configuration UI
        self.config_ui = ConfigurationUI(self.WIDTH, self.HEIGHT)

        # Initialize physics manager
        self.physics = physics_manager
        self.collision = collision_manager

        # Initialize HUD system AFTER WIDTH/HEIGHT are defined
        self.hud_system = FPVHUDSystem(self.WIDTH, self.HEIGHT)
        
        # Initialize enhanced obstacle renderer
        self.obstacle_renderer = ObstacleRenderer(self.WIDTH, self.HEIGHT)

        # Load all required images
        self.load_images()
        
        # Colors (simplified - main colors only since ConfigurationUI has its own)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        
        # Fonts (simplified - ConfigurationUI handles most UI fonts)
        self.font_small = pygame.font.Font(None, 24)
        
        # Game state
        self.game_state = "CONFIGURATION"  # "CONFIGURATION", "FLYING"
        self.drone = None
        self.current_scenario = None
        self.score = 0
        
        # User-configurable parameters (centralized in config dict)
        self.config = {
            'max_speed_kmh': 180,     # Default professional racing speed
            'max_range_km': 5,        # Default 5km range
            'environment_type': "buildings"  # "buildings", "forest", "hybrid"
        }
        
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
        
    

    def handle_configuration_input(self, key):
        """Handle configuration input using the ConfigurationUI"""
        updated_config, action = self.config_ui.handle_input(key, self.config)
        self.config = updated_config
        
        if action == "START_SIMULATION":
            # Start simulation with configured parameters
            spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE if DebugConfig.is_testing_mode() else 300
            self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
            self.current_scenario = self.create_scenario_by_environment()
            self.game_state = "FLYING"
            
            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                print(f"Starting FPV simulation:")
                print(f"  Environment: {self.config['environment_type'].title()}")
                print(f"  Max Speed: {self.config['max_speed_kmh']} km/h")
                print(f"  Max Range: {self.config['max_range_km']} km")
                print(f"  Spawn Altitude: {spawn_y}")

    def create_scenario_by_environment(self):
        """Create scenario based on selected environment type"""
        if self.config['environment_type'] == "buildings":
            obstacles, targets, name = EnvironmentGenerator.create_building_course()
        elif self.config['environment_type'] == "forest":
            obstacles, targets, name = EnvironmentGenerator.create_forest_course()
        else:  # hybrid
            obstacles, targets, name = EnvironmentGenerator.create_hybrid_course()
        
        return TrainingScenario(
            name,
            f"Navigate through {self.config['environment_type']} environment at speeds up to {self.config['max_speed_kmh']} km/h",
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

    def project_3d_to_fpv(self, world_pos):
        """Use unified projection from physics manager"""
        return self.physics.project_3d_to_screen(
            world_pos, 
            self.drone.position, 
            self.drone.rotation
        )

    def check_fpv_collision(self):
        """Use unified collision detection with debug override"""
        if DebugConfig.DISABLE_OBSTACLE_COLLISION:
            return False
        return self.collision.check_drone_obstacle_collision(
            self.drone, 
            self.current_scenario.obstacles
        ) is not None

    def check_fpv_target_collection(self):
        """Use unified target collection"""
        return self.collision.check_target_collection(
            self.drone, 
            self.current_scenario.targets, 
            self.drone.rotation
        )
    
    def check_ground_collision(self):
        """Use unified ground collision detection with debug override"""
        if DebugConfig.DISABLE_GROUND_COLLISION:
            return False
        return self.collision.check_drone_ground_collision(self.drone)

    def draw_debug_info(self):
        """Draw debug information on screen"""
        if not DebugConfig.is_testing_mode():
            return
            
        debug_y = 10
        line_height = 25
        
        if DebugConfig.SHOW_SPEED_DEBUG:
            speed_text = self.font_small.render(f"Speed: {self.drone.get_speed_kmh():.1f} km/h", True, self.GREEN)
            self.screen.blit(speed_text, (10, debug_y))
            debug_y += line_height
            
            max_speed_text = self.font_small.render(f"Max: {self.drone.max_speed_achieved:.1f} km/h", True, self.YELLOW)
            self.screen.blit(max_speed_text, (10, debug_y))
            debug_y += line_height
        
        if DebugConfig.SHOW_POSITION_DEBUG:
            pos_text = self.font_small.render(f"Position: ({self.drone.position.x:.0f}, {self.drone.position.y:.0f}, {self.drone.position.z:.0f})", True, self.WHITE)
            self.screen.blit(pos_text, (10, debug_y))
            debug_y += line_height
            
            alt_text = self.font_small.render(f"Altitude: {self.physics.get_altitude_from_world_y(self.drone.position.y):.1f}m", True, self.WHITE)
            self.screen.blit(alt_text, (10, debug_y))  # Changed pos_text to alt_text
            debug_y += line_height

    def draw_fpv_ground(self):
        """Use unified horizon calculation"""
        # Get actual altitude using physics manager
        actual_altitude = self.physics.get_altitude_from_world_y(self.drone.position.y)
        
        # Calculate horizon using unified system
        horizon_y = self.physics.calculate_horizon_position(
            self.drone.rotation.x, 
            actual_altitude
        )
        
        # Sky (above horizon)
        if horizon_y > 0:
            for y in range(min(horizon_y, self.HEIGHT)):
                altitude_intensity = min(actual_altitude / 300.0, 1.0)
                color_ratio = y / max(1, horizon_y)
                
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
        
        # Ground (below horizon)
        if horizon_y < self.HEIGHT:
            ground_rect = pygame.Rect(0, max(0, horizon_y), self.WIDTH, self.HEIGHT - max(0, horizon_y))
            
            if actual_altitude < 50:
                ground_color = (34, 139, 34)
            elif actual_altitude < 150:
                ground_color = (20, 100, 20)
            else:
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
        """Draw obstacles using unified projection"""
        for obstacle in self.current_scenario.obstacles:
            projection = self.project_3d_to_fpv(obstacle.position)
            if projection is None:
                continue
                
            screen_x, screen_y, depth = projection
            
            # Skip if off-screen
            if screen_x < -100 or screen_x > self.WIDTH + 100 or screen_y < -100 or screen_y > self.HEIGHT + 100:
                continue
                
            # Use physics manager for consistent scaling
            scale_factor = self.physics.get_distance_scale_factor(depth, 200.0)
            width = max(1, int(obstacle.width * scale_factor))
            height = max(1, int(obstacle.height * scale_factor))
            
            if width < 2 or height < 2:
                continue
                
            obstacle_rect = pygame.Rect(screen_x - width//2, screen_y - height//2, width, height)
            if obstacle_rect.colliderect(pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)):
                pygame.draw.rect(self.screen, obstacle.color, obstacle_rect)

    def draw_fpv_targets(self):
        """Draw targets using unified projection"""
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
                
            # Use physics manager for consistent scaling
            scale_factor = self.physics.get_distance_scale_factor(depth, 100.0)
            radius = max(3, int(target.radius * scale_factor))
            
            pygame.draw.circle(self.screen, target.color, (screen_x, screen_y), radius)
            pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), radius, 2)

    def log_debug_data(self, throttle):
        """Log debug data to file for analysis - every 10th frame only"""
        self.debug_frame_counter += 1
        
        # Only log every 10th frame to reduce file size
        if self.debug_frame_counter % 10 == 0:
            current_time = time.time() - self.current_scenario.start_time
            actual_altitude = self.physics.get_altitude_from_world_y(self.drone.position.y)
            
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
        
        # Print debug configuration status
        DebugConfig.print_active_flags()
        
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
                            spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE if DebugConfig.is_testing_mode() else 300
                            self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
                            self.current_scenario = self.create_scenario_by_environment()
                            self.score = 0
                            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                                print(f"FPV scenario reset - Environment: {self.config['environment_type'].title()}")
                            
                        elif event.key == pygame.K_ESCAPE:
                            # Return to configuration
                            self.game_state = "CONFIGURATION"
                            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                                print("Returning to configuration screen")
                            
                        elif event.key == pygame.K_SPACE and self.drone.crashed:
                            # Quick restart when crashed
                            spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE if DebugConfig.is_testing_mode() else 300
                            self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
                            self.current_scenario = self.create_scenario_by_environment()
                            self.score = 0
                            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                                print("Quick restart - drone respawned")
            
            if self.game_state == "CONFIGURATION":
                # Use the extracted configuration UI
                self.config_ui.draw_screen(self.screen, self.config)
                
            elif self.game_state == "FLYING":
                # Process controls and update physics
                throttle, yaw, pitch, roll = self.process_emg_controls()
                
                # Apply debug auto-throttle if enabled
                if DebugConfig.AUTO_THROTTLE and not self.drone.crashed:
                    throttle = 1.0
                
                # Normalize inputs using physics manager
                throttle = self.physics.normalize_control_input(throttle)
                yaw = self.physics.normalize_control_input(yaw)
                pitch = self.physics.normalize_control_input(pitch)
                roll = self.physics.normalize_control_input(roll)
                
                self.drone.update_physics(throttle, yaw, pitch, roll, emg_signals)
                
                # Log debug data every frame
                self.log_debug_data(throttle)
                
                # Update first-person camera
                self.camera_position = self.drone.position
                self.camera_rotation = self.drone.rotation
                
                # Check collisions using unified collision detection (with debug overrides)
                if self.check_fpv_collision():
                    self.drone.crashed = True
                    if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                        print("CRASH: Flew into obstacle!")
                
                # Check ground collision using unified coordinate system (with debug override)
                if self.check_ground_collision():
                    self.drone.crashed = True
                    if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                        print("CRASH: Hit the ground!")
                
                # Check target collection using unified detection
                collected_target = self.check_fpv_target_collection()
                if collected_target:
                    self.score += 10
                    if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                        print(f"Checkpoint collected at {self.drone.get_speed_kmh():.0f} km/h! Score: {self.score}")
                
                # Check scenario completion
                if self.current_scenario.check_completion(self.drone):
                    if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                        print(f"Mission completed! Final score: {self.score}")
                        print(f"Environment: {self.config['environment_type'].title()}")
                        if hasattr(self.drone, 'max_speed_achieved'):
                            print(f"Maximum speed achieved: {self.drone.max_speed_achieved:.0f} km/h")
                        if hasattr(self.drone, 'get_total_distance_km'):
                            print(f"Total distance traveled: {self.drone.get_total_distance_km():.2f} km")
                
                # Check mission failure conditions
                elapsed_time = time.time() - self.current_scenario.start_time
                if elapsed_time > self.current_scenario.time_limit or (self.drone.battery <= 0 and not DebugConfig.DISABLE_BATTERY_DRAIN):
                    if not self.drone.crashed:
                        self.drone.crashed = True
                        if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                            print("Mission failed: Time/battery exhausted")
                
                # Check range limit (with debug override)
                if not DebugConfig.DISABLE_RANGE_LIMITS and hasattr(self.drone, 'get_range_from_start_km'):
                    range_percentage = (self.drone.get_range_from_start_km() / self.config['max_range_km']) * 100
                    if range_percentage > 95:
                        if not self.drone.crashed:
                            self.drone.crashed = True
                            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                                print("Mission failed: Maximum range exceeded")
                
                # Draw TRUE FIRST-PERSON VIEW
                self.screen.fill(self.BLACK)
                self.draw_fpv_ground()        # Ground with horizon based on drone pitch
                self.draw_fpv_obstacles()     # Obstacles with true perspective
                self.draw_fpv_targets()       # Targets with proper distance scaling
                self.draw_hud()               # HUD overlay
                
                # Draw debug info overlay
                self.draw_debug_info()
            
            pygame.display.flip()
            clock.tick(60)
        
        # Cleanup
        global breaking_case
        breaking_case = True
        if ARDUINO_MODE and ser:
            ser.close()
            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                print("Arduino connection closed")
        
        # Close debug file
        if hasattr(self, 'debug_file'):
            self.debug_file.close()
            if DebugConfig.VERBOSE_CONSOLE_OUTPUT:
                print("Debug data saved to drone_debug.txt")
        
        pygame.quit()

if __name__ == "__main__":
    simulator = FPVSimulator()
    simulator.run()