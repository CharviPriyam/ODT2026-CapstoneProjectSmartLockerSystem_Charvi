from machine import Pin, time_pulse_us, PWM
import time
import neopixel


# Ultrasonic Sensor
trig = Pin(27, Pin.OUT)
echo = Pin(14, Pin.IN)

# Servo Motor (Pin 4) - Using the safe positioning logic
servo = PWM(Pin(4), freq=50)
POS_CLOSED = 40
POS_OPEN = 115
servo.duty(POS_CLOSED) # Ensure it starts locked

# Buzzer (Pin 23)
buzzer = PWM(Pin(23, Pin.OUT))
buzzer.duty(0)

# NeoPixel (Pin 15, 16 LEDs)
np = neopixel.NeoPixel(Pin(15), 16)



# In the final system, this target will be sent from the App via Bluetooth.
# For testing, we assume the equation was "15 - 3 = ?", so target is 12.
target_distance = 12.0 

# We allow +/- 1cm of error since it's hard for a human to hold perfectly still
TOLERANCE = 1.0 



def measure_distance():
    """Fires the ultrasonic pulse and returns the distance in cm."""
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    
    # 30000us timeout prevents the code from freezing if nothing is detected
    duration = time_pulse_us(echo, 1, 30000) 
    
    if duration < 0:
        return 999 # Return a high number if nothing is detected
    else:
        return duration / 58.0 # Convert time to cm

def success_effect():
    """Green LEDs, happy sound, and opens the servo."""
    print("Correct! Access Granted.")
    buzzer.duty(512)
    for freq in [1000, 1500, 2000]:
        buzzer.freq(freq)
        time.sleep(0.1)
    buzzer.duty(0)
    
    for i in range(16):
        np[i] = (0, 255, 0) # Green
        np.write()
        time.sleep(0.05)
        
    # Open the locker
    servo.duty(POS_OPEN)
    time.sleep(4) # Keep it open for 4 seconds
    
    # Close it back and turn off LEDs
    servo.duty(POS_CLOSED)
    clear_leds()

def wrong_effect():
    """Red LEDs and an error sound."""
    print("Wrong Distance!")
    buzzer.duty(512)
    buzzer.freq(300)
    time.sleep(0.5)
    buzzer.duty(0)
    
    for i in range(16):
        np[i] = (255, 0, 0) # Red
    np.write()
    time.sleep(1.5)
    clear_leds()

def clear_leds():
    """Turns off all NeoPixels."""
    for i in range(16):
        np[i] = (0, 0, 0)
    np.write()


clear_leds()
print("Gateway 2 Ready. Solve the equation and position your hand.")

steady_count = 0
last_dist = 0

while True:
    current_dist = measure_distance()
    
    # Only start checking if a hand is reasonably close (under 25cm)
    if current_dist < 25:
        
        # Check if the hand is staying relatively still (within 1.5cm of its last position)
        if abs(current_dist - last_dist) < 1.5:
            steady_count += 1
        else:
            steady_count = 0 # Hand is moving, reset the counter
            
        # If the hand has been steady for ~1 second (10 loops of 0.1s)
        if steady_count >= 10:
            print(f"Hand locked in at: {current_dist:.1f} cm")
            
            # Evaluate the answer
            if (target_distance - TOLERANCE) <= current_dist <= (target_distance + TOLERANCE):
                success_effect()
            else:
                wrong_effect()
                
            # Reset after an attempt so it doesn't loop instantly
            steady_count = 0
            time.sleep(2) 
            
        last_dist = current_dist
        
    else:
        # No hand detected, reset everything
        steady_count = 0
        last_dist = 0
        
    time.sleep(0.1) # Fast loop for responsive reading
