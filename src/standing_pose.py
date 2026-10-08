from adafruit_servokit import ServoKit
import time
kit = ServoKit(channels=16)
def set_angle(ch, angle):
  angle = max(0, min(180, angle)) # safety clamp
  kit.servo[ch].angle = angle
# ---------------------------
# BASE STANDING POSTURE
# ---------------------------
def stand_pose():
  # LEFT LEG
  set_angle(0, 70) # hip side
  set_angle(1, 60) # hip front/back
  set_angle(2, 110) # knee
  set_angle(3, 80) # ankle front/back
  set_angle(4, 70) # ankle side
  # RIGHT LEG
  set_angle(10, 70) # hip side
  set_angle(11, 80) # hip front/back
  set_angle(13, 40) # knee
  set_angle(14, 50) # ankle front/back
  set_angle(15, 70) # ankle side
print("Setting perfect standing posture...")
stand_pose()
time.sleep(2)

