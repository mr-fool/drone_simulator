import pygame
import time

class EMGCalibrationUI:
    """UI for EMG calibration process with BioAmp EXG Pill"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 150, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.GRAY = (128, 128, 128)
        
        # Calibration state management
        self.calibration_state = "baseline"  # "baseline", "throttle", "yaw", "pitch", "roll", "complete"
        self.countdown_timer = 0
        self.instruction_start_time = time.time()
        
    def draw_calibration_screen(self, screen, emg_eval):
        """Draw EMG calibration instruction screen"""
        screen.fill((20, 30, 60))  # Dark blue background
        
        # Title
        title = self.font_large.render("EMG Calibration - BioAmp EXG Pill", True, self.WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 80))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_medium.render("Arduino Uno R4 + 4-Channel EMG Acquisition", True, self.YELLOW)
        subtitle_rect = subtitle.get_rect(center=(self.screen_width//2, 110))
        screen.blit(subtitle, subtitle_rect)
        
        # Instructions based on current calibration state
        if self.calibration_state == "baseline":
            self._draw_baseline_instructions(screen, emg_eval)
        elif self.calibration_state in ["throttle", "yaw", "pitch", "roll"]:
            self._draw_muscle_calibration_instructions(screen, emg_eval)
        else:  # complete
            self._draw_completion_screen(screen, emg_eval)
        
        # Current EMG values display
        self._draw_current_emg_values(screen, emg_eval)
        
        # Progress indicator
        self._draw_progress_indicator(screen)
        
        # Control instructions
        self._draw_control_instructions(screen)
    
    def _draw_baseline_instructions(self, screen, emg_eval):
        """Draw baseline calibration instructions"""
        instruction_y = 180
        
        # Main instruction
        instruction = self.font_large.render("BASELINE CALIBRATION", True, self.BLUE)
        instruction_rect = instruction.get_rect(center=(self.screen_width//2, instruction_y))
        screen.blit(instruction, instruction_rect)
        
        # Detailed instructions
        details = [
            "Relax all muscles completely",
            "Keep your arm at rest on a stable surface",
            "Avoid any muscle contractions",
            "Breathe normally and stay still",
            "This establishes your resting EMG baseline"
        ]
        
        for i, detail in enumerate(details):
            detail_text = self.font_medium.render(detail, True, self.WHITE)
            detail_rect = detail_text.get_rect(center=(self.screen_width//2, instruction_y + 50 + i * 30))
            screen.blit(detail_text, detail_rect)
        
        # Duration indicator
        duration_text = self.font_medium.render("Duration: 10 seconds of complete rest", True, self.GRAY)
        duration_rect = duration_text.get_rect(center=(self.screen_width//2, instruction_y + 220))
        screen.blit(duration_text, duration_rect)
        
        # Start instruction
        start_text = self.font_medium.render("Press 'C' to start baseline calibration", True, self.GREEN)
        start_rect = start_text.get_rect(center=(self.screen_width//2, instruction_y + 260))
        screen.blit(start_text, start_rect)
    
    def _draw_muscle_calibration_instructions(self, screen, emg_eval):
        """Draw muscle-specific calibration instructions"""
        instruction_y = 180
        
        # Muscle mapping for instructions
        muscle_info = {
            "throttle": {
                "muscle": "Forearm Flexor Muscles",
                "action": "Wrist Flexion",
                "description": "Bend your wrist downward (palm toward forearm)",
                "electrode_pos": "Ventral forearm, 1/3 from wrist",
                "function": "Controls drone throttle (vertical movement)"
            },
            "yaw": {
                "muscle": "Forearm Extensor Muscles", 
                "action": "Wrist Extension",
                "description": "Bend your wrist upward (back of hand toward forearm)",
                "electrode_pos": "Dorsal forearm, 1/3 from wrist",
                "function": "Controls drone yaw (rotation left/right)"
            },
            "pitch": {
                "muscle": "Bicep Brachii",
                "action": "Elbow Flexion", 
                "description": "Bend your elbow (bring hand toward shoulder)",
                "electrode_pos": "Anterior upper arm, muscle belly",
                "function": "Controls drone pitch (nose up/down)"
            },
            "roll": {
                "muscle": "Tricep Brachii",
                "action": "Elbow Extension",
                "description": "Straighten your elbow (extend arm)",
                "electrode_pos": "Posterior upper arm, lateral head",
                "function": "Controls drone roll (banking left/right)"
            }
        }
        
        current_muscle = muscle_info[self.calibration_state]
        
        # Main instruction
        instruction = self.font_large.render(f"{self.calibration_state.upper()} CALIBRATION", True, self.GREEN)
        instruction_rect = instruction.get_rect(center=(self.screen_width//2, instruction_y))
        screen.blit(instruction, instruction_rect)
        
        # Muscle information
        muscle_text = self.font_medium.render(f"Muscle: {current_muscle['muscle']}", True, self.WHITE)
        muscle_rect = muscle_text.get_rect(center=(self.screen_width//2, instruction_y + 50))
        screen.blit(muscle_text, muscle_rect)
        
        action_text = self.font_medium.render(f"Action: {current_muscle['action']}", True, self.BLUE)
        action_rect = action_text.get_rect(center=(self.screen_width//2, instruction_y + 80))
        screen.blit(action_text, action_rect)
        
        # Description
        desc_text = self.font_small.render(current_muscle['description'], True, self.YELLOW)
        desc_rect = desc_text.get_rect(center=(self.screen_width//2, instruction_y + 110))
        screen.blit(desc_text, desc_rect)
        
        # Electrode position
        electrode_text = self.font_small.render(f"Electrode Position: {current_muscle['electrode_pos']}", True, self.GRAY)
        electrode_rect = electrode_text.get_rect(center=(self.screen_width//2, instruction_y + 140))
        screen.blit(electrode_text, electrode_rect)
        
        # Function explanation
        function_text = self.font_small.render(f"Function: {current_muscle['function']}", True, self.GRAY)
        function_rect = function_text.get_rect(center=(self.screen_width//2, instruction_y + 170))
        screen.blit(function_text, function_rect)
        
        # Calibration instructions
        calib_instructions = [
            "1. Contract the muscle as hard as you can",
            "2. Hold maximum contraction for 5 seconds", 
            "3. Maintain steady, strong contraction",
            "4. Press 'C' when ready to calibrate"
        ]
        
        for i, instruction in enumerate(calib_instructions):
            inst_text = self.font_small.render(instruction, True, self.WHITE)
            inst_rect = inst_text.get_rect(center=(self.screen_width//2, instruction_y + 210 + i * 25))
            screen.blit(inst_text, inst_rect)
    
    def _draw_completion_screen(self, screen, emg_eval):
        """Draw calibration completion screen"""
        instruction_y = 200
        
        # Completion message
        complete_text = self.font_large.render("CALIBRATION COMPLETE", True, self.GREEN)
        complete_rect = complete_text.get_rect(center=(self.screen_width//2, instruction_y))
        screen.blit(complete_text, complete_rect)
        
        # Status message
        status_text = self.font_medium.render("EMG system ready for flight control", True, self.WHITE)
        status_rect = status_text.get_rect(center=(self.screen_width//2, instruction_y + 50))
        screen.blit(status_text, status_rect)
        
        # Calibration summary
        summary_y = instruction_y + 100
        summary_title = self.font_medium.render("Calibration Summary:", True, self.YELLOW)
        summary_rect = summary_title.get_rect(center=(self.screen_width//2, summary_y))
        screen.blit(summary_title, summary_rect)
        
        # Show baseline values
        if hasattr(emg_eval, 'baseline'):
            channels = ['throttle', 'yaw', 'pitch', 'roll']
            for i, channel in enumerate(channels):
                baseline_val = emg_eval.baseline.get(channel, 0)
                max_val = emg_eval.max_values.get(channel, 100)
                summary_line = f"{channel.title()}: Baseline {baseline_val:.1f}, Max {max_val:.1f}"
                summary_text = self.font_small.render(summary_line, True, self.WHITE)
                summary_text_rect = summary_text.get_rect(center=(self.screen_width//2, summary_y + 40 + i * 25))
                screen.blit(summary_text, summary_text_rect)
        
        # Start flight instruction
        start_text = self.font_medium.render("Press SPACE to start flight simulation", True, self.GREEN)
        start_rect = start_text.get_rect(center=(self.screen_width//2, instruction_y + 250))
        screen.blit(start_text, start_rect)
    
    def _draw_current_emg_values(self, screen, emg_eval):
        """Draw real-time EMG values during calibration"""
        values_y = 450
        
        # Title
        values_title = self.font_medium.render("Real-time EMG Values", True, self.WHITE)
        values_rect = values_title.get_rect(center=(self.screen_width//2, values_y))
        screen.blit(values_title, values_rect)
        
        # Channel values
        channels = ['throttle', 'yaw', 'pitch', 'roll']
        channel_labels = ['Throttle (A0)', 'Yaw (A1)', 'Pitch (A2)', 'Roll (A3)']
        
        for i, (channel, label) in enumerate(zip(channels, channel_labels)):
            if hasattr(emg_eval, 'signal_history') and emg_eval.signal_history[channel]:
                current_value = emg_eval.signal_history[channel][-1]
                
                # Determine color based on signal strength
                if current_value > 50:
                    color = self.GREEN
                elif current_value > 25:
                    color = self.YELLOW
                else:
                    color = self.WHITE
                
                value_text = self.font_small.render(f"{label}: {current_value:.1f}", True, color)
                
                # Position in 2x2 grid
                x_offset = -100 if i % 2 == 0 else 100
                y_offset = 30 if i < 2 else 60
                
                value_rect = value_text.get_rect(center=(self.screen_width//2 + x_offset, values_y + y_offset))
                screen.blit(value_text, value_rect)
    
    def _draw_progress_indicator(self, screen):
        """Draw calibration progress indicator"""
        progress_y = 600
        
        # Progress bar background
        bar_width = 400
        bar_height = 20
        bar_x = (self.screen_width - bar_width) // 2
        
        pygame.draw.rect(screen, self.GRAY, (bar_x, progress_y, bar_width, bar_height))
        
        # Progress fill
        states = ["baseline", "throttle", "yaw", "pitch", "roll", "complete"]
        current_progress = states.index(self.calibration_state) if self.calibration_state in states else 0
        progress_width = int((current_progress / (len(states) - 1)) * bar_width)
        
        if progress_width > 0:
            pygame.draw.rect(screen, self.GREEN, (bar_x, progress_y, progress_width, bar_height))
        
        # Progress text
        progress_text = f"Step {current_progress + 1} of {len(states)}: {self.calibration_state.title()}"
        progress_display = self.font_small.render(progress_text, True, self.WHITE)
        progress_rect = progress_display.get_rect(center=(self.screen_width//2, progress_y - 15))
        screen.blit(progress_display, progress_rect)
    
    def _draw_control_instructions(self, screen):
        """Draw control instructions at bottom of screen"""
        controls_y = 650
        
        if self.calibration_state == "complete":
            control_text = "SPACE = Start Flight | ESC = Return to Config"
        else:
            control_text = "C = Continue Calibration | ESC = Return to Config"
        
        controls_display = self.font_small.render(control_text, True, self.GRAY)
        controls_rect = controls_display.get_rect(center=(self.screen_width//2, controls_y))
        screen.blit(controls_display, controls_rect)
        
        # Hardware reminder
        hardware_text = "Ensure BioAmp EXG Pill is connected and electrodes are properly placed"
        hardware_display = self.font_small.render(hardware_text, True, self.GRAY)
        hardware_rect = hardware_display.get_rect(center=(self.screen_width//2, controls_y + 20))
        screen.blit(hardware_display, hardware_rect)