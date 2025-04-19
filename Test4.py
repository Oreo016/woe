import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import motor

# Setup I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Setup PCA9685
pca = PCA9685(i2c)
pca.frequency = 1000  # Set frequency for motor control

# Setup motor using Motor library
# Assign channels
in1_channel = pca.channels[0]  # Connect this to L298N IN1
in2_channel = pca.channels[1]  # Connect this to L298N IN2
ena_channel = pca.channels[2]  # Connect this to L298N ENA

# Create a motor object
my_motor = motor.DCMotor(in1_channel, in2_channel)
my_motor.decay_mode = motor.SLOW_DECAY  # Optional: smoother stopping

# Function to set motor speed
def set_motor_speed(speed):
    """
    speed range:
    -1.0 = full reverse
     0.0 = stop
     1.0 = full forward
    """
    my_motor.throttle = speed

# Main program
try:
    print("Motor Forward")
    set_motor_speed(0.8)  # 80% forward
    time.sleep(3)

    print("Motor Backward")
    set_motor_speed(-0.5)  # 50% backward
    time.sleep(3)

    print("Motor Stop")
    set_motor_speed(0.0)

except KeyboardInterrupt:
    print("Program stopped by user")
    set_motor_speed(0.0)
