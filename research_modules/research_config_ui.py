import pygame
from config import DebugConfig, EMGConfig

class ResearchConfigurationUI:
    """Simplified configuration UI focused on EMG research parameters"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
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
    
    def draw_screen(self, screen, current_config):
        """Draw the research configuration screen"""
        screen.fill((20, 30, 60))  # Dark blue background
        
        # Title
        title = self.font_large.render("EMG Flight Control Research Platform", True, self.WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 60))
        screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("BioAmp EXG Pill + Arduino Uno R4", True, self.YELLOW)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width//2, 90))
        screen.blit(subtitle, subtitle_rect)
        
        research_note = self.font_small.render("HardwareX Publication Platform - EMG Signal Validation", True, self.GRAY)
        research_rect = research_note.get_rect(center=(self.screen_width//2, 115))
        screen.blit(research_note, research_rect)
        
        # Configuration sections
        left_col_x = 100
        right_col_x = 650
        section_y = 160
        
        # Draw flight parameters
        self._draw_flight_configuration(screen, left_col_x, section_y, current_config)
        
        # Draw EMG settings
        self._draw_emg_configuration(screen, right_col_x, section_y, current_config)
        
        # Draw research environment info - MOVED DOWN MORE
        self._draw_research_environment(screen, right_col_x, section_y + 320, current_config)
        
        # Draw start section - MOVED DOWN MORE  
        self._draw_start_section(screen, left_col_x, 620, current_config)
    
    def _draw_flight_configuration(self, screen, x, y, config):
        """Draw flight performance parameters"""
        flight_title = self.font_medium.render("Flight Parameters", True, self.WHITE)
        screen.blit(flight_title, (x, y))
        
        speed_options = [
            ("1 - Conservative (120 km/h)", 120, "Stable flight for initial testing"),
            ("2 - Standard (150 km/h)", 150, "Balanced performance"),
            ("3 - High Performance (180 km/h)", 180, "Racing drone characteristics")
        ]
        
        for i, (option, speed, desc) in enumerate(speed_options):
            y_pos = y + 35 + i * 45
            color = self.GREEN if speed == config['max_speed_kmh'] else self.WHITE
            option_text = self.font_small.render(option, True, color)
            screen.blit(option_text, (x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            screen.blit(desc_text, (x + 20, y_pos + 18))
        
        # Range options
        range_y = y + 170
        range_title = self.font_medium.render("Flight Range", True, self.WHITE)
        screen.blit(range_title, (x, range_y))
        
        range_options = [
            ("4 - Short Range (2 km)", 2, "Close-proximity testing"),
            ("5 - Medium Range (5 km)", 5, "Standard research range"),
        ]
        
        for i, (option, range_val, desc) in enumerate(range_options):
            y_pos = range_y + 35 + i * 45
            color = self.GREEN if range_val == config['max_range_km'] else self.WHITE
            option_text = self.font_small.render(option, True, color)
            screen.blit(option_text, (x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            screen.blit(desc_text, (x + 20, y_pos + 18))
    
    def _draw_emg_configuration(self, screen, x, y, config):
        """Draw EMG hardware settings"""
        emg_title = self.font_medium.render("EMG Configuration", True, self.WHITE)
        screen.blit(emg_title, (x, y))
        
        # Hardware status
        hardware_status = "Connected" if config.get('emg_connected', False) else "Simulated"
        status_color = self.GREEN if config.get('emg_connected', False) else self.YELLOW
        status_text = self.font_small.render(f"Hardware Status: {hardware_status}", True, status_color)
        screen.blit(status_text, (x + 20, y + 30))
        
        # Channel mapping
        channel_y = y + 60
        channel_title = self.font_small.render("EMG Channel Mapping:", True, self.WHITE)
        screen.blit(channel_title, (x + 20, channel_y))
        
        channels = [
            "A0: Forearm Flexor - Throttle",
            "A1: Forearm Extensor - Yaw", 
            "A2: Bicep Brachii - Pitch",
            "A3: Tricep Brachii - Roll"
        ]
        
        for i, channel in enumerate(channels):
            channel_text = self.font_small.render(channel, True, self.BLUE)
            screen.blit(channel_text, (x + 40, channel_y + 25 + i * 20))
        
        # EMG settings
        settings_y = channel_y + 120
        settings_title = self.font_small.render("Signal Processing:", True, self.WHITE)
        screen.blit(settings_title, (x + 20, settings_y))
        
        threshold_text = self.font_small.render(f"Noise Threshold: {EMGConfig.NOISE_THRESHOLD}", True, self.GRAY)
        screen.blit(threshold_text, (x + 40, settings_y + 25))
        
        sample_rate_text = self.font_small.render(f"Sample Rate: {EMGConfig.SAMPLE_RATE} Hz", True, self.GRAY)
        screen.blit(sample_rate_text, (x + 40, settings_y + 45))
        
        # Calibration reminder
        cal_y = settings_y + 80
        cal_title = self.font_small.render("6 - Toggle EMG Logging", True, self.WHITE)
        logging_status = "ENABLED" if config.get('emg_logging', True) else "DISABLED"
        logging_color = self.GREEN if config.get('emg_logging', True) else self.RED
        
        screen.blit(cal_title, (x + 20, cal_y))
        log_text = self.font_small.render(f"Data Logging: {logging_status}", True, logging_color)
        screen.blit(log_text, (x + 40, cal_y + 20))
    
    def _draw_research_environment(self, screen, x, y, config):
        """Draw research environment information"""
        env_title = self.font_medium.render("Research Environment", True, self.WHITE)
        screen.blit(env_title, (x, y))
        
        # Environment characteristics
        env_features = [
            "* Obstacles: DISABLED (research focus)",
            "* Ground Collision: ENABLED (primary challenge)",
            "* Navigation Targets: OPTIONAL",
            "* Physics: Realistic flight dynamics",
            "* Data Logging: Comprehensive EMG + flight data"
        ]
        
        for i, feature in enumerate(env_features):
            color = self.GREEN if feature.startswith("*") else self.GRAY
            feature_text = self.font_small.render(feature, True, color)
            screen.blit(feature_text, (x + 20, y + 35 + i * 22))
        
        # Research objectives
        obj_y = y + 160
        obj_title = self.font_small.render("Research Objectives:", True, self.YELLOW)
        screen.blit(obj_title, (x + 20, obj_y))
        
        objectives = [
            "- Validate EMG signal quality and control precision",
            "- Measure system response time and accuracy", 
            "- Collect data for HardwareX publication"
        ]
        
        for i, objective in enumerate(objectives):
            obj_text = self.font_small.render(objective, True, self.WHITE)
            screen.blit(obj_text, (x + 40, obj_y + 25 + i * 20))
    
    def _draw_start_section(self, screen, x, y, config):
        """Draw configuration summary and start options"""
        config_title = self.font_medium.render("Current Configuration:", True, self.YELLOW)
        screen.blit(config_title, (x, y))
        
        config_items = [
            f"Max Speed: {config['max_speed_kmh']} km/h",
            f"Max Range: {config['max_range_km']} km",
            f"Environment: Empty (Research Mode)",
            f"EMG Logging: {'ON' if config.get('emg_logging', True) else 'OFF'}"
        ]
        
        for i, item in enumerate(config_items):
            item_text = self.font_small.render(item, True, self.WHITE)
            screen.blit(item_text, (x + 20, y + 30 + i * 20))
        
        # Start instructions - moved up slightly
        start_y = y + 140  # Reduced from 160 to 140
        
        if config.get('emg_connected', False):
            start_instruction = "ENTER - Start EMG Calibration"
            start_color = self.GREEN
        else:
            start_instruction = "ENTER - Start Simulation (Keyboard Mode)"
            start_color = self.YELLOW
        
        start_text = self.font_medium.render(start_instruction, True, start_color)
        start_rect = start_text.get_rect(center=(self.screen_width//2, start_y))
        screen.blit(start_text, start_rect)
        
        # Controls reminder - reduced spacing
        controls_text = self.font_small.render(
            "Controls: WASD + Space + QE | R = Reset | ESC = Return to Config",
            True, self.GRAY
        )
        controls_rect = controls_text.get_rect(center=(self.screen_width//2, start_y + 25))  # Reduced from 35 to 25
        screen.blit(controls_text, controls_rect)
        
    def handle_input(self, key, current_config):
        """Handle simplified research configuration input"""
        updated_config = current_config.copy()
        
        # Flight speed options
        if key == pygame.K_1:
            updated_config['max_speed_kmh'] = 120
        elif key == pygame.K_2:
            updated_config['max_speed_kmh'] = 150
        elif key == pygame.K_3:
            updated_config['max_speed_kmh'] = 180
        
        # Range options
        elif key == pygame.K_4:
            updated_config['max_range_km'] = 2
        elif key == pygame.K_5:
            updated_config['max_range_km'] = 5
        
        # EMG logging toggle
        elif key == pygame.K_6:
            updated_config['emg_logging'] = not updated_config.get('emg_logging', True)
        
        # Start simulation
        elif key == pygame.K_RETURN:
            # Force research environment settings
            updated_config['environment_type'] = "research"
            return updated_config, "START_SIMULATION"
        
        return updated_config, "CONTINUE_CONFIG"