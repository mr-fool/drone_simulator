from vector3 import Vector3
import math

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