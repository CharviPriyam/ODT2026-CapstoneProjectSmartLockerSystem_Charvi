#trial compiled code for gateway 1 
#as user enters the code on keypad (pushbuttons), each pb has different frequency
#correct sequence - servo opens door, neopixel - green, correct buzz
#wrong sequence - servo does NOT open door, neopixel - red, wrong buzz
#servo does not respond after 3 wrong attempts

#import modules
from machine import Pin, PWM
import time
import neopixel

#initialisation
#buzzer
buzzer = PWM(Pin(23, Pin.OUT))
buzzer.duty(0)
#NeoPixel
np = neopixel.NeoPixel(Pin(15), 16)
#Pushbuttons using list to keep it short
button_pins = [13, 12, 14, 27, 26, 4, 5, 18, 19, 21] # Represents digits 0-9
buttons = []
for p in button_pins:
    buttons.append(Pin(p, Pin.IN, Pin.PULL_UP))
#Servo
servo=PWM(Pin(4))    #Pin.OUT default hence optional
servo.freq(50)
S_CLOSED = 40   # 0 degrees
S_OPEN = 115    # 180 degrees

target_otp = [1, 2, 3, 4]  # The correct code (simulating the Bluetooth OTP)
entered_otp = []           # Stores what the user types
wrong_attempts = 0         # Counts failed tries
is_locked = False          # Becomes True after 3 wrong tries

#functions using def
def open_locker():
    """Rotates the servo to the open position."""
    print("Unlocking...")
    servo.duty(S_OPEN)
    time.sleep(0.5) # Give the motor half a second to physically turn

def close_locker():
    """Rotates the servo back to the closed position."""
    print("Locking...")
    servo.duty(S_CLOSED)
    time.sleep(0.5)
    
def play_button_sound(digit_index):
    #Plays a unique frequency based on the button pressed.
    buzzer.duty(512)
    start_freq = 800 + (digit_index * 100)
    for f in range(start_freq, start_freq + 100, 10): 
        buzzer.freq(f)
        time.sleep(0.005)
    buzzer.duty(0)

def success_effect():
    """Green LEDs one-by-one and a happy sound."""
    print("Access Granted!")
    # Happy Sound
    buzzer.duty(512)
    for freq in [1000, 1500, 2000]:
        buzzer.freq(freq)
        time.sleep(0.1)
    buzzer.duty(0)
    
    # Green LED Sequence
    for i in range(16):
        np[i] = (0, 255, 0) # Green
        np.write()
        time.sleep(0.05)
    time.sleep(1)
    clear_leds() #function defined ahead

def wrong_effect():
    #Red LEDs flash and an error sound.
    print("Wrong Code!")
    # Error Sound
    buzzer.duty(512)
    buzzer.freq(300)
    time.sleep(0.5)
    buzzer.duty(0)
    
    # Red LED Flash
    for i in range(16):
        np[i] = (255, 0, 0) # Red
    np.write()
    time.sleep(1)
    clear_leds() #function defined ahead

def clear_leds():
    """Turns off all NeoPixels."""
    for i in range(16):
        np[i] = (0, 0, 0)
    np.write()

#main loop
clear_leds()
print("System Ready. Enter 4-digit OTP.")

while True:
    # If the system is locked, skip checking the buttons entirely
    if is_locked:
        continue 

    # Loop through all 10 buttons to see if any are pressed
    for i in range(10):
        if buttons[i].value() == 0: # Button is pressed
            
            play_button_sound(i)
            entered_otp.append(i) # Add the digit to our list
            print("Typed:", i)
            
            # Wait for the user to let go of the button (Debounce)
            while buttons[i].value() == 0:
                time.sleep(0.01)
            
            # Check if they have entered 4 digits yet
            if len(entered_otp) == 4:
                
                if entered_otp == target_otp:
                    success_effect()
                    open_locker()
                    time.sleep(20) # Keep open for 20 seconds
                    close_locker()
                    time.sleep(3) # Keep closed for 3 seconds #CHECKKKKK
                    entered_otp = [] # Reset for next time
                    wrong_attempts = 0 # Reset attempts
                    
                else:
                    wrong_effect()
                    wrong_attempts += 1
                    entered_otp = [] # Clear their wrong entry
                    
                    # Check for lockout
                    if wrong_attempts >= 3:
                        print("SYSTEM LOCKED! 3 Wrong Attempts.")
                        is_locked = True
                        
    time.sleep(0.05) # Small delay to keep the ESP32 running smoothly
