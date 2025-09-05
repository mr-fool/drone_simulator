import pygame
import math
import time

class FPVHUDSystem:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Colors for HUD elements
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.BLUE = (0, 150, 255)
        self.ORANGE = (255, 165, 0)
        self.CYAN = (0, 255, 255)
        self.GRAY = (128, 128, 128)
        self.DARK_GRAY = (64, 64, 64)
        self.BLACK = (0, 0, 0)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # HUD element positions - MOVED ATTITUDE INDICATOR RIGHT
        self.compass_center = (screen_width // 2, 80)
        self.compass_radius = 60
        
        self.attitude_center = (150, screen_height // 2)  # Moved from 100 to 150
        self.attitude_size = 120
        
        self.speed_pos = (50, 150)
        self.altitude_pos = (screen_width - 150, 150)
        self.battery_pos = (50, 50)
        self.range_pos = (screen_width - 200, 50)
        
    def draw_compass(self, screen, heading):
        """Draw compass that rotates with heading"""
        center_x, center_y = self.compass_center
        
        # Outer compass ring
        pygame.draw.circle(screen, self.WHITE, (center_x, center_y), self.compass_radius, 3)
        pygame.draw.circle(screen, self.BLACK, (center_x, center_y), self.compass_radius - 3, 0)
        
        # Cardinal directions - rotate with heading
        directions = [
            (0, "N", self.RED),
            (90, "E", self.WHITE), 
            (180, "S", self.WHITE),
            (270, "W", self.WHITE)
        ]
        
        for angle, label, color in directions:
            # Calculate rotated position
            marker_angle = math.radians(angle - heading)
            marker_x = center_x + math.sin(marker_angle) * (self.compass_radius - 15)
            marker_y = center_y - math.cos(marker_angle) * (self.compass_radius - 15)
            
            # Draw direction marker
            text = self.font_small.render(label, True, color)
            text_rect = text.get_rect(center=(marker_x, marker_y))
            screen.blit(text, text_rect)
        
        # Center dot
        pygame.draw.circle(screen, self.WHITE, (center_x, center_y), 3)
        
        # Heading text
        heading_value = int(heading) % 360
        heading_text = self.font_medium.render(f"{heading_value:03d}°", True, self.YELLOW)
        heading_rect = heading_text.get_rect(center=(center_x, center_y + self.compass_radius + 20))
        screen.blit(heading_text, heading_rect)

    def draw_artificial_horizon(self, screen, pitch, roll):
        """Draw artificial horizon - shows actual drone orientation with proper circular clipping"""
        center_x, center_y = self.attitude_center
        size = self.attitude_size
        
        # Create a surface for the horizon
        horizon_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        
        # Fill entire surface with brown ground
        pygame.draw.circle(horizon_surface, (139, 69, 19), (size, size), size)  # Ground color

        # Calculate horizon line position based on pitch
        horizon_y = size - (pitch * 3)  # Negative because up pitch should show more sky

        # Draw sky portion above horizon line - but only within the circle
        for x in range(size * 2):
            for y in range(0, int(horizon_y)):
                # Check if this pixel is within the circle
                dist = math.sqrt((x - size) ** 2 + (y - size) ** 2)
                if dist <= size:
                    horizon_surface.set_at((x, y), self.BLUE)  # Sky color
        
        
        # Draw horizon line
        pygame.draw.line(horizon_surface, self.WHITE, (0, horizon_y), (size * 2, horizon_y), 3)
        
        # Apply roll rotation to the entire horizon
        if abs(roll) > 0.1:
            # Rotate the horizon surface
            rotated_surface = pygame.transform.rotate(horizon_surface, roll)
            
            # Get the center of the rotated surface
            rotated_rect = rotated_surface.get_rect()
            
            # Calculate offset to center the rotated surface
            offset_x = center_x - rotated_rect.width // 2
            offset_y = center_y - rotated_rect.height // 2
            
            # Create a clipping mask to ensure we only draw within the original circle
            temp_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            
            # Extract only the circular portion from the rotated surface
            for x in range(size * 2):
                for y in range(size * 2):
                    # Check if this pixel should be within our target circle
                    dist = math.sqrt((x - size) ** 2 + (y - size) ** 2)
                    if dist <= size:
                        # Calculate where this pixel comes from in the rotated surface
                        src_x = x + (rotated_rect.width // 2 - size)
                        src_y = y + (rotated_rect.height // 2 - size)
                        
                        if (0 <= src_x < rotated_surface.get_width() and 
                            0 <= src_y < rotated_surface.get_height()):
                            pixel_color = rotated_surface.get_at((src_x, src_y))
                            temp_surface.set_at((x, y), pixel_color)
            
            # Blit the clipped surface
            screen.blit(temp_surface, (center_x - size, center_y - size))
        else:
            # No rotation - blit directly
            screen.blit(horizon_surface, (center_x - size, center_y - size))
        
        # Draw white circle frame
        pygame.draw.circle(screen, self.WHITE, (center_x, center_y), size, 3)
        
        # Aircraft symbol (fixed in center - represents your drone)
        pygame.draw.line(screen, self.YELLOW, (center_x - 20, center_y), (center_x + 20, center_y), 4)
        pygame.draw.line(screen, self.YELLOW, (center_x, center_y - 5), (center_x, center_y + 5), 4)
        
    def draw_speed_indicator(self, screen, current_speed, max_speed):
        """Draw vertical speed tape"""
        x, y = self.speed_pos
        tape_height = 200
        tape_width = 60
        
        # Speed tape background
        pygame.draw.rect(screen, (0, 0, 0, 180), (x, y, tape_width, tape_height))
        pygame.draw.rect(screen, self.WHITE, (x, y, tape_width, tape_height), 2)
        
        # Speed markings
        speed_range = 100
        center_y = y + tape_height // 2
        
        for speed in range(max(0, int(current_speed) - speed_range//2), 
                          int(current_speed) + speed_range//2, 10):
            mark_y = center_y - (speed - current_speed) * 2
            
            if y <= mark_y <= y + tape_height:
                if speed % 20 == 0:
                    pygame.draw.line(screen, self.WHITE, (x + tape_width - 15, mark_y), (x + tape_width, mark_y), 2)
                    speed_text = self.font_tiny.render(str(speed), True, self.WHITE)
                    screen.blit(speed_text, (x + 5, mark_y - 8))
                else:
                    pygame.draw.line(screen, self.GRAY, (x + tape_width - 8, mark_y), (x + tape_width, mark_y), 1)
        
        # Current speed indicator
        pygame.draw.polygon(screen, self.YELLOW, [
            (x + tape_width, center_y - 8),
            (x + tape_width + 15, center_y),
            (x + tape_width, center_y + 8)
        ])
        
        # Speed readout
        speed_text = self.font_medium.render(f"{current_speed:.0f}", True, self.YELLOW)
        speed_bg = pygame.Rect(x + tape_width + 20, center_y - 15, 60, 30)
        pygame.draw.rect(screen, self.BLACK, speed_bg)
        pygame.draw.rect(screen, self.YELLOW, speed_bg, 2)
        screen.blit(speed_text, (speed_bg.x + 5, speed_bg.y + 5))
        
    def draw_altitude_indicator(self, screen, altitude):
        """Draw vertical altitude tape"""
        x, y = self.altitude_pos
        tape_height = 200
        tape_width = 60
        
        # Altitude tape background
        pygame.draw.rect(screen, (0, 0, 0, 180), (x, y, tape_width, tape_height))
        pygame.draw.rect(screen, self.WHITE, (x, y, tape_width, tape_height), 2)
        
        # Altitude markings
        altitude_range = 200
        center_y = y + tape_height // 2
        
        for alt in range(max(0, int(altitude) - altitude_range//2), 
                        int(altitude) + altitude_range//2, 10):
            mark_y = center_y + (alt - altitude) * 1
            
            if y <= mark_y <= y + tape_height:
                if alt % 50 == 0:
                    pygame.draw.line(screen, self.WHITE, (x, mark_y), (x + 15, mark_y), 2)
                    alt_text = self.font_tiny.render(str(alt), True, self.WHITE)
                    screen.blit(alt_text, (x + 20, mark_y - 8))
                else:
                    pygame.draw.line(screen, self.GRAY, (x, mark_y), (x + 8, mark_y), 1)
        
        # Current altitude indicator
        pygame.draw.polygon(screen, self.YELLOW, [
            (x - 15, center_y),
            (x, center_y - 8),
            (x, center_y + 8)
        ])
        
        # Altitude readout
        alt_text = self.font_medium.render(f"{altitude:.0f}m", True, self.YELLOW)
        alt_bg = pygame.Rect(x - 80, center_y - 15, 70, 30)
        pygame.draw.rect(screen, self.BLACK, alt_bg)
        pygame.draw.rect(screen, self.YELLOW, alt_bg, 2)
        screen.blit(alt_text, (alt_bg.x + 5, alt_bg.y + 5))
        
    def draw_battery_indicator(self, screen, battery_percentage, voltage=None):
        """Draw battery status"""
        x, y = self.battery_pos
        battery_width = 60
        battery_height = 20
        
        pygame.draw.rect(screen, self.WHITE, (x, y, battery_width, battery_height), 2)
        pygame.draw.rect(screen, self.WHITE, (x + battery_width, y + 5, 4, battery_height - 10))
        
        # Battery fill
        fill_width = int((battery_percentage / 100) * (battery_width - 4))
        fill_color = self.GREEN if battery_percentage > 30 else self.YELLOW if battery_percentage > 15 else self.RED
        
        if battery_percentage > 0:
            pygame.draw.rect(screen, fill_color, (x + 2, y + 2, fill_width, battery_height - 4))
        
        # Battery percentage text
        battery_text = self.font_small.render(f"{battery_percentage:.0f}%", True, self.WHITE)
        screen.blit(battery_text, (x, y + battery_height + 5))
        
        if voltage:
            voltage_text = self.font_tiny.render(f"{voltage:.1f}V", True, self.GRAY)
            screen.blit(voltage_text, (x, y + battery_height + 25))
        
    def draw_range_indicator(self, screen, current_range, max_range):
        """Draw range indicator"""
        x, y = self.range_pos
        circle_radius = 30
        pygame.draw.circle(screen, self.WHITE, (x, y), circle_radius, 2)
        
        # Range fill
        range_percentage = min(current_range / max_range, 1.0)
        fill_angle = range_percentage * 360
        
        if range_percentage > 0:
            arc_color = self.GREEN if range_percentage < 0.7 else self.YELLOW if range_percentage < 0.9 else self.RED
            
            for angle in range(0, int(fill_angle), 2):
                angle_rad = math.radians(angle - 90)
                start_x = x + math.cos(angle_rad) * (circle_radius - 5)
                start_y = y + math.sin(angle_rad) * (circle_radius - 5)
                end_x = x + math.cos(angle_rad) * circle_radius
                end_y = y + math.sin(angle_rad) * circle_radius
                pygame.draw.line(screen, arc_color, (start_x, start_y), (end_x, end_y), 3)
        
        # Range text
        range_text = self.font_small.render(f"{current_range:.1f}km", True, self.WHITE)
        range_rect = range_text.get_rect(center=(x, y))
        screen.blit(range_text, range_rect)
        
        max_text = self.font_tiny.render(f"/{max_range:.0f}km", True, self.GRAY)
        screen.blit(max_text, (x - 25, y + circle_radius + 10))
        
    def draw_crosshair(self, screen):
        """Draw center crosshair"""
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2
        
        # Main crosshair
        crosshair_size = 20
        pygame.draw.line(screen, self.GREEN, 
                        (center_x - crosshair_size, center_y), 
                        (center_x + crosshair_size, center_y), 2)
        pygame.draw.line(screen, self.GREEN,
                        (center_x, center_y - crosshair_size),
                        (center_x, center_y + crosshair_size), 2)
        
        # Center dot
        pygame.draw.circle(screen, self.GREEN, (center_x, center_y), 3)
        
        # Corner brackets
        bracket_size = 5
        bracket_distance = 50
        
        corners = [
            (center_x - bracket_distance, center_y - bracket_distance),
            (center_x + bracket_distance, center_y - bracket_distance),
            (center_x - bracket_distance, center_y + bracket_distance),
            (center_x + bracket_distance, center_y + bracket_distance)
        ]
        
        for i, (corner_x, corner_y) in enumerate(corners):
            if i == 0:  # Top-left
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x + bracket_size, corner_y), 2)
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x, corner_y + bracket_size), 2)
            elif i == 1:  # Top-right
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x - bracket_size, corner_y), 2)
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x, corner_y + bracket_size), 2)
            elif i == 2:  # Bottom-left
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x + bracket_size, corner_y), 2)
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x, corner_y - bracket_size), 2)
            elif i == 3:  # Bottom-right
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x - bracket_size, corner_y), 2)
                pygame.draw.line(screen, self.GREEN, (corner_x, corner_y), (corner_x, corner_y - bracket_size), 2)
    
    def draw_flight_mode_indicator(self, screen, flight_mode, armed_status):
        """Draw flight mode and armed status"""
        x = self.screen_width // 2 - 100
        y = self.screen_height - 60
        
        mode_color = self.GREEN if armed_status else self.YELLOW
        mode_text = self.font_medium.render(f"MODE: {flight_mode}", True, mode_color)
        screen.blit(mode_text, (x, y))
        
        armed_text = "ARMED" if armed_status else "DISARMED"
        armed_color = self.RED if armed_status else self.GRAY
        armed_display = self.font_small.render(armed_text, True, armed_color)
        screen.blit(armed_display, (x + 150, y + 5))
        
    def draw_mission_info(self, screen, mission_name, targets_remaining, time_left):
        """Draw mission information"""
        x = 20
        y = self.screen_height - 120
        
        mission_text = self.font_medium.render(f"Mission: {mission_name}", True, self.WHITE)
        screen.blit(mission_text, (x, y))
        
        targets_text = self.font_small.render(f"Checkpoints: {targets_remaining}", True, self.WHITE)
        screen.blit(targets_text, (x, y + 25))
        
        time_color = self.RED if time_left < 10 else self.WHITE
        time_text = self.font_small.render(f"Time: {time_left:.1f}s", True, time_color)
        screen.blit(time_text, (x, y + 45))
    
    def draw_complete_hud(self, screen, drone_data):
        """Draw complete HUD"""
        heading = drone_data.get('heading', 0)
        pitch = drone_data.get('pitch', 0)
        roll = drone_data.get('roll', 0)
        speed = drone_data.get('speed', 0)
        max_speed = drone_data.get('max_speed', 180)
        altitude = drone_data.get('altitude', 0)
        battery = drone_data.get('battery', 100)
        voltage = drone_data.get('voltage', None)
        current_range = drone_data.get('range', 0)
        max_range = drone_data.get('max_range', 5)
        flight_mode = drone_data.get('flight_mode', 'FPV')
        armed = drone_data.get('armed', False)
        mission_name = drone_data.get('mission_name', 'Training')
        targets_remaining = drone_data.get('targets_remaining', 0)
        time_left = drone_data.get('time_left', 0)
        
        # Draw all HUD elements
        self.draw_crosshair(screen)
        self.draw_compass(screen, heading)
        self.draw_artificial_horizon(screen, pitch, roll)
        self.draw_speed_indicator(screen, speed, max_speed)
        self.draw_altitude_indicator(screen, altitude)
        self.draw_battery_indicator(screen, battery, voltage)
        self.draw_range_indicator(screen, current_range, max_range)
        self.draw_flight_mode_indicator(screen, flight_mode, armed)
        self.draw_mission_info(screen, mission_name, targets_remaining, time_left)

def integrate_hud_with_drone(drone, hud_system, screen, mission_data=None):
    """Integration function with optional mission data"""
    
    # Default mission data if none provided
    if mission_data is None:
        mission_data = {
            'mission_name': 'Training Flight',
            'targets_remaining': 0,
            'time_left': 0.0
        }
    
    drone_data = {
        'heading': drone.rotation.y % 360,
        'pitch': drone.rotation.x,
        'roll': drone.rotation.z,
        'speed': drone.get_speed_kmh(),
        'max_speed': drone.max_speed_kmh,
        'altitude': max(0, 600 - drone.position.y),
        'battery': drone.battery,
        'voltage': 3.7 * (drone.battery / 100),
        'range': drone.get_range_from_start_km(),
        'max_range': drone.max_range_km,
        'flight_mode': 'FPV' if not drone.crashed else 'CRASH',
        'armed': not drone.crashed,
        'mission_name': mission_data.get('mission_name', 'Training Flight'),
        'targets_remaining': mission_data.get('targets_remaining', 0),
        'time_left': mission_data.get('time_left', 0.0)
    }
    
    hud_system.draw_complete_hud(screen, drone_data)
    