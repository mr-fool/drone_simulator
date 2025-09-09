import sys
import os
# Add core_systems to path so we can import Vector3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core_systems'))
                                
from vector3 import Vector3
from config import DebugConfig
import math

class Target:
    """Simple navigation target for EMG research"""
    
    def __init__(self, x, y, z, radius=20, target_type="waypoint"):
        self.position = Vector3(x, y, z)
        self.radius = radius
        self.collected = False
        self.target_type = target_type
        self.color = self.get_color_by_type()
        
    def get_color_by_type(self):
        """Get color based on target type"""
        colors = {
            "waypoint": (0, 255, 0),       # Green - basic navigation
            "checkpoint": (255, 215, 0),   # Gold - research checkpoint  
            "marker": (0, 191, 255),       # Blue - position marker
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

class ResearchScenarioGenerator:
    """Generate simple scenarios for EMG research - no obstacles"""
    
    @staticmethod
    def create_basic_navigation():
        """Basic waypoint navigation for EMG control validation"""
        # No obstacles in research mode
        obstacles = []
        
        # Simple navigation targets (optional based on config)
        if DebugConfig.DISABLE_TARGETS:
            targets = []
        else:
            targets = [
                Target(200, 250, 0, 25, "checkpoint"),
                Target(400, 200, 50, 25, "waypoint"), 
                Target(600, 250, -30, 25, "checkpoint"),
                Target(800, 200, 20, 25, "waypoint")
            ]
        
        return obstacles, targets, "EMG Navigation Research"
    
    @staticmethod 
    def create_altitude_test():
        """Altitude control test for EMG throttle validation"""
        obstacles = []
        
        if DebugConfig.DISABLE_TARGETS:
            targets = []
        else:
            # Vertical navigation targets
            targets = [
                Target(200, 200, 0, 20, "marker"),    # Higher altitude
                Target(400, 350, 0, 20, "marker"),    # Lower altitude  
                Target(600, 150, 0, 20, "marker"),    # High altitude
                Target(800, 300, 0, 20, "marker")     # Medium altitude
            ]
        
        return obstacles, targets, "EMG Altitude Control Test"
    
    @staticmethod
    def create_precision_test():
        """Precision control test with smaller targets"""
        obstacles = []
        
        if DebugConfig.DISABLE_TARGETS:
            targets = []
        else:
            # Smaller, more precise targets
            targets = [
                Target(150, 250, 20, 15, "checkpoint"),
                Target(350, 200, -20, 15, "checkpoint"),
                Target(550, 280, 30, 15, "checkpoint"),
                Target(750, 220, -10, 15, "checkpoint"),
                Target(900, 260, 25, 15, "checkpoint")
            ]
        
        return obstacles, targets, "EMG Precision Control Test"
    
    @staticmethod
    def create_endurance_test():
        """Longer course for muscle fatigue research"""
        obstacles = []
        
        if DebugConfig.DISABLE_TARGETS:
            targets = []
        else:
            # Extended navigation course
            targets = [
                Target(150, 250, 0, 25, "waypoint"),
                Target(300, 200, 40, 25, "waypoint"),
                Target(450, 280, -30, 25, "waypoint"), 
                Target(600, 220, 50, 25, "waypoint"),
                Target(750, 260, -20, 25, "waypoint"),
                Target(900, 200, 30, 25, "waypoint"),
                Target(1050, 250, 0, 25, "checkpoint")  # Final target
            ]
        
        return obstacles, targets, "EMG Endurance Research"

# Simplified renderer for targets only
class ResearchRenderer:
    """Minimal renderer for research targets"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
    
    def draw_target(self, screen, target, projection_func, drone_position, drone_rotation):
        """Draw research target with proper 3D projection"""
        if target.collected:
            return
            
        projection = projection_func(target.position, drone_position, drone_rotation)
        if projection is None:
            return
            
        screen_x, screen_y, depth = projection
        
        # Skip if off-screen
        if (screen_x < -50 or screen_x > self.screen_width + 50 or 
            screen_y < -50 or screen_y > self.screen_height + 50):
            return
        
        # Scale with distance
        base_radius = target.radius
        distance_scale = max(0.3, 100.0 / max(10, depth))
        scaled_radius = int(base_radius * distance_scale)
        scaled_radius = max(5, min(50, scaled_radius))  # Clamp size
        
        # Draw target
        import pygame
        pygame.draw.circle(screen, target.color, (screen_x, screen_y), scaled_radius)
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), scaled_radius, 2)
        
        # Draw center dot for precision
        center_size = max(2, scaled_radius // 4)
        pygame.draw.circle(screen, (255, 255, 255), (screen_x, screen_y), center_size)

# Research scenario mapping
RESEARCH_SCENARIOS = {
    "basic": ResearchScenarioGenerator.create_basic_navigation,
    "altitude": ResearchScenarioGenerator.create_altitude_test,
    "precision": ResearchScenarioGenerator.create_precision_test,
    "endurance": ResearchScenarioGenerator.create_endurance_test
}