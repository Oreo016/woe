import torch
import open_clip
from picamera import PiCamera
import time
from datetime import datetime
from PIL import Image
import os
import RPi.GPIO as GPIO
import time
# Pin Configuration
PIR_PIN = 17  # GPIO pin connected to PIR sensor

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)
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
        print("Biodegradable Waste")
        os.system("python3 motor.py 1")
    elif garbage_id==1:
        print("Non-Biodegradable Waste")
        os.system("python3 motor.py 2")
    elif garbage_id==2:
        print("Plastic Waste")
        os.system("python3 motor.py 3")
    else:
        print("Other Waste")
        os.system("python3 motor.py 4")
def open_flap()->None:
    """Open the flap for a specified duration"""
    os.system("python3 motor.py 5")  # Open flap
    time.sleep(2)  # Keep open for 5 seconds
    os.system("python3 motor.py 6")  # Close flap 
    print("Flap closed")

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
    

   
