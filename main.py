import sys
import pygame
import math
import random
import threading
import time
import os
import json
from dataclasses import dataclass
from typing import List, Tuple

# Add subdirectories to Python path
project_root = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(project_root, 'core_systems'))
sys.path.insert(0, os.path.join(project_root, 'research_modules'))

# Import custom classes (now using simple imports)
from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone
from vector3 import Vector3
from drone import FPVDrone
from physics_manager import physics_manager, collision_manager
from research_obstacles import ResearchRenderer, RESEARCH_SCENARIOS, Target
from config import DebugConfig, PhysicsConfig, EMGConfig, UIConfig
from research_config_ui import ResearchConfigurationUI
from emg_evaluation_system import EMGEvaluationSystem
from emg_calibration_ui import EMGCalibrationUI

# Hardware control toggle
ARDUINO_MODE = False  # Set to True when Arduino is connected

# Arduino setup
ser = None
if ARDUINO_MODE:
    import serial
    arduino_port = 'COM3'  # Update for your system
    baud_rate = 115200
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=1)
        print(f"Arduino connected on {arduino_port}")
    except Exception as e:
        print(f"Arduino connection failed: {e}")
        ARDUINO_MODE = False

# EMG signal storage
emg_signals = [0.0, 0.0, 0.0, 0.0]  # throttle, yaw, pitch, roll
breaking_case = False

def arduino_data():
    """Continuously fetch EMG data from Arduino"""
    global emg_signals, breaking_case
    while not breaking_case and ARDUINO_MODE:
        try:
            if ser and ser.in_waiting > 0:
                ser_out = ser.readline().decode().strip().split(',')
                if len(ser_out) == 4:
                    parsed_signals = []
                    for signal_str in ser_out:
                        try:
                            signal_value = float(signal_str)
                            signal_value = max(0, min(1000, signal_value))  # Clamp range
                            parsed_signals.append(signal_value)
                        except ValueError:
                            parsed_signals.append(0.0)
                    emg_signals = parsed_signals
        except Exception as e:
            print(f"Arduino error: {e}")
            emg_signals = [0.0, 0.0, 0.0, 0.0]
            time.sleep(0.1)

# Start Arduino thread if connected
if ARDUINO_MODE:
    arduino_thread = threading.Thread(target=arduino_data, daemon=True)
    arduino_thread.start()

class TrainingScenario:
    """Research scenario class"""
    def __init__(self, name, description, obstacles, targets, time_limit=180):
        self.name = name
        self.description = description
        self.obstacles = obstacles  # Always empty in research mode
        self.targets = targets      # Optional navigation targets
        self.time_limit = time_limit
        self.completed = False
        self.start_time = time.time()
        
    def check_completion(self, drone):
        """Check if research scenario objectives are met"""
        if not DebugConfig.DISABLE_TARGETS:
            return len([t for t in self.targets if not t.collected]) == 0 and not drone.crashed
        else:
            # In target-free mode, completion is time-based or manual
            return False

class FPVSimulator:
    def __init__(self):
        pygame.init()
        
        # Create data directories
        self.create_data_directories()

        # Print debug status
        DebugConfig.print_research_status()

        self.WIDTH, self.HEIGHT = 1200, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("EMG Flight Control Research Platform")

        # Initialize research configuration UI
        self.config_ui = ResearchConfigurationUI(self.WIDTH, self.HEIGHT)

        # Initialize physics manager
        self.physics = physics_manager
        self.collision = collision_manager

        # Initialize HUD system
        self.hud_system = FPVHUDSystem(self.WIDTH, self.HEIGHT)
        
        # Initialize research renderer
        self.research_renderer = ResearchRenderer(self.WIDTH, self.HEIGHT)

        # EMG evaluation system
        self.emg_evaluation = EMGEvaluationSystem()
        self.calibration_ui = EMGCalibrationUI(self.WIDTH, self.HEIGHT)

        # Load images (optional for research mode)
        self.load_images()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        
        # Fonts
        self.font_small = pygame.font.Font(None, 24)
        
        # Game state for research workflow
        self.game_state = "CONFIGURATION"  # "CONFIGURATION", "EMG_CALIBRATION", "FLYING"
        self.drone = None
        self.current_scenario = None
        self.score = 0
        
        # Research session tracking
        self.research_session_id = time.strftime("%Y%m%d_%H%M%S")
        
        # Simplified configuration (research-focused)
        self.config = {
            'max_speed_kmh': 150,
            'max_range_km': 5,
            'environment_type': "research",
            'emg_connected': ARDUINO_MODE,
            'emg_logging': True
        }
        
        # Initialize EMG logging
        if self.config['emg_logging']:
            self.emg_evaluation.initialize_logging(self.research_session_id)
        
        # Control mapping
        self.emg_threshold = EMGConfig.NOISE_THRESHOLD
        self.emg_max = EMGConfig.EMG_MAX_VALUE
        
        # First-person camera
        self.camera_position = Vector3(0, 0, 0)
        self.camera_rotation = Vector3(0, 0, 0)
        
        # Debug logging
        debug_folder = "data_output/debug_logs"  # Instead of just "data_output"
        self.debug_file = open(f"{debug_folder}/research_debug_{self.research_session_id}.txt", "w")
        self.debug_file.write("Time,Throttle,Yaw,Pitch,Roll,Speed_kmh,Altitude,EMG_Quality,Fatigue_Level\n")
        self.debug_frame_counter = 0

    def create_data_directories(self):
        """Create directories for organized data storage"""
        import os
        
        directories = [
            "data_output",
            "data_output/debug_logs",
            "data_output/emg_data", 
            "data_output/reports"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")

    def load_images(self):
        """Load optional images for research mode"""
        self.images = {}
        
        image_files = {
            'sky_background': 'images/sky_background.png',
            'ground_texture': 'images/ground_texture.png',
            'checkpoint': 'images/checkpoint.png'
        }
        
        for key, filename in image_files.items():
            try:
                if os.path.exists(filename):
                    self.images[key] = pygame.image.load(filename)
                else:
                    self.images[key] = None
            except pygame.error:
                self.images[key] = None

    def create_research_scenario(self, scenario_type="basic"):
        """Create research scenario - no obstacles, optional targets"""
        if scenario_type in RESEARCH_SCENARIOS:
            obstacles, targets, name = RESEARCH_SCENARIOS[scenario_type]()
        else:
            obstacles, targets, name = RESEARCH_SCENARIOS["basic"]()
        
        return TrainingScenario(
            name,
            f"EMG research scenario: {name}",
            obstacles,  # Always empty list
            targets,    # Optional based on config
            180  # 3 minute research sessions
        )

    def handle_configuration_input(self, key):
        """Handle research configuration input"""
        updated_config, action = self.config_ui.handle_input(key, self.config)
        self.config = updated_config
        
        if action == "START_SIMULATION":
            if self.config['emg_connected']:
                self.game_state = "EMG_CALIBRATION"
                print("Starting EMG calibration process...")
            else:
                spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE
                self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
                self.current_scenario = self.create_research_scenario()
                self.game_state = "FLYING"
                print("Starting research simulation (keyboard mode)")

    def handle_calibration_input(self, key):
        """Handle EMG calibration workflow"""
        if key == pygame.K_c:
            if self.calibration_ui.calibration_state == "baseline":
                if self.emg_evaluation.calibrate_baseline():
                    self.calibration_ui.calibration_state = "throttle"
                    print("Baseline complete. Contract forearm flexor muscles for throttle...")
                    
            elif self.calibration_ui.calibration_state == "throttle":
                self.emg_evaluation.calibrate_maximum("throttle")
                self.calibration_ui.calibration_state = "yaw"
                print("Throttle calibrated. Contract forearm extensor muscles for yaw...")
                
            elif self.calibration_ui.calibration_state == "yaw":
                self.emg_evaluation.calibrate_maximum("yaw")
                self.calibration_ui.calibration_state = "pitch"
                print("Yaw calibrated. Contract bicep for pitch...")
                
            elif self.calibration_ui.calibration_state == "pitch":
                self.emg_evaluation.calibrate_maximum("pitch")
                self.calibration_ui.calibration_state = "roll"
                print("Pitch calibrated. Contract tricep for roll...")
                
            elif self.calibration_ui.calibration_state == "roll":
                self.emg_evaluation.calibrate_maximum("roll")
                self.calibration_ui.calibration_state = "complete"
                print("EMG calibration complete! System ready for research.")
        
        elif key == pygame.K_SPACE and self.calibration_ui.calibration_state == "complete":
            spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE
            self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
            self.current_scenario = self.create_research_scenario()
            self.game_state = "FLYING"
            print("Starting EMG research flight session...")

    def process_emg_controls(self):
        """Enhanced EMG processing with proper hardware detection"""
        if ARDUINO_MODE:
            # Pass Arduino connection status to EMG evaluation
            self.emg_evaluation.arduino_connected = True
            self.emg_evaluation.update_emg_signals(emg_signals, arduino_connected=True)
            processed_signals = self.emg_evaluation.process_signals(emg_signals)
            throttle, yaw, pitch, roll = processed_signals
            
            if hasattr(self.drone, 'velocity'):
                actual_response = [
                    abs(self.drone.velocity.y),
                    abs(self.drone.rotation.y), 
                    abs(self.drone.rotation.x),
                    abs(self.drone.rotation.z)
                ]
                self.emg_evaluation.calculate_control_accuracy(processed_signals, actual_response)
            
            return throttle, yaw, pitch, roll
        else:
            # Keyboard controls - don't process fake EMG data
            self.emg_evaluation.arduino_connected = False
            keys = pygame.key.get_pressed()
            
            # FIXED: Reduce keyboard throttle from 1.0 to 0.3 for gradual response
            throttle = 0.3 if (keys[pygame.K_SPACE] and not self.drone.crashed) else 0.0
            yaw = (-0.5 if keys[pygame.K_q] else 0.0) + (0.5 if keys[pygame.K_e] else 0.0)
            pitch = (0.5 if keys[pygame.K_w] else 0.0) + (-0.5 if keys[pygame.K_s] else 0.0)
            roll = (-0.5 if keys[pygame.K_a] else 0.0) + (0.5 if keys[pygame.K_d] else 0.0)
            
            # Don't simulate fake EMG signals when no Arduino
            return throttle, yaw, pitch, roll

    def project_3d_to_fpv(self, world_pos, drone_position=None, drone_rotation=None):
        """Use unified projection from physics manager"""
        # Use provided parameters or default to current drone position/rotation
        camera_pos = drone_position if drone_position is not None else self.drone.position
        camera_rot = drone_rotation if drone_rotation is not None else self.drone.rotation
        
        return self.physics.project_3d_to_screen(
            world_pos, 
            camera_pos, 
            camera_rot
        )

    def check_ground_collision(self):
        """Use unified ground collision detection"""
        if DebugConfig.DISABLE_GROUND_COLLISION:
            return False
        return self.collision.check_drone_ground_collision(self.drone)

    def check_fpv_target_collection(self):
        """Use unified target collection"""
        return self.collision.check_target_collection(
            self.drone, 
            self.current_scenario.targets, 
            self.drone.rotation
        )

    def draw_fpv_ground(self):
        """Draw ground using unified horizon calculation"""
        actual_altitude = self.physics.get_altitude_from_world_y(self.drone.position.y)
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
                
                r = max(0, min(255, int(base_r + (25 * color_ratio))))
                g = max(0, min(255, int(base_g + (25 * color_ratio))))
                b = max(0, min(255, int(base_b + (20 * color_ratio))))
                
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

    def draw_research_targets(self):
        """Draw research targets using simplified renderer"""
        for target in self.current_scenario.targets:
            self.research_renderer.draw_target(
                self.screen, 
                target, 
                self.project_3d_to_fpv,  # Use the original method
                self.drone.position,
                self.drone.rotation
            )

    def draw_hud(self):
        """Draw HUD using integration function"""
        targets_remaining = len([t for t in self.current_scenario.targets if not t.collected])
        elapsed_time = time.time() - self.current_scenario.start_time
        time_left = max(0, self.current_scenario.time_limit - elapsed_time)
        
        mission_data = {
            'mission_name': self.current_scenario.name,
            'targets_remaining': targets_remaining,
            'time_left': time_left
        }
        
        integrate_hud_with_drone(self.drone, self.hud_system, self.screen, mission_data)

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

    def log_research_data(self, throttle, yaw, pitch, roll):
        """Log research data every 10th frame"""
        self.debug_frame_counter += 1
        
        if self.debug_frame_counter % 10 == 0:
            current_time = time.time()
            signal_quality = self.emg_evaluation.evaluate_signal_quality()
            fatigue_level = self.emg_evaluation.detect_fatigue()
            
            debug_line = (f"{current_time:.2f},{throttle:.2f},{yaw:.2f},{pitch:.2f},{roll:.2f},"
                         f"{self.drone.get_speed_kmh():.1f},"
                         f"{self.physics.get_altitude_from_world_y(self.drone.position.y):.1f},"
                         f"{signal_quality},{fatigue_level:.1f}\n")
            
            self.debug_file.write(debug_line)
            self.debug_file.flush()

    def run(self):
        """Main research loop"""
        clock = pygame.time.Clock()
        running = True
        
        print("=== EMG Flight Control Research Platform ===")
        print("BioAmp EXG Pill + Arduino Uno R4")
        print("HardwareX Publication Platform")
        print("Research Focus: EMG signal validation")
        print("=" * 50)
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if self.game_state == "CONFIGURATION":
                        self.handle_configuration_input(event.key)
                        
                    elif self.game_state == "EMG_CALIBRATION":
                        self.handle_calibration_input(event.key)
                        
                    elif self.game_state == "FLYING":
                        if event.key == pygame.K_r:
                            spawn_y = DebugConfig.SAFE_SPAWN_ALTITUDE
                            self.drone = FPVDrone(100, spawn_y, 0, self.config['max_speed_kmh'], self.config['max_range_km'])
                            self.current_scenario = self.create_research_scenario()
                            print("Research session reset")
                            
                        elif event.key == pygame.K_ESCAPE:
                            self.game_state = "CONFIGURATION"
                            print("Returned to configuration")
                            
                        elif event.key == pygame.K_e:
                            report = self.emg_evaluation.generate_evaluation_report()
                            self.save_evaluation_report(report)
                            print("Research evaluation report generated")
            
            # Render based on current state
            if self.game_state == "CONFIGURATION":
                self.config_ui.draw_screen(self.screen, self.config)
                
            elif self.game_state == "EMG_CALIBRATION":
                self.calibration_ui.draw_calibration_screen(self.screen, self.emg_evaluation)
                
                if ARDUINO_MODE:
                    self.emg_evaluation.update_emg_signals(emg_signals)
                else:
                    # Simulate EMG for testing
                    keys = pygame.key.get_pressed()
                    test_signals = [
                        random.uniform(20, 80) if keys[pygame.K_SPACE] else random.uniform(10, 30),
                        random.uniform(20, 80) if keys[pygame.K_q] or keys[pygame.K_e] else random.uniform(10, 30),
                        random.uniform(20, 80) if keys[pygame.K_w] or keys[pygame.K_s] else random.uniform(10, 30),
                        random.uniform(20, 80) if keys[pygame.K_a] or keys[pygame.K_d] else random.uniform(10, 30)
                    ]
                    self.emg_evaluation.update_emg_signals(test_signals)
                
            elif self.game_state == "FLYING":
                throttle, yaw, pitch, roll = self.process_emg_controls()
                self.drone.update_physics(throttle, yaw, pitch, roll, emg_signals if ARDUINO_MODE else None)
                
                self.log_research_data(throttle, yaw, pitch, roll)
                
                if self.check_ground_collision():
                     if not self.drone.crashed:  # Only crash once
                        self.drone.crashed = True
                        self.drone.velocity = Vector3(0, 0, 0)  # Stop all movement
                        print(f"GROUND COLLISION at {self.drone.get_speed_kmh():.0f} km/h")
                
                if not DebugConfig.DISABLE_TARGETS:
                    collected_target = self.check_fpv_target_collection()
                    if collected_target:
                        print(f"Research waypoint reached at {self.drone.get_speed_kmh():.0f} km/h")
                
                self.camera_position = self.drone.position
                self.camera_rotation = self.drone.rotation
                
                fatigue_level = self.emg_evaluation.detect_fatigue()
                if fatigue_level > 50:
                    print(f"Research Note: High muscle fatigue detected ({fatigue_level:.1f}%)")
                
                # Render flight view
                self.screen.fill(self.BLACK)
                self.draw_fpv_ground()
                
                if not DebugConfig.DISABLE_TARGETS:
                    self.draw_research_targets()
                
                self.draw_hud()
                
                if EMGConfig.SHOW_EMG_SIGNALS and ARDUINO_MODE:
                    self.emg_evaluation.draw_evaluation_hud(self.screen, 10, 10)
                
                self.draw_debug_info()
            
            pygame.display.flip()
            clock.tick(60)
        
        self.cleanup_research_session()

    def save_evaluation_report(self, report):
        """Save research evaluation report"""
        
        # Ensure reports directory exists
        os.makedirs("data_output/reports", exist_ok=True)

        filename = f"data_output/reports/emg_research_report_{self.research_session_id}.json"
        with open(filename, 'w') as f:
            serializable_report = {}
            for key, value in report.items():
                if hasattr(value, 'tolist'):
                    serializable_report[key] = value.tolist()
                else:
                    serializable_report[key] = value
            
            json.dump(serializable_report, f, indent=2)
        
        print(f"Research report saved: {filename}")
        
        print("\n=== EMG RESEARCH SUMMARY ===")
        print(f"Session Duration: {report['session_duration']:.1f} seconds")
        print(f"Signal Quality: {report['signal_quality']}")
        print(f"Control Accuracy: {report['control_accuracy']:.1f}%")
        print(f"Fatigue Level: {report['fatigue_level']:.1f}%")
        print("SNR Values:")
        for channel, snr in report['snr_values'].items():
            print(f"  {channel}: {snr:.1f} dB")
        print("=" * 30)

    def cleanup_research_session(self):
        """Clean up and finalize research session"""
        global breaking_case
        breaking_case = True
        
        self.emg_evaluation.close_logging()
        final_report = self.emg_evaluation.generate_evaluation_report()
        self.save_evaluation_report(final_report)
        
        if hasattr(self, 'debug_file'):
            self.debug_file.close()
            print(f"Research debug data saved: research_debug_{self.research_session_id}.txt")
        
        if ARDUINO_MODE and ser:
            ser.close()
            print("Arduino connection closed")
        
        print("EMG research session completed")
        print(f"All data files saved with session ID: {self.research_session_id}")
        pygame.quit()


if __name__ == "__main__":
    # Force research mode configuration
    DebugConfig.RESEARCH_MODE = True
    DebugConfig.EMPTY_ENVIRONMENT = True
    DebugConfig.DISABLE_OBSTACLES = True
    
    # Initialize and run research simulator
    simulator = FPVSimulator()
    simulator.run()