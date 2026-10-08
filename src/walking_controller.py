from adafruit_servokit import ServoKit
from mpu6050 import mpu6050
import RPi.GPIO as GPIO
import time
import math
# --- HARDWARE INITIALIZATION ---
kit = ServoKit(channels=16)
try:
  imu = mpu6050(0x68)
except Exception as e:
  print("IMU not found at 0x68. Check wiring!")
# GPIO Setup for Ultrasonic
TRIG_PIN = 23
ECHO_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
# --- CONFIGURATION & CALIBRATION ---
# Replace with your perfect stand values
STAND = {
  "L_HIP_R": 70, "L_HIP_P": 60, "L_KNEE": 110, "L_ANK_P": 80, "L_ANK_R":70,
  "R_HIP_R": 70, "R_HIP_P": 80, "R_KNEE": 40, "R_ANK_P": 50, "R_ANK_R":70,
  "L_SH_R": 90, "R_SH_R": 90
}
PINS = {
  "L_HIP_R": 0, "L_HIP_P": 1, "L_KNEE": 2, "L_ANK_P": 3, "L_ANK_R": 4,
  "R_HIP_R": 10, "R_HIP_P": 11, "R_KNEE": 13, "R_ANK_P": 14, "R_ANK_R":15,
  "L_SH_R": 5, "R_SH_R": 8
}
# IMU Calibration Offset (Based on your -110.5 degree neutral reading)
IMU_OFFSET = 110.5
# --- SENSOR FUNCTIONS ---
def get_calibrated_roll():
"""Reads the side-to-side tilt and applies the baseline offset."""
  try:
    accel = imu.get_accel_data()
    raw_roll = math.atan2(accel[’y’], accel[’z’]) * 180 / math.pi
    return raw_roll + IMU_OFFSET
  except OSError:
    return 0.0 # Return neutral on occasional I2C read failure
def get_distance():
  """Measures front distance in centimeters using the ultrasonic sensor.
  """
  GPIO.output(TRIG_PIN, True)
  time.sleep(0.00001)
  GPIO.output(TRIG_PIN, False)
  start_time = time.time()
  stop_time = time.time()
  # Save start_time
  while GPIO.input(ECHO_PIN) == 0:
    start_time = time.time()
  # Save time of arrival
  while GPIO.input(ECHO_PIN) == 1:
    stop_time = time.time()
  # Time difference between start and arrival
  time_elapsed = stop_time - start_time
  # Sonic speed (34300 cm/s) formula
  distance = (time_elapsed * 34300) / 2
  return distance
# --- ACTUATION FUNCTIONS ---
def set_angle(ch, angle):
  try:
    angle = max(0, min(180, angle))
    kit.servo[ch].angle = angle
except OSError:
    pass # Ignore minor I2C jitters
def stand_pose():
  for part, angle in STAND.items():
    set_angle(PINS[part], angle)
def imu_lean_left(target_roll=15.0):
    """Dynamically moves ankles until the IMU registers the target left
  tilt."""
  current_l_ank = STAND["L_ANK_R"]
  current_r_ank = STAND["R_ANK_R"]
  print("Leaning Left...")
  for _ in range(25): # Loop limit prevents runaway movements
    if get_calibrated_roll() >= target_roll:
      print("Target tilt achieved.")
      break
    current_l_ank += 1
    current_r_ank += 1
    set_angle(PINS["L_ANK_R"], current_l_ank)
    set_angle(PINS["R_ANK_R"], current_r_ank)
    time.sleep(0.04)
# --- MAIN LOOP ---
def autonomous_walk():
  try:
    print("Stabilizing Standing Pose...")
    stand_pose()
    time.sleep(2)
    while True:
      # 1. OBSTACLE CHECK
      dist = get_distance()
      print(f"Obstacle Distance: {dist:.1f} cm")
      if dist < 25.0: # Stop if an object is within 25 cm
        print("Obstacle too close! Pausing walk cycle...")
        stand_pose()
        time.sleep(0.5)
        continue # Skip the walking step and re-evaluate
      # 2. CLOSED-LOOP WEIGHT SHIFT
      # Pushes weight completely over the left leg using real-time
      IMU feedback
      imu_lean_left(target_roll=16.0)
      time.sleep(0.1)
      # 3. VERTICAL STEP LIFT (Clears high-friction leather/cardboard
      )
      set_angle(PINS["R_KNEE"], 65)
      set_angle(PINS["R_ANK_P"], 40)
      time.sleep(0.2)
      # 4. SWING RIGHT LEG FORWARD
      set_angle(PINS["R_HIP_P"], 95)
      time.sleep(0.2)
      # 5. PLANT FOOT
      set_angle(PINS["R_KNEE"], 40)
      set_angle(PINS["R_ANK_P"], 50)
      # 6. RETURN TO CENTER & SETTLE VIBRATIONS
      stand_pose()
      time.sleep(0.6)
  except KeyboardInterrupt:
    print("\nHalting robot. Releasing servo torque.")
    for i in range(16):
      kit.servo[i].angle = None
    GPIO.cleanup()
if __name__ == "__main__":
  autonomous_walk()
