// EMG-Controlled FPV Drone Training Simulator
// BioAmp EXG Pill - 4 Channel EMG Acquisition
// For HardwareX Research Paper - FPV Drone Training Simulator
// 
// Hardware: Arduino Uno R4 + BioAmp EXG Pill
// Single Arm EMG Sensor Configuration:
// A0: Forearm flexor muscles (wrist flexion) -> Throttle
// A1: Forearm extensor muscles (wrist extension) -> Yaw
// A2: Bicep brachii (elbow flexion) -> Pitch
// A3: Tricep brachii (elbow extension) -> Roll
// Output: EMG signals for FPV racing drone control via Serial

#define SAMPLE_RATE 500
#define BAUD_RATE 115200
#define INPUT_PIN_THROTTLE A0  // Forearm flexor (wrist flexion)
#define INPUT_PIN_YAW A1       // Forearm extensor (wrist extension)
#define INPUT_PIN_PITCH A2     // Bicep brachii (elbow flexion)
#define INPUT_PIN_ROLL A3      // Tricep brachii (elbow extension)
#define BUFFER_SIZE 128
#define NOISE_THRESHOLD 25     // Minimum signal to register as intentional

// Circular buffers for envelope detection
int throttle_buffer[BUFFER_SIZE];
int yaw_buffer[BUFFER_SIZE];
int pitch_buffer[BUFFER_SIZE];
int roll_buffer[BUFFER_SIZE];

// Buffer indices
int throttle_index = 0;
int yaw_index = 0;
int pitch_index = 0;
int roll_index = 0;

// Running sums for efficient averaging
float throttle_sum = 0;
float yaw_sum = 0;
float pitch_sum = 0;
float roll_sum = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  
  // Initialize buffers
  for(int i = 0; i < BUFFER_SIZE; i++) {
    throttle_buffer[i] = 0;
    yaw_buffer[i] = 0;
    pitch_buffer[i] = 0;
    roll_buffer[i] = 0;
  }
  
  // Startup message
  Serial.println("EMG FPV Drone Control System Ready");
  Serial.println("Single Arm Configuration - 4 Channel EMG");
  delay(1000);
}

void loop() {
  // Calculate elapsed time for precise sampling
  static unsigned long past = 0;
  unsigned long present = micros();
  unsigned long interval = present - past;
  past = present;

  // Sampling timer
  static long timer = 0;
  timer -= interval;

  // Sample at defined rate
  if(timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    // Read and filter all 4 EMG channels
    int throttle_raw = analogRead(INPUT_PIN_THROTTLE);
    int yaw_raw = analogRead(INPUT_PIN_YAW);
    int pitch_raw = analogRead(INPUT_PIN_PITCH);
    int roll_raw = analogRead(INPUT_PIN_ROLL);

    // Apply EMG filtering
    int throttle_filtered = EMGFilter_Throttle(throttle_raw);
    int yaw_filtered = EMGFilter_Yaw(yaw_raw);
    int pitch_filtered = EMGFilter_Pitch(pitch_raw);
    int roll_filtered = EMGFilter_Roll(roll_raw);

    // Get envelope (signal strength)
    float throttle_envelope = getThrottleEnvelope(abs(throttle_filtered));
    float yaw_envelope = getYawEnvelope(abs(yaw_filtered));
    float pitch_envelope = getPitchEnvelope(abs(pitch_filtered));
    float roll_envelope = getRollEnvelope(abs(roll_filtered));

    // Amplify and apply noise threshold
    throttle_envelope *= 10;
    yaw_envelope *= 10;
    pitch_envelope *= 10;
    roll_envelope *= 10;

    // Apply noise threshold
    if (throttle_envelope < NOISE_THRESHOLD) throttle_envelope = 0;
    if (yaw_envelope < NOISE_THRESHOLD) yaw_envelope = 0;
    if (pitch_envelope < NOISE_THRESHOLD) pitch_envelope = 0;
    if (roll_envelope < NOISE_THRESHOLD) roll_envelope = 0;

    // Send data to FPV drone simulator
    Serial.print(throttle_envelope);
    Serial.print(",");
    Serial.print(yaw_envelope);
    Serial.print(",");
    Serial.print(pitch_envelope);
    Serial.print(",");
    Serial.println(roll_envelope);
  }
}

// Envelope detection for Throttle channel
float getThrottleEnvelope(int abs_emg) {
  throttle_sum -= throttle_buffer[throttle_index];
  throttle_sum += abs_emg;
  throttle_buffer[throttle_index] = abs_emg;
  throttle_index = (throttle_index + 1) % BUFFER_SIZE;
  return (throttle_sum / BUFFER_SIZE) * 2.0;
}

// Envelope detection for Yaw channel
float getYawEnvelope(int abs_emg) {
  yaw_sum -= yaw_buffer[yaw_index];
  yaw_sum += abs_emg;
  yaw_buffer[yaw_index] = abs_emg;
  yaw_index = (yaw_index + 1) % BUFFER_SIZE;
  return (yaw_sum / BUFFER_SIZE) * 2.0;
}

// Envelope detection for Pitch channel
float getPitchEnvelope(int abs_emg) {
  pitch_sum -= pitch_buffer[pitch_index];
  pitch_sum += abs_emg;
  pitch_buffer[pitch_index] = abs_emg;
  pitch_index = (pitch_index + 1) % BUFFER_SIZE;
  return (pitch_sum / BUFFER_SIZE) * 2.0;
}

// Envelope detection for Roll channel
float getRollEnvelope(int abs_emg) {
  roll_sum -= roll_buffer[roll_index];
  roll_sum += abs_emg;
  roll_buffer[roll_index] = abs_emg;
  roll_index = (roll_index + 1) % BUFFER_SIZE;
  return (roll_sum / BUFFER_SIZE) * 2.0;
}

// Band-Pass Butterworth IIR digital filter for Throttle
// Sampling rate: 500.0 Hz, frequency: [74.5, 149.5] Hz
float EMGFilter_Throttle(float input) {
  float output = input;
  {
    static float z1, z2;
    float x = output - 0.05159732*z1 - 0.36347401*z2;
    output = 0.01856301*x + 0.03712602*z1 + 0.01856301*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - -0.53945795*z1 - 0.39764934*z2;
    output = 1.00000000*x + -2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - 0.47319594*z1 - 0.70744137*z2;
    output = 1.00000000*x + 2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  {
    static float z1, z2;
    float x = output - -1.00211112*z1 - 0.74520226*z2;
    output = 1.00000000*x + -2.00000000*z1 + 1.00000000*z2;
    z2 = z1;
    z1 = x;
  }
  return output;
}

// Band-Pass Butterworth IIR digital filter for Yaw
float EMGFilter_Yaw(float input) {
  float output = input;
  {
    static float a1, a2;
    float x = output - 0.05159732*a1 - 0.36347401*a2;
    output = 0.01856301*x + 0.03712602*a1 + 0.01856301*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - -0.53945795*a1 - 0.39764934*a2;
    output = 1.00000000*x + -2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - 0.47319594*a1 - 0.70744137*a2;
    output = 1.00000000*x + 2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  {
    static float a1, a2;
    float x = output - -1.00211112*a1 - 0.74520226*a2;
    output = 1.00000000*x + -2.00000000*a1 + 1.00000000*a2;
    a2 = a1;
    a1 = x;
  }
  return output;
}

// Band-Pass Butterworth IIR digital filter for Pitch
float EMGFilter_Pitch(float input) {
  float output = input;
  {
    static float b1, b2;
    float x = output - 0.05159732*b1 - 0.36347401*b2;
    output = 0.01856301*x + 0.03712602*b1 + 0.01856301*b2;
    b2 = b1;
    b1 = x;
  }
  {
    static float b1, b2;
    float x = output - -0.53945795*b1 - 0.39764934*b2;
    output = 1.00000000*x + -2.00000000*b1 + 1.00000000*b2;
    b2 = b1;
    b1 = x;
  }
  {
    static float b1, b2;
    float x = output - 0.47319594*b1 - 0.70744137*b2;
    output = 1.00000000*x + 2.00000000*b1 + 1.00000000*b2;
    b2 = b1;
    b1 = x;
  }
  {
    static float b1, b2;
    float x = output - -1.00211112*b1 - 0.74520226*b2;
    output = 1.00000000*x + -2.00000000*b1 + 1.00000000*b2;
    b2 = b1;
    b1 = x;
  }
  return output;
}

// Band-Pass Butterworth IIR digital filter for Roll
float EMGFilter_Roll(float input) {
  float output = input;
  {
    static float c1, c2;
    float x = output - 0.05159732*c1 - 0.36347401*c2;
    output = 0.01856301*x + 0.03712602*c1 + 0.01856301*c2;
    c2 = c1;
    c1 = x;
  }
  {
    static float c1, c2;
    float x = output - -0.53945795*c1 - 0.39764934*c2;
    output = 1.00000000*x + -2.00000000*c1 + 1.00000000*c2;
    c2 = c1;
    c1 = x;
  }
  {
    static float c1, c2;
    float x = output - 0.47319594*c1 - 0.70744137*c2;
    output = 1.00000000*x + 2.00000000*c1 + 1.00000000*c2;
    c2 = c1;
    c1 = x;
  }
  {
    static float c1, c2;
    float x = output - -1.00211112*c1 - 0.74520226*c2;
    output = 1.00000000*x + -2.00000000*c1 + 1.00000000*c2;
    c2 = c1;
    c1 = x;
  }
  return output;
}
