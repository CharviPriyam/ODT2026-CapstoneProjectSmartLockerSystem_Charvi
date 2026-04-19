#Gateway 2 wherein a user generates an equation on the app in the form of a+b-c or a-b+c
#User then solves the equation, places the hand at the correct distance from the locker - locker responds
#==========================================================================================
#IMPORT MODULES

from machine import Pin, time_pulse_us, PWM
import time
import neopixel
import bluetooth
import random
#==========================================================================================

#==========================================================================================
#BLUETOOTH SETUP

conn_handle = None 
value = "" 
name = "Chika" 
ble = bluetooth.BLE() 

ble.active(False) 
time.sleep(0.5)
ble.active(True)
ble.config(gap_name=name)

service_UUID = bluetooth.UUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
char_UUID = bluetooth.UUID("6e400002-b5a3-f393-e0a9-e50e24dcca9e")

char = (char_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY) #Data can be both written, read and then notified (pushed) to the app
service = (service_UUID, (char,),)
((char_handle,),) = ble.gatts_register_services((service,))

def event_occured(event, data):
    global conn_handle, value 
    if event == 1:      #Event 1 means a device (your phone) just connected. It saves the connection ID to conn_handle
        conn_handle = data[0]
        print("Connected to App")
        
    elif event == 2:    #Event 2 means the phone disconnected. It resets conn_handle to None.
        print("Disconnected from App")
        conn_handle = None
        advertise(name) #Advertise() function so the ESP32 becomes discoverable again.
        
    elif event == 3:
        conn_handle, value_handle = data
        if value_handle == char_handle:    #reading the Value written on characteristics by Phone/client
            raw_msg = ble.gatts_read(char_handle).rstrip(b'\x00')
            value = raw_msg.decode().strip()
            print("Bluetooth Received:", value)

def advertise(device_name):
    name_bytes = device_name.encode()
    flags = bytearray([0x02, 0x01, 0x06])
    short_name = bytearray([len(name_bytes) + 1, 0x08]) + name_bytes   #These lines construct a "payload packet" out of raw bytes, so phones can read the device's name ("Chika") before connecting.
    full_name = bytearray([len(name_bytes) + 1, 0x09]) + name_bytes
    adv_data = flags + short_name + full_name
    ble.gap_advertise(50, adv_data=adv_data)    #Starts the actual broadcasting, sending out a signal every 50 milliseconds.
    print("Awaiting Connection... Advertising as:", device_name)

advertise(name)
ble.irq(event_occured)
#==========================================================================================

#==========================================================================================
#HARDWARE INITIALISATION

#Buzzer
buzzer = PWM(Pin(33, Pin.OUT))
buzzer.duty(0)

#NeoPixel (16 LEDs)
np = neopixel.NeoPixel(Pin(12), 16)

#Servo Motor
servo = PWM(Pin(13), freq=50)
S_CLOSED = 40   #0 degrees - start position
S_OPEN = 115    #180 degrees - end position
servo.duty(S_CLOSED) 

#Ultrasonic Sensor
trig = Pin(26, Pin.OUT)
echo = Pin(34, Pin.IN)
#==========================================================================================

#==========================================================================================
#SYSTEM VARIABLES

active_mode = 0 # 0 = Idle, 2 = Gateway 2 Active

#Gateway 2 Variables
target_distance = 0.0 
TOLERANCE = 2.0     #+/- 1cm leeway for human error
steady_count = 0    #Timer to ensure hand is still
last_dist = 0.0     #Tracks previous hand position
#==========================================================================================

#==========================================================================================
#DEFINED FUNCTIONS

#function to open locker
def open_locker():
    print("Unlocking Main Door...")
    servo.duty(S_OPEN)
    time.sleep(0.5) 

#function to close locker
def close_locker():
    print("Locking Main Door...")
    servo.duty(S_CLOSED)
    time.sleep(0.5)

#ultrasound sensor code to measure distance
def measure_distance():
    """Fires the ultrasonic pulse and returns distance in cm."""
    trig.off()
    time.sleep_us(2)
    trig.on()
    time.sleep_us(10)
    trig.off()
    
    #30000us timeout prevents code freeze if no object is there
    duration = time_pulse_us(echo, 1, 30000) 
    if duration < 0:
        return 999 
    else:
        return duration / 58.0

#correct scenario (buzzer, neopixel - green)
def success_effect():
    print("Access Granted!")
    buzzer.duty(512)
    for freq in [1000, 1500, 2000]:
        buzzer.freq(freq)
        time.sleep(0.1)
    buzzer.duty(0)
    
    for i in range(16):
        np[i] = (0, 255, 0) 
        np.write()
        time.sleep(0.05)
    time.sleep(1)
    clear_leds()

#wrong scenario (buzzer, neopixel - red)
def wrong_effect():
    print("Failed Attempt!")
    buzzer.duty(512)
    buzzer.freq(300)
    time.sleep(0.5)
    buzzer.duty(0)
    
    for i in range(16):
        np[i] = (255, 0, 0) 
    np.write()
    time.sleep(1)
    clear_leds()

#neopixel when no input
def clear_leds():
    for i in range(16):
        np[i] = (0, 0, 0)
    np.write()
#==========================================================================================
    
#==========================================================================================
#MAIN LOOP

clear_leds()
print("System Idle. Waiting for App connection...")

while True:
    
    #CHECK BLUETOOTH COMMANDS
    
    if value == '6':
        #Picking the answer first (between 10 and 15)
        target_distance = random.randint(10, 15)
        
        #Randomly choosing the pattern: A+B-C or A-B+C
        pattern = random.choice(['+-', '-+'])
        
        #Working backwards to build the equation
        if pattern == '+-':
            #Pattern: num1 + num2 - num3 = target_distance
            num3 = random.randint(1, 9)              #Pick a random number to subtract, for example 8 = num3
            subtotal = target_distance + num3        #subtotal = 12+8 = 20
            num1 = random.randint(1, subtotal - 1)   #(1,19) = lets say, 15 = num1
            num2 = subtotal - num1                   #num2 = 20-15 = 5            
            equation_str = str(num1) + " + " + str(num2) + " - " + str(num3) + " = ?" #15+5-8 = ? (12!)
            
        else:
            #Pattern: num1 - num2 + num3 = target_distance
            num3 = random.randint(1, 9)              # Pick a random number to add, for example 6 = num3
            subtotal = target_distance - num3        #subtotal = 12-6 = 6
            num2 = random.randint(1, 9)              #Pick a random number to subtract, for example 3 = num2
            num1 = subtotal + num2                   #6+3 = 9
            equation_str = str(num1) + " - " + str(num2) + " + " + str(num3) + " = ?"  #9-3+6=? (12!) [BODMAS - addition & subtraction have equal priority, solve from left to right]
            
        print("Generated Equation:", equation_str)
        
        #Sending the equation to the phone
        ble.gatts_write(char_handle, "B" + equation_str)   
        if conn_handle is not None: 
            ble.gatts_notify(conn_handle, char_handle) 
            
        active_mode = 2 #Activate the ultrasonic sensor
        steady_count = 0
        last_dist = 0
        value = "" 
        print("System Switched to Gateway 2. Waiting for hand placement...")

    elif value != "":
        value = "" #Clear any unused commands


    #GATEWAY 2 HARDWARE 
    
    if active_mode == 2:
        current_dist = measure_distance()
        
        #Ignore ghost glitches entirely! [Utrasound was acting up - dhangh se nahi chal rha tha]
        #If the sensor hiccups, we just skip this loop and keep the timer running.
        if current_dist < 2 or current_dist == 999:
            pass 
            
        #Normal sensing zone (Hand is between 2cm and 25cm)
        elif current_dist < 25:
            
            #Slightly wider stability margin (2.5cm) to allow for natural hand shaking
            if abs(current_dist - last_dist) < 2.5:
                steady_count += 1
            else:
                steady_count = 0 # Hand is actually moving, reset timer
                
            #If steady for ~1.5 seconds (15 loops)
            if steady_count >= 15:
                print(f"Hand locked in at: {current_dist:.1f} cm")
                
                #Evaluating the answer
                if (target_distance - TOLERANCE) <= current_dist <= (target_distance + TOLERANCE):
                    success_effect()
                    open_locker()
                    time.sleep(15) 
                    close_locker()
                    
                    steady_count = 0
                    active_mode = 0 
                    print("System Idle. Waiting for App command...")
                else:
                    wrong_effect()
                    steady_count = 0
                    
                    #Anti-Punishment Loop. 
                    #Force the user to completely remove their hand before trying again.
                    print("Please remove hand from sensor to try again.")
                    while measure_distance() < 25:
                        time.sleep(0.1)
                    print("Ready for a new attempt!")
                    
            last_dist = current_dist
            
        else:
            #Hand is removed or too far away, reset the timer safely
            steady_count = 0
            last_dist = 0
            
    time.sleep(0.1) # Loop delay for sensor stability
