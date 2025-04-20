import RPi.GPIO as GPIO
import time

# Use BCM pin numbering
GPIO.setmode(GPIO.BCM)

# PIR sensor output connected to GPIO17
PIR_PIN = 17

# Setup pin as input
GPIO.setup(PIR_PIN, GPIO.IN)

print("Motion Sensor Ready (Press CTRL+C to exit)")

try:
    while True:
        if GPIO.input(PIR_PIN):
            print("Motion Detected!")
        else:
            print("No Motion")
        time.sleep(1)  # Delay for readability

except KeyboardInterrupt:
    print("Quit")
    GPIO.cleanup()
