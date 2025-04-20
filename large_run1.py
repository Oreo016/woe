import torch
import open_clip
from picamera import PiCamera
import time
from datetime import datetime
from PIL import Image
import os
import RPi.GPIO as GPIO
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor
from adafruit_servokit import ServoKit

# Pin Configuration
PIR_PIN = 17  # GPIO pin connected to PIR sensor

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

USE_PI_CAMERA = True  # Set to True if using Raspberry Pi camera

# Load CLIP model (ViT-B-32)
device = "cpu"
model, preprocess, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")
tokenizer = open_clip.get_tokenizer("ViT-B-32-quickgelu")
model.to(device)

# Camera Configuration
camera = PiCamera()
camera.resolution = (1280, 720)

# Waste classification labels
waste_classes = [
    "Compostable organic waste like food scraps, leaves, and plants",  # Biodegradable
    "Non-biodegradable materials like metal, glass, and fabric",       # Non-Biodegradable
    "Plastic waste such as bottles, wrappers, and containers",         # Plastic
    "Other waste including hazardous or unknown materials"             # Other
]

print("CLIP model loaded successfully!")

text_inputs = tokenizer(waste_classes).to(device)

# Initialize ServoKit for flap
kit = ServoKit(channels=16)
kit.servo[8].set_pulse_width_range(500, 2500)
kit.servo[8].angle = 0

def open_flap() -> None:
    kit.servo[8].angle = 90
    time.sleep(2)
    kit.servo[8].angle = 0
    print("Flap closed")

# Initialize PCA9685 for motor control
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000

# Assign channels for motor control
in1_channel = pca.channels[0]
in2_channel = pca.channels[1]
ena_channel = pca.channels[2]

my_motor = motor.DCMotor(in1_channel, in2_channel)
my_motor.decay_mode = motor.SLOW_DECAY

def motor_control(duration: float) -> None:
    my_motor.throttle = 0.5
    time.sleep(duration)
    my_motor.throttle = 0.0
    time.sleep(0.5)
    open_flap()
    time.sleep(1)
    my_motor.throttle = -0.5
    time.sleep(duration)
    my_motor.throttle = 0.0
    time.sleep(0.5)

def classify_waste(image_path) -> int:
    image = Image.open(image_path).convert("RGB")
    image = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text_inputs)
        similarity = (image_features @ text_features.T).softmax(dim=-1)

    class_id = similarity.argmax().item()
    print(f"Predicted class ID: {class_id}")
    return class_id

def capture2() -> str:
    file_name = str(datetime.now()) + ".jpg"
    print("Capturing image...")
    os.system(f"fswebcam -r 1280x720 --no-banner {file_name}")
    print(f"Image saved as {file_name}")
    return file_name

rotation_map = {
    0: (1, "Biodegradable Waste"),
    1: (2, "Non-Biodegradable Waste"),
    2: (3, "Plastic Waste"),
    3: (4, "Other Waste")
}

def rotation(garbage_id: int = 3) -> None:
    duration, label = rotation_map.get(garbage_id, (4, "Other Waste"))
    motor_control(duration)
    print(label)

try:
    print("PIR Sensor Active - Waiting for Motion...")
    while True:
        if GPIO.input(PIR_PIN):
            print("Motion Detected! Capturing Image...")
            file_path = capture2()
            garbage_type = classify_waste(file_path)
            rotation(garbage_type)
            print("Processing complete. Waiting for next motion...")
            time.sleep(5)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting Program...")
    GPIO.cleanup()
