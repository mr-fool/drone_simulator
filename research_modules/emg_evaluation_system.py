import pygame
import numpy as np
import time
import csv
from collections import deque
import math

class EMGEvaluationSystem:
    """
    EMG signal quality evaluation for BioAmp EXG Pill research.
    Monitors signal quality, calibration, and control performance.
    """
    
    def __init__(self):
        # Signal storage for analysis
        self.signal_history = {
            'throttle': deque(maxlen=1000),
            'yaw': deque(maxlen=1000),
            'pitch': deque(maxlen=1000),
            'roll': deque(maxlen=1000)
        }
        
        # Baseline values (set during calibration)
        self.baseline = {'throttle': 0, 'yaw': 0, 'pitch': 0, 'roll': 0}
        self.max_values = {'throttle': 100, 'yaw': 100, 'pitch': 100, 'roll': 100}
        
        # Signal quality metrics
        self.snr_values = {'throttle': 0, 'yaw': 0, 'pitch': 0, 'roll': 0}
        self.crosstalk_matrix = np.zeros((4, 4))  # Inter-channel interference
        
        # Performance tracking
        self.calibration_complete = False
        self.session_start_time = time.time()
        self.emg_log_file = None
        
        # Evaluation criteria
        self.evaluation_results = {
            'signal_quality': 'Unknown',
            'control_accuracy': 0.0,
            'response_latency': 0.0,
            'fatigue_level': 0.0,
            'overall_score': 0.0
        }
        
        # Colors for UI
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        self.RED = (255, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (0, 150, 255)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
    
    def initialize_logging(self, session_id=None):
        """Initialize EMG data logging for research analysis"""
        if session_id is None:
            session_id = time.strftime("%Y%m%d_%H%M%S")
        
        filename = f"emg_evaluation_{session_id}.csv"
        self.emg_log_file = open(filename, 'w', newline='')
        writer = csv.writer(self.emg_log_file)
        
        # Write header
        writer.writerow([
            'timestamp', 'throttle_raw', 'yaw_raw', 'pitch_raw', 'roll_raw',
            'throttle_processed', 'yaw_processed', 'pitch_processed', 'roll_processed',
            'snr_throttle', 'snr_yaw', 'snr_pitch', 'snr_roll',
            'control_accuracy', 'response_latency', 'fatigue_indicator'
        ])
        
        print(f"EMG evaluation logging started: {filename}")
    
    def update_emg_signals(self, raw_signals):
        """
        Update EMG signals and perform real-time analysis
        raw_signals: [throttle, yaw, pitch, roll] from Arduino
        """
        channels = ['throttle', 'yaw', 'pitch', 'roll']
        
        for i, channel in enumerate(channels):
            if i < len(raw_signals):
                self.signal_history[channel].append(raw_signals[i])
        
        # Calculate real-time metrics
        self.calculate_snr()
        self.calculate_crosstalk()
        
        # Log data if logging is enabled
        if self.emg_log_file:
            self.log_emg_data(raw_signals)
    
    def calculate_snr(self):
        """Calculate Signal-to-Noise Ratio for each channel"""
        for channel in ['throttle', 'yaw', 'pitch', 'roll']:
            if len(self.signal_history[channel]) > 100:
                signals = list(self.signal_history[channel])
                
                # Signal power (variance of muscle activation periods)
                signal_power = np.var(signals)
                
                # Noise power (variance during rest periods)
                # Approximate rest periods as values near baseline
                rest_threshold = self.baseline[channel] + 10
                rest_values = [s for s in signals if s < rest_threshold]
                
                if len(rest_values) > 10:
                    noise_power = np.var(rest_values)
                    if noise_power > 0:
                        snr_linear = signal_power / noise_power
                        self.snr_values[channel] = 10 * math.log10(snr_linear) if snr_linear > 0 else 0
                    else:
                        self.snr_values[channel] = 50  # Very clean signal
                else:
                    self.snr_values[channel] = 0
    
    def calculate_crosstalk(self):
        """Calculate cross-talk between EMG channels"""
        channels = ['throttle', 'yaw', 'pitch', 'roll']
        
        if all(len(self.signal_history[ch]) > 50 for ch in channels):
            # Create correlation matrix
            data_matrix = np.array([
                list(self.signal_history[ch])[-50:] for ch in channels
            ])
            
            correlation_matrix = np.corrcoef(data_matrix)
            
            # Extract off-diagonal elements as crosstalk
            for i in range(4):
                for j in range(4):
                    if i != j:
                        self.crosstalk_matrix[i][j] = abs(correlation_matrix[i][j]) * 100
    
    def calibrate_baseline(self, duration_seconds=10):
        """
        Perform baseline calibration - user should be at rest
        Returns True when calibration is complete
        """
        channels = ['throttle', 'yaw', 'pitch', 'roll']
        
        # Collect baseline data
        if all(len(self.signal_history[ch]) > duration_seconds * 10 for ch in channels):
            for channel in channels:
                recent_values = list(self.signal_history[channel])[-100:]
                self.baseline[channel] = np.mean(recent_values)
            
            self.calibration_complete = True
            print("EMG Baseline calibration complete:")
            for channel in channels:
                print(f"  {channel}: {self.baseline[channel]:.1f}")
            return True
        
        return False
    
    def calibrate_maximum(self, channel, duration_seconds=5):
        """
        Calibrate maximum voluntary contraction for specific channel
        User should perform maximum contraction during this period
        """
        if len(self.signal_history[channel]) > duration_seconds * 10:
            recent_values = list(self.signal_history[channel])[-50:]
            self.max_values[channel] = max(recent_values)
            print(f"Maximum calibration for {channel}: {self.max_values[channel]:.1f}")
    
    def evaluate_signal_quality(self):
        """Evaluate overall EMG signal quality"""
        if not self.calibration_complete:
            return "Not Calibrated"
        
        # Check SNR for all channels
        min_snr = min(self.snr_values.values())
        avg_snr = np.mean(list(self.snr_values.values()))
        
        # Check crosstalk
        max_crosstalk = np.max(self.crosstalk_matrix)
        
        if min_snr > 20 and max_crosstalk < 15:
            return "Excellent"
        elif min_snr > 15 and max_crosstalk < 25:
            return "Good" 
        elif min_snr > 10 and max_crosstalk < 35:
            return "Fair"
        else:
            return "Poor"
    
    def calculate_control_accuracy(self, intended_controls, actual_drone_response):
        """
        Calculate control accuracy by comparing intended vs actual response
        intended_controls: [throttle, yaw, pitch, roll] (0-1 range)
        actual_drone_response: drone velocity/rotation changes
        """
        # Simplified accuracy calculation
        control_error = 0
        for i, intended in enumerate(intended_controls):
            if intended > 0.1:  # Only evaluate when significant control input
                # This would need more sophisticated implementation
                # based on your specific drone response characteristics
                control_error += abs(intended - 0.5)  # Placeholder calculation
        
        accuracy = max(0, 100 - (control_error * 100))
        self.evaluation_results['control_accuracy'] = accuracy
        return accuracy
    
    def detect_fatigue(self):
        """Detect muscle fatigue based on signal characteristics"""
        channels = ['throttle', 'yaw', 'pitch', 'roll']
        fatigue_indicators = []
        
        for channel in channels:
            if len(self.signal_history[channel]) > 500:
                # Compare recent performance to earlier performance
                early_signals = list(self.signal_history[channel])[:250]
                recent_signals = list(self.signal_history[channel])[-250:]
                
                early_power = np.var(early_signals)
                recent_power = np.var(recent_signals)
                
                if early_power > 0:
                    power_ratio = recent_power / early_power
                    fatigue_indicator = max(0, (1 - power_ratio) * 100)
                    fatigue_indicators.append(fatigue_indicator)
        
        if fatigue_indicators:
            avg_fatigue = np.mean(fatigue_indicators)
            self.evaluation_results['fatigue_level'] = avg_fatigue
            return avg_fatigue
        
        return 0
    
    def log_emg_data(self, raw_signals):
        """Log EMG data for offline analysis"""
        if not self.emg_log_file:
            return
        
        timestamp = time.time() - self.session_start_time
        
        # Process signals (apply your existing filtering)
        processed_signals = self.process_signals(raw_signals)
        
        # Get current metrics
        snr_values = [self.snr_values[ch] for ch in ['throttle', 'yaw', 'pitch', 'roll']]
        
        # Write data row
        writer = csv.writer(self.emg_log_file)
        writer.writerow([
            timestamp,
            *raw_signals,
            *processed_signals,
            *snr_values,
            self.evaluation_results['control_accuracy'],
            self.evaluation_results['response_latency'],
            self.evaluation_results['fatigue_level']
        ])
        
        self.emg_log_file.flush()  # Ensure data is written
    
    def process_signals(self, raw_signals):
        """Apply signal processing (placeholder - use your existing filters)"""
        # Apply your existing EMG filtering from drone.py
        processed = []
        for i, signal in enumerate(raw_signals):
            # Subtract baseline
            channel = ['throttle', 'yaw', 'pitch', 'roll'][i]
            baseline_corrected = max(0, signal - self.baseline[channel])
            
            # Normalize to 0-1 range
            if self.max_values[channel] > self.baseline[channel]:
                normalized = baseline_corrected / (self.max_values[channel] - self.baseline[channel])
                normalized = min(1.0, normalized)
            else:
                normalized = 0.0
            
            processed.append(normalized)
        
        return processed
    
    def draw_evaluation_hud(self, screen, x=10, y=10):
        """Draw EMG evaluation HUD overlay"""
        # Background panel
        panel_width = 300
        panel_height = 400
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 180))
        screen.blit(panel_surface, (x, y))
        
        # Title
        title = self.font_large.render("EMG Evaluation", True, self.WHITE)
        screen.blit(title, (x + 10, y + 10))
        
        current_y = y + 45
        
        # Signal Quality
        quality = self.evaluate_signal_quality()
        quality_color = self.GREEN if quality == "Excellent" else self.YELLOW if quality in ["Good", "Fair"] else self.RED
        quality_text = self.font_medium.render(f"Signal Quality: {quality}", True, quality_color)
        screen.blit(quality_text, (x + 10, current_y))
        current_y += 25
        
        # SNR Values
        snr_text = self.font_small.render("Signal-to-Noise Ratio (dB):", True, self.WHITE)
        screen.blit(snr_text, (x + 10, current_y))
        current_y += 20
        
        for channel in ['throttle', 'yaw', 'pitch', 'roll']:
            snr = self.snr_values[channel]
            snr_color = self.GREEN if snr > 20 else self.YELLOW if snr > 15 else self.RED
            snr_display = self.font_small.render(f"  {channel}: {snr:.1f} dB", True, snr_color)
            screen.blit(snr_display, (x + 20, current_y))
            current_y += 18
        
        # Control Accuracy
        accuracy = self.evaluation_results['control_accuracy']
        acc_color = self.GREEN if accuracy > 90 else self.YELLOW if accuracy > 75 else self.RED
        acc_text = self.font_medium.render(f"Control Accuracy: {accuracy:.1f}%", True, acc_color)
        screen.blit(acc_text, (x + 10, current_y))
        current_y += 25
        
        # Fatigue Level
        fatigue = self.evaluation_results['fatigue_level']
        fatigue_color = self.GREEN if fatigue < 20 else self.YELLOW if fatigue < 40 else self.RED
        fatigue_text = self.font_medium.render(f"Fatigue Level: {fatigue:.1f}%", True, fatigue_color)
        screen.blit(fatigue_text, (x + 10, current_y))
        current_y += 25
        
        # Real-time EMG values
        emg_title = self.font_small.render("Real-time EMG:", True, self.WHITE)
        screen.blit(emg_title, (x + 10, current_y))
        current_y += 20
        
        for channel in ['throttle', 'yaw', 'pitch', 'roll']:
            if self.signal_history[channel]:
                current_value = self.signal_history[channel][-1]
                emg_display = self.font_small.render(f"  {channel}: {current_value:.1f}", True, self.BLUE)
                screen.blit(emg_display, (x + 20, current_y))
                current_y += 18
        
        # Calibration status
        cal_status = "Complete" if self.calibration_complete else "Required"
        cal_color = self.GREEN if self.calibration_complete else self.RED
        cal_text = self.font_medium.render(f"Calibration: {cal_status}", True, cal_color)
        screen.blit(cal_text, (x + 10, current_y))
    
    def generate_evaluation_report(self):
        """Generate comprehensive evaluation report"""
        report = {
            'session_duration': time.time() - self.session_start_time,
            'signal_quality': self.evaluate_signal_quality(),
            'snr_values': self.snr_values.copy(),
            'crosstalk_matrix': self.crosstalk_matrix.copy(),
            'control_accuracy': self.evaluation_results['control_accuracy'],
            'fatigue_level': self.evaluation_results['fatigue_level'],
            'calibration_complete': self.calibration_complete,
            'baseline_values': self.baseline.copy(),
            'max_values': self.max_values.copy()
        }
        
        return report
    
    def close_logging(self):
        """Close EMG logging file"""
        if self.emg_log_file:
            self.emg_log_file.close()
            print("EMG evaluation logging stopped")


class EMGCalibrationUI:
    """UI for EMG calibration process"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 150, 255)
        self.RED = (255, 0, 0)
        
        self.calibration_state = "baseline"  # "baseline", "throttle", "yaw", "pitch", "roll", "complete"
        self.countdown_timer = 0
        
    def draw_calibration_screen(self, screen, emg_eval):
        """Draw calibration instruction screen"""
        screen.fill((20, 30, 60))
        
        # Title
        title = self.font_large.render("EMG Calibration - BioAmp EXG Pill", True, self.WHITE)
        title_rect = title.get_rect(center=(self.screen_width//2, 100))
        screen.blit(title, title_rect)
        
        # Instructions based on current state
        if self.calibration_state == "baseline":
            instruction = "BASELINE CALIBRATION"
            detail = "Relax all muscles completely"
            detail2 = "Keep arms at rest for 10 seconds"
            color = self.BLUE
            
        elif self.calibration_state in ["throttle", "yaw", "pitch", "roll"]:
            muscle_map = {
                "throttle": "Forearm Flexor (Wrist Flexion)",
                "yaw": "Forearm Extensor (Wrist Extension)", 
                "pitch": "Bicep Brachii (Elbow Flexion)",
                "roll": "Tricep Brachii (Elbow Extension)"
            }
            instruction = f"{self.calibration_state.upper()} CALIBRATION"
            detail = f"Contract: {muscle_map[self.calibration_state]}"
            detail2 = "Hold maximum contraction for 5 seconds"
            color = self.GREEN
            
        else:  # complete
            instruction = "CALIBRATION COMPLETE"
            detail = "EMG system ready for flight"
            detail2 = "Press SPACE to start simulation"
            color = self.GREEN
        
        # Draw instructions
        inst_text = self.font_large.render(instruction, True, color)
        inst_rect = inst_text.get_rect(center=(self.screen_width//2, 200))
        screen.blit(inst_text, inst_rect)
        
        detail_text = self.font_medium.render(detail, True, self.WHITE)
        detail_rect = detail_text.get_rect(center=(self.screen_width//2, 250))
        screen.blit(detail_text, detail_rect)
        
        detail2_text = self.font_medium.render(detail2, True, self.WHITE)
        detail2_rect = detail2_text.get_rect(center=(self.screen_width//2, 280))
        screen.blit(detail2_text, detail2_rect)
        
        # Countdown timer
        if self.countdown_timer > 0:
            countdown_text = self.font_large.render(f"{self.countdown_timer:.1f}s", True, self.RED)
            countdown_rect = countdown_text.get_rect(center=(self.screen_width//2, 350))
            screen.blit(countdown_text, countdown_rect)
        
        # Current EMG values
        if emg_eval.signal_history['throttle']:
            values_y = 450
            values_text = self.font_small.render("Current EMG Values:", True, self.WHITE)
            screen.blit(values_text, (self.screen_width//2 - 100, values_y))
            
            for i, channel in enumerate(['throttle', 'yaw', 'pitch', 'roll']):
                if emg_eval.signal_history[channel]:
                    value = emg_eval.signal_history[channel][-1]
                    val_text = self.font_small.render(f"{channel}: {value:.1f}", True, self.BLUE)
                    screen.blit(val_text, (self.screen_width//2 - 100 + (i * 100), values_y + 25))
