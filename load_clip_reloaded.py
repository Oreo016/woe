import torch
import open_clip
from picamera import PiCamera
import time
from datetime import datetime
from PIL import Image
import os
import RPi.GPIO as GPIO
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor
from adafruit_motor import Servokit
import sys
# Pin Configuration
PIR_PIN = 17  # GPIO pin connected to PIR sensor

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
GPIO.setup(18, GPIO.OUT)  # Motor control pin
GPIO.setup(23, GPIO.OUT)  # Flap control pin
USE_PI_CAMERA = True  # Set to True if using Raspberry Pi camera
# Load CLIP model (ViT-B-32)
device = "cpu"  # Raspberry Pi doesn't have a GPU, so we use CPU
model, preprocess, _ = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")
tokenizer = open_clip.get_tokenizer("ViT-B-32-quickgelu")

# Move model to CPU
model.to(device)
camera = PiCamera()
camera.resolution = (1280, 720)
waste_classes = [
    "Compostable organic waste like food scraps, leaves, and plants",  # Biodegradable
    "Non-biodegradable materials like metal, glass, and fabric",       # Non-Biodegradable
    "Plastic waste such as bottles, wrappers, and containers",         # Plastic
    "Other waste including hazardous or unknown materials"             # Other
]

print("CLIP model loaded successfully!")

text_inputs = tokenizer(waste_classes).to(device)
#    open_flap()  # Open flap
#intialize servo motor
kit = Servokit(channels=16)  # Initialize ServoKit on I2C bus 1
kit.servo[8].set_pulse_width_range(500, 2500)  # Set pulse width range for servo
kit.servo[8].angle = 0  # Set initial angle to 0 degrees
def open_flap()->None:
    """Open the flap for a specified duration"""
    kit.servo[8].angle = 90  # Open flap to 90 degrees
    time.sleep(2)  # Keep open for 2 seconds
    kit.servo[8].angle = 0  # Close flap to 0 degrees
    print("Flap closed")
# Initialize PCA9685 for motor control
i2c = busio.I2C(board.SCL, board.SDA)   # Initialize I2C bus
pca = PCA9685(i2c)  # Initialize PCA9685
pca.frequency = 1000  # Set frequency for motor control

# Assign channels for motor control
in1_channel = pca.channels[0]  # Connect this to L298N IN1
in2_channel = pca.channels[1]  # Connect this to L298N IN2
ena_channel = pca.channels[2]  # Connect this to L298N ENA
my_motor = motor.DCMotor(in1_channel, in2_channel)  # Create a motor object
my_motor.decay_mode = motor.SLOW_DECAY  # Optional: smoother stopping
def motor_control(time: float) -> None:
    """
    Control motor speed.
    speed range:
    -1.0 = full reverse
     0.0 = stop
     1.0 = full forward
    """
    my_motor.throttle = 0.5  # Set motor speed
    time.sleep(time)  # Run motor for specified time
    my_motor.throttle = 0.0  # Stop motor
    time.sleep(0.5)  # Allow some time before stopping
    open_flap()  # Open flap
    time.sleep(1)  # Keep open for 1 seconds
    my_motor.throttle = -0.5 # Stop motor
    time.sleep(time)
    my_motor.throttle = 0.0  # Stop motor
    time.sleep(0.5)  # Allow some time before stopping

def classify_waste(image_path)->int:
    """Classify waste image using CLIP"""
    f=open("output.txt","w")
    image = Image.open(image_path).convert("RGB")  # Load image
    image = preprocess(image).unsqueeze(0).to(device)  # Preprocess

    with torch.no_grad():
        image_features = model.encode_image(image)
        text_features = model.encode_text(text_inputs)
        similarity = (image_features @ text_features.T).softmax(dim=-1)

    class_id = similarity.argmax().item()
    f.write(str(class_id))
  # Get the most probable category
    f.close()
    print(f"Predicted class ID: {class_id}")    
    return class_id

# Test with an image

   

def capture()->str:
    try:
        camera = PiCamera()
        camera.resolution = (1920, 1080)  # Set resolution
        t=0.5
        print(f"Waiting for {t} seconds...")
        time.sleep(t)  # Delay before capturing
        file_name=str(datetime.now())+".jpg"
        print("Capturing image...")
        camera.start_preview()

        time.sleep(2)  # Allow camera to adjust
        camera.capture(file_name)  # Capture image
        camera.stop_preview()
        
        print(f"Image saved as {file_name}")
        camera.close()
        return file_name
    except:
        print("File not found")
def rotation2(roatation_id : int)-> None:
    print("Rotating motor based on classification result")
    
    

def capture2()->str:
    file_name=str(datetime.now())+".jpg"
    os.system(f"libcamera-still -o {file_name}")
    os.system(f"libcamera-still -o {file_name}")   
    return file_name
def rotation(garbage_id: int = 3) -> None:
    """Rotate motor based on classification result"""
    
    if garbage_id==0:
       motor_control(1)  # Rotate motor forward
       print("Biodegradable Waste")
        
    elif garbage_id==1:
        motor_control(2)  # Rotate motor forward
        print("Non-Biodegradable Waste")
    elif garbage_id==2:
        motor_control(3)  # Rotate motor forward
        print("Plastic Waste")
    else:
        motor_control(4)
        print("Other Waste")


file_path=""
try:
    print("PIR Sensor Active - Waiting for Motion...")
    while True:
        if GPIO.input(PIR_PIN):  # Motion Detected
            print("Motion Detected! Capturing Image...")
            
            file_path=capture2()
            garbage_type=classify_waste(file_path)
            rotation()
         
            time.sleep(5)  # Prevent multiple triggers in a short time
           
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting Program...")
    GPIO.cleanup()

   
