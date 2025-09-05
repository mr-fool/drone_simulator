from dataclasses import dataclass
import math

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