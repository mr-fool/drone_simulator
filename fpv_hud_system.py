# Add this to your main.py imports
from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone

# In your FPVSimulator __init__ method, add:
class FPVSimulator:
    def __init__(self):
        # ... existing code ...
        
        # Initialize HUD system
        self.hud_system = FPVHUDSystem(self.WIDTH, self.HEIGHT)
        
        # ... rest of existing code ...

    # Replace your existing draw_hud method with this:
    def draw_hud(self):
        """Draw advanced FPV HUD system"""
        # Use the integrated HUD system
        integrate_hud_with_drone(self.drone, self.hud_system, self.screen)
        
        # Add EMG signal indicators (if in Arduino mode)
        if ARDUINO_MODE:
            self.draw_emg_indicators()
        
        # Add control instructions
        self.draw_control_instructions()
    
    def draw_emg_indicators(self):
        """Draw EMG signal strength indicators"""
        signal_x = self.WIDTH - 250
        signal_y = 150
        
        signal_labels = ["Throttle", "Yaw", "Pitch", "Roll"]
        signal_colors = [self.hud_system.GREEN, self.hud_system.BLUE, 
                        self.hud_system.YELLOW, self.hud_system.ORANGE]
        
        for i, (label, signal, color) in enumerate(zip(signal_labels, emg_signals, signal_colors)):
            # EMG signal bar
            bar_width = 100
            bar_height = 8
            signal_strength = min(100, signal)
            
            # Background bar
            pygame.draw.rect(self.screen, self.hud_system.DARK_GRAY, 
                           (signal_x, signal_y + i * 25, bar_width, bar_height))
            
            # Signal bar
            if signal_strength > 0:
                pygame.draw.rect(self.screen, color, 
                               (signal_x, signal_y + i * 25, int(signal_strength), bar_height))
            
            # Signal label and value
            label_text = self.hud_system.font_tiny.render(f"{label}: {signal:.0f}", True, self.hud_system.WHITE)
            self.screen.blit(label_text, (signal_x + 110, signal_y + i * 25 - 2))
    
    def draw_control_instructions(self):
        """Draw control mode and instructions"""
        control_x = self.WIDTH - 200
        control_y = self.HEIGHT - 100
        
        # Control mode indicator
        control_mode = "EMG CONTROL" if ARDUINO_MODE else "KEYBOARD"
        mode_color = self.hud_system.GREEN if ARDUINO_MODE else self.hud_system.YELLOW
        mode_text = self.hud_system.font_small.render(control_mode, True, mode_color)
        self.screen.blit(mode_text, (control_x, control_y))
        
        if not ARDUINO_MODE:
            # Keyboard controls
            controls = [
                "SPACE: Throttle",
                "WASD: Pitch/Roll", 
                "QE: Yaw",
                "R: Reset",
                "ESC: Config"
            ]
            for i, control in enumerate(controls):
                control_text = self.hud_system.font_tiny.render(control, True, self.hud_system.WHITE)
                self.screen.blit(control_text, (control_x, control_y + 20 + i * 12))

# Complete example of how to modify your existing main.py:

# 1. Add the import at the top:
# from fpv_hud_system import FPVHUDSystem, integrate_hud_with_drone

# 2. In FPVSimulator.__init__, add:
# self.hud_system = FPVHUDSystem(self.WIDTH, self.HEIGHT)

# 3. Replace your draw_hud method with the one above

# 4. In your main game loop, the HUD will now show:
#    - Interactive compass with heading
#    - Artificial horizon with pitch/roll
#    - Vertical speed tape
#    - Vertical altitude tape  
#    - Battery indicator with voltage
#    - Range indicator with warnings
#    - Flight mode and armed status
#    - Signal strength indicator
#    - Center crosshair for targeting
#    - EMG signal bars (when using hardware)

# Example of how the integrated HUD data flows:
"""
Your drone object provides:
- drone.rotation.y → compass heading
- drone.rotation.x → pitch for artificial horizon
- drone.rotation.z → roll for artificial horizon  
- drone.get_speed_kmh() → speed tape
- drone.position.y → altitude calculation
- drone.battery → battery indicator
- drone.get_range_from_start_km() → range indicator
- drone.crashed → flight mode and armed status
"""