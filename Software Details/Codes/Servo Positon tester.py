#I generated this one code using AI to calsulate and verify the suitable servo positions for our main locker door
#Whenever the axle collapsed due to overwork, this code was used to determine the new position after attaching it.
#I do not take credits of making this code, its all AI.

from machine import Pin, PWM
import time


# SERVO CALIBRATION TOOL


# Initialize the servo on Pin 13 (matching your master code)
servo = PWM(Pin(13), freq=50)

print("--- Servo Calibration Started ---")
print("Standard safe duty range is typically between 40 and 115.")
print("Type a number and press Enter to test an angle.")
print("Type 'q' to quit.")
print("-" * 35)

while True:
    # Wait for you to type a number in the console
    user_input = input("Enter duty value: ")
    
    # Check if you want to quit
    if user_input.lower() == 'q':
        print("Stopping calibration.")
        servo.duty(user_input) # Depower the motor
        break
        
    try:
        # Convert your typed text into an integer
        val = int(user_input)
        
        # A safety net to prevent you from accidentally typing 
        # a massive number and breaking the servo gears!
        if 20 <= val <= 130:
            print(f"--> Moving to: {val}")
            servo.duty(val)
        else:
            print("WARNING: Value is outside the safe range (20-130). Try again.")
            
    except ValueError:
        print("Please enter a valid whole number.")
