import cv2
import time
import numpy as np
import threading
import os
import speech_recognition as sr
from picamera2 import Picamera2
from groq import Groq
import pvporcupine
from pvrecorder import PvRecorder
# OLED & SERVO
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas
from PIL import Image, ImageDraw
from adafruit_servokit import ServoKit
# ================= CONFIGURATION =================
PICO_KEY = ""
WAKEWORD_PATH = "/home/kiran/Pixel_en_raspberry-pi_v4_0_0.ppn"
GROQ_API_KEY = ""
PIPER_PATH = "/home/kiran/piper/piper"
PIPER_MODEL = "/home/kiran/en_US-ryan-medium.onnx"
client = Groq(api_key=GROQ_API_KEY)
kit = ServoKit(channels=16)
serial_i2c = i2c(port=1, address=0x3C)
oled_device = sh1106(serial_i2c)
PAN_CH, TILT_CH = 5, 4
RIGHT_SHOULDER_ROLL = 2
RIGHT_SHOULDER_PITCH = 1
RIGHT_ELBOW = 0
LEFT_ARM = 13
# State Flags
is_interacting = False
is_speaking = False
is_listening = False
chat_memory = []
# YOLO Setup
net = cv2.dnn.readNet("yolov3-tiny.weights", "yolov3-tiny.cfg")
with open("coco.names", "r") as f:
  classes = [line.strip() for line in f.readlines()]
output_layers = [net.getLayerNames()[i-1] for i in net.
  getUnconnectedOutLayers()]
# Robot Globals
pan_angle, tilt_angle = 90.0, 90.0
target_pan, target_tilt = 90.0, 90.0
smoothing_factor = 0.15
Kp = 0.035
current_emotion = "sleepy"
anim_counter = 0
# ================= OLED FACE MANAGER =================
class FaceManager:
  def __init__(self, device):
    self.device = device
    self.mouth_open = False
  def draw(self):
    global anim_counter
    with canvas(self.device) as draw:
      if is_listening:
        draw.arc((100, 15, 110, 30), start=300, end=60, fill="white")
        draw.arc((105, 10, 118, 35), start=300, end=60, fill="white")
        draw.arc((110, 5, 125, 40), start=300, end=60, fill="white")
      if current_emotion == "sleepy":
        draw.line((30,25,50,25), "white", 3); draw.line((78,25,98,25), "white", 3) z_y = 5 + (anim_counter % 6)
        draw.text((95, z_y), "Z", fill="white")
        draw.text((105, z_y+3), "Z", fill="white")
        draw.text((115, z_y+6), "Z", fill="white")
      elif current_emotion == "angry":
        draw.line((20,10,55,18), "white", 2); draw.line((108,10,73,18), "white", 2)
        draw.rounded_rectangle((25, 20, 45, 35), radius=5, fill="white")
        draw.rounded_rectangle((83, 20, 103, 35), radius=5, fill="white")
      elif current_emotion == "surprise":
        draw.ellipse((25,15,45,35), outline="white", fill="white")
        draw.ellipse((83,15,103,35), outline="white", fill="white")
      elif current_emotion == "sad":
        draw.line((25,25,45,25), "white", 2); draw.line((83,25,103,25), "white", 2)
      else:
        draw.rounded_rectangle((25, 15, 50, 35), radius=7, fill="white")
        draw.rounded_rectangle((78, 15, 103, 35), radius=7, fill="white")
      if is_speaking:
        if self.mouth_open: draw.pieslice((34, 38, 94, 63), start=0, end=180, fill="white")
        else: draw.line((44, 48, 84, 48), fill="white")
      else:
        if current_emotion == "happy": draw.arc((40,45,88,60), 0,180, fill="white")
        elif current_emotion == "sad": draw.arc((45,50,83,65), 180,0, fill="white")
        elif current_emotion == "surprise": draw.ellipse((55,45,73,60), fill="white")
        else: draw.line((44, 48, 84, 48), fill="white")
  def animate_loop(self):
    global anim_counter
    while True:
      anim_counter += 1
      if is_speaking:
        self.mouth_open = not self.mouth_open
        self.draw(); time.sleep(0.12)
      elif current_emotion == "sleepy":
        self.draw(); time.sleep(0.2)
      else:
        self.mouth_open = False
        self.draw(); time.sleep(0.3)
fm = FaceManager(oled_device)
threading.Thread(target=fm.animate_loop, daemon=True).start()
# ================= CORE FUNCTIONS =================
def moveServo(channel, angle):
  try: kit.servo[channel].angle = int(max(0, min(180, angle)))
  except: pass
def wave_both_hands():
  for _ in range(2):
    moveServo(RIGHT_SHOULDER_ROLL, 150); moveServo(LEFT_ARM, 30); time.sleep(0.5)
    moveServo(RIGHT_SHOULDER_ROLL, 90); moveServo(LEFT_ARM, 90); time.sleep(0.5)
def speak(text, emotion="happy"):
  global is_speaking, current_emotion
  current_emotion = emotion
  clean_text = text.replace("*", "").replace("#", "").replace("- ", "").replace(’"’, "").replace("’", "")
  is_speaking = True
  os.system(f’echo "{clean_text}" | {PIPER_PATH} -m {PIPER_MODEL} --output_file /tmp/s.wav && aplay -q /tmp/s.wav’)
  is_speaking = False
def gesture_intro_sequence():
  moveServo(RIGHT_SHOULDER_ROLL, 180); moveServo(RIGHT_SHOULDER_PITCH,10); moveServo(RIGHT_ELBOW, 20)
  while is_speaking: time.sleep(0.1)
  time.sleep(0.5)
  moveServo(RIGHT_ELBOW, 90); moveServo(RIGHT_SHOULDER_PITCH, 90);
  moveServo(RIGHT_SHOULDER_ROLL, 90)
# ================= AI VOICE ASSISTANT =================
def run_assistant():
  global is_interacting, is_listening, chat_memory, current_emotion
  is_interacting = True
  # 1. Start Intro and CAPTURE THE THREAD
  intro_thread = threading.Thread(target=speak, args=("Hello, I am Pixel, your humanoid assistant. How can I help you?", "happy"))
  intro_thread.start()
  threading.Thread(target=gesture_intro_sequence).start()
  # 2. Wait for the introduction to finish speaking before listening
  intro_thread.join()
  time.sleep(0.5) # Silence gap to clear the speaker’s echo from the microphone buffer
  chat_memory = [{"role": "system", "content": "You are Pixel, a friendly humanoid robot. Speak naturally in 2-3 sentences. Don’t mention updates."}]
  r = sr.Recognizer()
  while is_interacting:
    with sr.Microphone() as source:
      # 3. Adjust for silence to flush the buffer
      r.adjust_for_ambient_noise(source, duration=0.6)
      is_listening = True
      try:
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
        is_listening = False
        user_text = r.recognize_google(audio)
        if any(word in user_text.lower() for word in ["stop", "goodbye", "exit"]):
          speak("Goodbye!", "happy")
          break
        chat_memory.append({"role": "user", "content": user_text})
        completion = client.chat.completions.create(model="llama-3.1-8b-instant", messages=chat_memory)
        response = completion.choices[0].message.content
        chat_memory.append({"role": "assistant", "content": response})
        # Speak response and pause briefly before listening again
        speak(response, "happy")
        time.sleep(0.3)
      except:
        is_listening = False
        break
    is_interacting = False
    current_emotion = "happy"
# ================= MAIN ROBOT LOOP =================
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (320,240)}))
picam2.start()
def ww_thread():
  porcupine = pvporcupine.create(access_key=PICO_KEY, keyword_paths=[WAKEWORD_PATH])
  recorder = PvRecorder(frame_length=porcupine.frame_length)
  recorder.start()
  while True:
    if porcupine.process(recorder.read()) >= 0 and not is_interacting:
      threading.Thread(target=run_assistant).start()
threading.Thread(target=ww_thread, daemon=True).start()
boot_sleep, greeted = True, False
last_seen, disabled_until, last_emotion_time = time.time(), 0, 0
while True:
  now = time.time()
  key = cv2.waitKey(1) & 0xFF
  if key == 27: break
  if key == ord(’g’):
    speak("I am going to sleep now.", "sleepy")
    boot_sleep, greeted = True, False; disabled_until = now + 1800
  if now < disabled_until:
    current_emotion = "sleepy"; time.sleep(0.1); continue
  if is_interacting:
    time.sleep(0.1); continue
  # Vision Processing
  frame_raw = picam2.capture_array()
  frame = cv2.rotate(cv2.cvtColor(frame_raw, cv2.COLOR_RGBA2BGR), cv2.ROTATE_180)
  h, w, _ = frame.shape
  blob = cv2.dnn.blobFromImage(frame, 1/255.0, (224, 224), (0,0,0), True,crop=False)
  net.setInput(blob)
  outs = net.forward(output_layers)
  p_count, phone, target = 0, False, None
  for out in outs:
    for det in out:
      scores = det[5:]
      cid = np.argmax(scores)
      if classes[cid] == "person" and scores[cid] > 0.85:
        p_count += 1
        if not target: target = (int(det[0]*w), int(det[1]*h))
      if classes[cid] == "cell phone" and scores[cid] > 0.3: phone =
  True
  if p_count > 0:
    boot_sleep = False; last_seen = now
    if phone:
      current_emotion = "angry"
      if now - last_emotion_time > 12:
        speak("Please put your phone away, I want to talk to you!","angry"); 
  last_emotion_time = now
    elif p_count >= 3:
      current_emotion = "surprise"
      if now - last_emotion_time > 15:
        speak("Oh! It is getting crowded here!", "surprise");
  last_emotion_time = now
    else:
      current_emotion = "happy"
    if target:
      tx, ty = target
      error_x, error_y = tx - w//2, ty - h//2
      if abs(error_x) > 40: target_pan -= Kp * error_x
      if abs(error_y) > 40: target_tilt -= (Kp * 0.5) * error_y
      target_pan = max(40, min(140, target_pan)); target_tilt = max(70, min(110, target_tilt))
      pan_angle = (pan_angle * (1 - smoothing_factor)) + (target_pan* smoothing_factor)
      tilt_angle = (tilt_angle * (1 - smoothing_factor)) + (
      target_tilt * smoothing_factor)
      moveServo(PAN_CH, pan_angle); moveServo(TILT_CH, tilt_angle)
    if not greeted:
      greeted = True
      threading.Thread(target=wave_both_hands).start()
      speak("Hello, nice to meet you", "happy")
  else:
    if boot_sleep: current_emotion = "sleepy"
    elif now - last_seen > 30:
      if greeted: speak("I’m feeling lonely.", "sad"); greeted =
  False
      else: current_emotion = "sad"
  cv2.imshow("Pixel Vision", frame)
cv2.destroyAllWindows()
