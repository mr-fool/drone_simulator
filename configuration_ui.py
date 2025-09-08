import pygame
from config import DebugConfig

class ConfigurationUI:
    """Handles the drone configuration screen interface"""
    
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
        """Draw the complete configuration screen"""
        screen.fill((20, 30, 60))  # Dark blue background
        
        # Title
        title = self.font_large.render("EMG FPV Drone Training Simulator", True, self.WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 60))
        screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Configure Drone Performance & Environment", True, self.YELLOW)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width//2, 90))
        screen.blit(subtitle, subtitle_rect)
        
        # Configuration sections
        left_col_x = 50
        right_col_x = 650
        section_y = 140
        
        # Draw performance options
        self._draw_speed_configuration(screen, left_col_x, section_y, current_config)
        self._draw_range_configuration(screen, left_col_x, section_y + 170, current_config)
        
        # Draw environment options
        self._draw_environment_configuration(screen, right_col_x, section_y, current_config)
        
        # Draw current configuration and start button
        self._draw_current_config_and_start(screen, left_col_x, 580, current_config)
    
    def _draw_speed_configuration(self, screen, x, y, config):
        """Draw speed configuration options"""
        speed_title = self.font_medium.render("Speed Configuration", True, self.WHITE)
        screen.blit(speed_title, (x, y))
        
        speed_options = [
            ("1 - Racing (180 km/h)", 180, "Professional FPV racing"),
            ("2 - Sport (120 km/h)", 120, "Recreational flying"),
            ("3 - Custom (200 km/h)", 200, "High-performance setup")
        ]
        
        for i, (option, speed, desc) in enumerate(speed_options):
            y_pos = y + 35 + i * 40
            color = self.GREEN if speed == config['max_speed_kmh'] else self.WHITE
            option_text = self.font_small.render(option, True, color)
            screen.blit(option_text, (x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            screen.blit(desc_text, (x + 20, y_pos + 18))
    
    def _draw_range_configuration(self, screen, x, y, config):
        """Draw range configuration options"""
        range_title = self.font_medium.render("Range Configuration", True, self.WHITE)
        screen.blit(range_title, (x, y))
        
        range_options = [
            ("4 - Short (2 km)", 2, "Close operations"),
            ("5 - Medium (5 km)", 5, "Standard range"),
            ("6 - Long (10 km)", 10, "Extended range")
        ]
        
        for i, (option, range_val, desc) in enumerate(range_options):
            y_pos = y + 35 + i * 40
            color = self.GREEN if range_val == config['max_range_km'] else self.WHITE
            option_text = self.font_small.render(option, True, color)
            screen.blit(option_text, (x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            screen.blit(desc_text, (x + 20, y_pos + 18))
    
    def _draw_environment_configuration(self, screen, x, y, config):
        """Draw environment configuration options"""
        env_title = self.font_medium.render("Environment Selection", True, self.WHITE)
        screen.blit(env_title, (x, y))
        
        env_options = [
            ("7 - Urban Buildings", "buildings", "Skyscrapers and city structures", "Navigate between tall buildings"),
            ("8 - Natural Forest", "forest", "Trees and organic obstacles", "Slalom through forest terrain"),
            ("9 - Hybrid Course", "hybrid", "Mixed urban and nature", "Varied environment challenges")
        ]
        
        for i, (option, env_type, desc, detail) in enumerate(env_options):
            y_pos = y + 35 + i * 65
            color = self.GREEN if env_type == config['environment_type'] else self.WHITE
            option_text = self.font_small.render(option, True, color)
            screen.blit(option_text, (x + 20, y_pos))
            
            desc_text = self.font_small.render(desc, True, self.GRAY)
            screen.blit(desc_text, (x + 20, y_pos + 18))
            
            detail_text = self.font_small.render(detail, True, (150, 150, 150))
            screen.blit(detail_text, (x + 20, y_pos + 36))
        
        # Environment Preview
        self._draw_environment_preview(screen, x, y + 250, config)
    
    def _draw_environment_preview(self, screen, x, y, config):
        """Draw environment preview visualization"""
        preview_title = self.font_small.render("Environment Preview:", True, self.YELLOW)
        screen.blit(preview_title, (x, y))
        
        # Draw mini preview based on selected environment
        preview_rect = pygame.Rect(x + 20, y + 25, 200, 100)
        pygame.draw.rect(screen, (40, 40, 60), preview_rect)
        pygame.draw.rect(screen, self.WHITE, preview_rect, 2)
        
        center_x = preview_rect.centerx
        center_y = preview_rect.centery
        
        if config['environment_type'] == "buildings":
            self._draw_buildings_preview(screen, center_x, center_y)
        elif config['environment_type'] == "forest":
            self._draw_forest_preview(screen, center_x, center_y)
        else:  # hybrid
            self._draw_hybrid_preview(screen, center_x, center_y)
    
    def _draw_buildings_preview(self, screen, center_x, center_y):
        """Draw mini buildings preview"""
        for i, (x_offset, height) in enumerate([(-60, 40), (-20, 60), (20, 35), (60, 50)]):
            building_x = center_x + x_offset
            building_bottom = center_y + 30
            pygame.draw.rect(screen, (139, 69, 19), 
                           (building_x - 8, building_bottom - height, 16, height))
            # 3D effect
            pygame.draw.polygon(screen, (80, 40, 10), [
                (building_x + 8, building_bottom - height),
                (building_x + 12, building_bottom - height - 4),
                (building_x + 12, building_bottom - 4),
                (building_x + 8, building_bottom)
            ])
    
    def _draw_forest_preview(self, screen, center_x, center_y):
        """Draw mini trees preview"""
        for i, x_offset in enumerate([-50, -15, 15, 50]):
            tree_x = center_x + x_offset
            tree_bottom = center_y + 25
            
            # Tree trunk
            pygame.draw.rect(screen, (101, 67, 33),
                           (tree_x - 2, tree_bottom - 10, 4, 10))
            
            # Tree crown
            pygame.draw.circle(screen, (34, 139, 34),
                             (tree_x, tree_bottom - 15), 8)
    
    def _draw_hybrid_preview(self, screen, center_x, center_y):
        """Draw mixed elements preview"""
        # Building
        pygame.draw.rect(screen, (139, 69, 19),
                       (center_x - 60, center_y + 5, 12, 25))
        
        # Tree
        pygame.draw.rect(screen, (101, 67, 33),
                       (center_x - 15, center_y + 20, 3, 8))
        pygame.draw.circle(screen, (34, 139, 34),
                         (center_x - 14, center_y + 15), 6)
        
        # Another building
        pygame.draw.rect(screen, (105, 105, 105),
                       (center_x + 20, center_y - 5, 14, 35))
        
        # Another tree
        pygame.draw.rect(screen, (101, 67, 33),
                       (center_x + 50, center_y + 18, 3, 10))
        pygame.draw.circle(screen, (0, 100, 0),
                         (center_x + 51, center_y + 12), 7)
    
    def _draw_current_config_and_start(self, screen, x, y, config):
        """Draw current configuration summary and start button"""
        config_display = self.font_medium.render("Current Configuration:", True, self.YELLOW)
        screen.blit(config_display, (x, y))
        
        config_items = [
            f"Max Speed: {config['max_speed_kmh']} km/h",
            f"Max Range: {config['max_range_km']} km",
            f"Environment: {config['environment_type'].title()}"
        ]
        
        for i, item in enumerate(config_items):
            item_text = self.font_small.render(item, True, self.WHITE)
            screen.blit(item_text, (x + 20, y + 30 + i * 20))
        
        # Start button
        start_text = self.font_medium.render("Press ENTER to Start Flight Simulation", True, self.GREEN)
        start_rect = start_text.get_rect(center=(self.screen_width//2, 700))
        screen.blit(start_text, start_rect)
        
        # Control mode indicator
        control_info = self.font_small.render(
            "Control: Keyboard (WASD + Space + QE)", 
            True, self.GRAY
        )
        control_rect = control_info.get_rect(center=(self.screen_width//2, 730))
        screen.blit(control_info, control_rect)
        
        # Help text
        help_text = self.font_small.render("R = Reset | ESC = Config | Space = Quick Restart", True, self.GRAY)
        help_rect = help_text.get_rect(center=(self.screen_width//2, 750))
        screen.blit(help_text, help_rect)
    
    def handle_input(self, key, current_config):
        """Handle keyboard input for configuration changes"""
        updated_config = current_config.copy()
        
        if key == pygame.K_1:
            updated_config['max_speed_kmh'] = 180
        elif key == pygame.K_2:
            updated_config['max_speed_kmh'] = 120
        elif key == pygame.K_3:
            updated_config['max_speed_kmh'] = 200
        elif key == pygame.K_4:
            updated_config['max_range_km'] = 2
        elif key == pygame.K_5:
            updated_config['max_range_km'] = 5
        elif key == pygame.K_6:
            updated_config['max_range_km'] = 10
        elif key == pygame.K_7:
            updated_config['environment_type'] = "buildings"
        elif key == pygame.K_8:
            updated_config['environment_type'] = "forest"
        elif key == pygame.K_9:
            updated_config['environment_type'] = "hybrid"
        elif key == pygame.K_RETURN:
            return updated_config, "START_SIMULATION"
        
        return updated_config, "CONTINUE_CONFIG"