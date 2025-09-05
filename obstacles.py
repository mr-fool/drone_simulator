from vector3 import Vector3
import math
import pygame
import random

class Obstacle:
    def __init__(self, x, y, z, width, height, depth, obstacle_type="building"):
        self.position = Vector3(x, y, z)
        self.width = width
        self.height = height  
        self.depth = depth
        self.obstacle_type = obstacle_type
        self.color = self.get_color_by_type()
        
    def get_color_by_type(self):
        """Get color based on obstacle type"""
        colors = {
            "building": (139, 69, 19),     # Brown
            "skyscraper": (105, 105, 105), # Gray
            "tree": (34, 139, 34),         # Forest green
            "pine": (0, 100, 0),           # Dark green
            "tower": (169, 169, 169),      # Light gray
            "warehouse": (160, 82, 45),    # Saddle brown
        }
        return colors.get(self.obstacle_type, (139, 69, 19))
        
    def check_collision(self, drone):
        """Check if drone collides with this obstacle"""
        dx = abs(drone.position.x - self.position.x)
        dy = abs(drone.position.y - self.position.y)
        dz = abs(drone.position.z - self.position.z)
        
        return (dx < (self.width/2 + drone.size/2) and 
                dy < (self.height/2 + drone.size/2) and
                dz < (self.depth/2 + drone.size/2))

class Target:
    def __init__(self, x, y, z, radius=15, target_type="checkpoint"):
        self.position = Vector3(x, y, z)
        self.radius = radius
        self.collected = False
        self.target_type = target_type
        self.color = self.get_color_by_type()
        
    def get_color_by_type(self):
        """Get color based on target type"""
        colors = {
            "checkpoint": (0, 255, 0),     # Green
            "gate": (255, 215, 0),         # Gold
            "ring": (0, 191, 255),         # Deep sky blue
            "beacon": (255, 165, 0),       # Orange
        }
        return colors.get(self.target_type, (0, 255, 0))
        
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

class EnvironmentGenerator:
    """Generate different types of racing environments"""
    
    @staticmethod
    def create_building_course():
        """Urban racing course with buildings and skyscrapers"""
        obstacles = [
            # Downtown skyscrapers
            Obstacle(200, 300, 50, 40, 200, 40, "skyscraper"),
            Obstacle(300, 250, -30, 35, 180, 35, "building"),
            Obstacle(450, 350, 40, 45, 220, 40, "skyscraper"),
            Obstacle(600, 280, -20, 38, 190, 38, "building"),
            Obstacle(750, 320, 60, 42, 210, 42, "tower"),
            
            # Medium buildings for variety
            Obstacle(150, 400, 20, 30, 120, 30, "warehouse"),
            Obstacle(400, 450, -50, 32, 140, 32, "building"),
            Obstacle(650, 200, 30, 35, 160, 35, "warehouse"),
            Obstacle(850, 380, -40, 40, 180, 40, "building"),
        ]
        
        targets = [
            # Urban checkpoint gates
            Target(120, 200, 10, 18, "gate"),
            Target(280, 180, -10, 18, "checkpoint"),
            Target(480, 200, 20, 18, "gate"),
            Target(680, 160, -15, 18, "checkpoint"),
            Target(820, 190, 25, 18, "gate"),
            Target(950, 180, 0, 18, "checkpoint"),
        ]
        
        return obstacles, targets, "Urban Racing Circuit"
    
    @staticmethod
    def create_forest_course():
        """Natural forest course with trees and organic obstacles"""
        obstacles = [
            # Large tree clusters
            Obstacle(180, 450, 30, 25, 80, 25, "tree"),
            Obstacle(220, 420, 50, 28, 90, 28, "pine"),
            Obstacle(280, 380, 20, 22, 75, 22, "tree"),
            
            Obstacle(420, 400, -40, 30, 95, 30, "pine"),
            Obstacle(480, 430, -20, 26, 85, 26, "tree"),
            Obstacle(520, 390, -60, 24, 78, 24, "pine"),
            
            Obstacle(680, 420, 45, 32, 100, 32, "tree"),
            Obstacle(720, 390, 25, 28, 88, 28, "pine"),
            Obstacle(760, 450, 65, 25, 82, 25, "tree"),
            
            # Scattered individual trees
            Obstacle(350, 350, 10, 18, 65, 18, "pine"),
            Obstacle(550, 320, -30, 20, 70, 20, "tree"),
            Obstacle(800, 340, 15, 19, 68, 19, "pine"),
        ]
        
        targets = [
            # Natural forest rings between trees
            Target(140, 250, 20, 16, "ring"),
            Target(310, 200, -5, 16, "beacon"),
            Target(450, 220, 15, 16, "ring"),
            Target(620, 180, -25, 16, "beacon"),
            Target(780, 200, 35, 16, "ring"),
            Target(920, 190, 5, 16, "beacon"),
        ]
        
        return obstacles, targets, "Forest Slalom Course"
    
    @staticmethod
    def create_hybrid_course():
        """Mixed environment with buildings and natural obstacles"""
        obstacles = [
            # Urban section
            Obstacle(150, 300, 40, 35, 160, 35, "building"),
            Obstacle(280, 320, -20, 40, 180, 40, "skyscraper"),
            
            # Transition area with scattered elements
            Obstacle(420, 380, 30, 25, 90, 25, "tree"),
            Obstacle(480, 350, 50, 38, 170, 38, "tower"),
            Obstacle(520, 400, 10, 22, 75, 22, "pine"),
            
            # Mixed zone
            Obstacle(650, 300, -40, 32, 150, 32, "warehouse"),
            Obstacle(720, 420, 20, 28, 85, 28, "tree"),
            Obstacle(800, 280, 60, 42, 190, 42, "building"),
            
            # Natural ending
            Obstacle(900, 390, -30, 26, 80, 26, "pine"),
        ]
        
        targets = [
            # Varied checkpoint types
            Target(100, 200, 25, 17, "gate"),
            Target(240, 180, -10, 17, "checkpoint"),
            Target(450, 200, 35, 17, "ring"),
            Target(620, 170, -15, 17, "beacon"),
            Target(750, 190, 40, 17, "gate"),
            Target(950, 180, 10, 17, "ring"),
        ]
        
        return obstacles, targets, "Urban-Nature Hybrid Track"

class ObstacleRenderer:
    """Enhanced rendering system for different obstacle types"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def project_3d_to_2d(self, pos):
        """Convert 3D position to 2D screen coordinates with improved projection"""
        # Enhanced isometric projection with better depth perception
        screen_x = self.screen_width // 2 + (pos.x - pos.z * 0.5) * 0.8
        screen_y = self.screen_height // 2 + (pos.y + (pos.x + pos.z) * 0.2) * 0.6
        return int(screen_x), int(screen_y)
    
    def draw_building(self, screen, obstacle, pos_2d):
        """Draw building-type obstacles with 3D effect"""
        if obstacle.obstacle_type == "skyscraper":
            # Tall, narrow skyscraper
            width_2d = int(obstacle.width * 0.6)
            height_2d = int(obstacle.height * 0.8)
            
            # Main building body
            building_rect = pygame.Rect(
                pos_2d[0] - width_2d//2, 
                pos_2d[1] - height_2d//2,
                width_2d, 
                height_2d
            )
            pygame.draw.rect(screen, obstacle.color, building_rect)
            
            # 3D depth effect
            depth_offset = 12
            depth_points = [
                (pos_2d[0] + width_2d//2, pos_2d[1] - height_2d//2),
                (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] - height_2d//2 - depth_offset),
                (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] + height_2d//2 - depth_offset),
                (pos_2d[0] + width_2d//2, pos_2d[1] + height_2d//2)
            ]
            dark_color = (obstacle.color[0]//3, obstacle.color[1]//3, obstacle.color[2]//3)
            pygame.draw.polygon(screen, dark_color, depth_points)
            
            # Top face
            top_points = [
                (pos_2d[0] - width_2d//2, pos_2d[1] - height_2d//2),
                (pos_2d[0] + width_2d//2, pos_2d[1] - height_2d//2),
                (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] - height_2d//2 - depth_offset),
                (pos_2d[0] - width_2d//2 + depth_offset, pos_2d[1] - height_2d//2 - depth_offset)
            ]
            light_color = tuple(min(255, c + 40) for c in obstacle.color)
            pygame.draw.polygon(screen, light_color, top_points)
            
            # Windows for skyscrapers
            for floor in range(3, height_2d - 10, 20):
                for window_x in range(width_2d//4, width_2d - width_2d//4, width_2d//3):
                    window_rect = pygame.Rect(
                        pos_2d[0] - width_2d//2 + window_x,
                        pos_2d[1] - height_2d//2 + floor,
                        6, 8
                    )
                    pygame.draw.rect(screen, (135, 206, 235), window_rect)  # Sky blue windows
                    
        else:  # Regular building, warehouse, tower
            width_2d = int(obstacle.width * 0.7)
            height_2d = int(obstacle.height * 0.7)
            
            # Main building
            pygame.draw.rect(screen, obstacle.color,
                           (pos_2d[0] - width_2d//2, pos_2d[1] - height_2d//2,
                            width_2d, height_2d))
            
            # 3D effect
            depth_offset = 8
            depth_points = [
                (pos_2d[0] + width_2d//2, pos_2d[1] - height_2d//2),
                (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] - height_2d//2 - depth_offset),
                (pos_2d[0] + width_2d//2 + depth_offset, pos_2d[1] + height_2d//2 - depth_offset),
                (pos_2d[0] + width_2d//2, pos_2d[1] + height_2d//2)
            ]
            dark_color = (obstacle.color[0]//2, obstacle.color[1]//2, obstacle.color[2]//2)
            pygame.draw.polygon(screen, dark_color, depth_points)
    
    def draw_tree(self, screen, obstacle, pos_2d):
        """Draw tree-type obstacles with natural appearance"""
        if obstacle.obstacle_type == "pine":
            # Pine tree - triangular shape
            width_2d = int(obstacle.width * 0.8)
            height_2d = int(obstacle.height * 0.9)
            
            # Tree trunk
            trunk_width = width_2d // 4
            trunk_height = height_2d // 3
            trunk_color = (101, 67, 33)  # Brown
            pygame.draw.rect(screen, trunk_color,
                           (pos_2d[0] - trunk_width//2, 
                            pos_2d[1] + height_2d//2 - trunk_height,
                            trunk_width, trunk_height))
            
            # Pine needles - layered triangles
            for layer in range(3):
                triangle_width = width_2d - (layer * 8)
                triangle_height = height_2d // 3
                triangle_y = pos_2d[1] + height_2d//2 - trunk_height - (layer * triangle_height//2)
                
                triangle_points = [
                    (pos_2d[0], triangle_y - triangle_height),
                    (pos_2d[0] - triangle_width//2, triangle_y),
                    (pos_2d[0] + triangle_width//2, triangle_y)
                ]
                pygame.draw.polygon(screen, obstacle.color, triangle_points)
                
        else:  # Regular tree
            # Deciduous tree - circular crown
            width_2d = int(obstacle.width * 0.9)
            height_2d = int(obstacle.height * 0.9)
            
            # Tree trunk
            trunk_width = width_2d // 3
            trunk_height = height_2d // 2
            trunk_color = (101, 67, 33)  # Brown
            pygame.draw.rect(screen, trunk_color,
                           (pos_2d[0] - trunk_width//2, 
                            pos_2d[1] + height_2d//4,
                            trunk_width, trunk_height))
            
            # Tree crown - multiple overlapping circles for fuller look
            crown_radius = width_2d // 2
            pygame.draw.circle(screen, obstacle.color, 
                             (pos_2d[0], pos_2d[1] - height_2d//4), crown_radius)
            
            # Additional smaller circles for texture
            for i in range(3):
                offset_x = (i - 1) * crown_radius // 3
                offset_y = (i - 1) * crown_radius // 4
                smaller_radius = crown_radius // 2
                darker_green = (obstacle.color[0] - 20, obstacle.color[1] - 10, obstacle.color[2] - 20)
                pygame.draw.circle(screen, darker_green,
                                 (pos_2d[0] + offset_x, pos_2d[1] - height_2d//4 + offset_y),
                                 smaller_radius)
    
    def draw_target(self, screen, target, pos_2d):
        """Draw enhanced targets with type-specific appearance"""
        if target.target_type == "gate":
            # Racing gate with posts
            gate_width = target.radius * 3
            gate_height = target.radius * 4
            post_width = 8
            
            # Left post
            pygame.draw.rect(screen, (255, 215, 0),  # Gold
                           (pos_2d[0] - gate_width//2 - post_width//2, 
                            pos_2d[1] - gate_height//2,
                            post_width, gate_height))
            
            # Right post  
            pygame.draw.rect(screen, (255, 215, 0),
                           (pos_2d[0] + gate_width//2 - post_width//2, 
                            pos_2d[1] - gate_height//2,
                            post_width, gate_height))
            
            # Top bar
            pygame.draw.rect(screen, (255, 215, 0),
                           (pos_2d[0] - gate_width//2, 
                            pos_2d[1] - gate_height//2,
                            gate_width, post_width))
            
            # Checkpoint indicator in center
            pygame.draw.circle(screen, target.color, pos_2d, target.radius//2)
            
        elif target.target_type == "ring":
            # Floating ring checkpoint
            outer_radius = target.radius + 8
            pygame.draw.circle(screen, (100, 100, 100), pos_2d, outer_radius, 4)
            pygame.draw.circle(screen, target.color, pos_2d, target.radius, 3)
            
        elif target.target_type == "beacon":
            # Pulsing beacon
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 0.3 + 1.0
            beacon_radius = int(target.radius * pulse)
            
            # Outer glow
            for i in range(3):
                glow_radius = beacon_radius + (3 - i) * 6
                alpha = 50 // (i + 1)
                glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*target.color, alpha), 
                                 (glow_radius, glow_radius), glow_radius)
                screen.blit(glow_surface, (pos_2d[0] - glow_radius, pos_2d[1] - glow_radius))
            
            # Core beacon
            pygame.draw.circle(screen, target.color, pos_2d, target.radius)
            
        else:  # Standard checkpoint
            # Animated checkpoint
            pulse = math.sin(pygame.time.get_ticks() * 0.008) * 0.2 + 1.0
            outer_radius = int(target.radius * pulse)
            
            pygame.draw.circle(screen, (0, 255, 0, 100), pos_2d, outer_radius, 3)
            pygame.draw.circle(screen, target.color, pos_2d, target.radius)
            pygame.draw.circle(screen, (255, 255, 255), pos_2d, target.radius, 2)