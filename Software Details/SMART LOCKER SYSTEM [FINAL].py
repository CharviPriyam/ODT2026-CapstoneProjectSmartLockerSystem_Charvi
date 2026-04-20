#========================================================================================================================
#FINAL CODE :)
#==========================================================================================
#IMPORTING MODULES

from machine import Pin, time_pulse_us, PWM
import time
import neopixel
import bluetooth
import random
#==========================================================================================

#==========================================================================================
#SETTING UP BLUETOOTH

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

#Pushbuttons - USING 26 at the end instead of 2 to fix the ghost typing (pin 2 wasn't taking input)
#before gpio 35, we had gpio 26, we made 35 work by adding an external "PullUp" resistor using Nayan's brilliant teachings.
#10k ohm resistor was attached externally (we had to resort to this coz of lack of gpios)
button_pins = [15, 4, 5, 18, 19, 21, 22, 23, 25, 35]    #usage of lists to shorten initialisation code, big brain
buttons = [Pin(p, Pin.IN, Pin.PULL_UP) for p in button_pins]

#Servo Motor (Main Locker)
servo = PWM(Pin(13), freq=50)
S_CLOSED = 110   
S_OPEN = 70    
servo.duty(S_CLOSED) 

#Ultrasonic Sensor
trig = Pin(26, Pin.OUT)
echo = Pin(34, Pin.IN)

#Stepper Motor (Mini Locker - Gateway 3)
in1 = Pin(14, Pin.OUT)
in2 = Pin(27, Pin.OUT)
in3 = Pin(32, Pin.OUT)
in4 = Pin(2, Pin.OUT)

#Wave Drive Sequence: Only one coil is energized at a time.
seq = [
    [1, 0, 0, 0],  # Step 1 → Energize Coil A
    [0, 1, 0, 0],  # Step 2 → Energize Coil B
    [0, 0, 1, 0],  # Step 3 → Energize Coil C
    [0, 0, 0, 1]   # Step 4 → Energize Coil D
]
#==========================================================================================

#==========================================================================================
#SYSTEM VARIABLES

active_mode = 0 #0 = Idle, 1 = Gateway 1 (OTP Mode), 2 = Gateway 2 (Math Mode)

#Gateway 1 Variables
target_otp = []  #otp to match
entered_otp = []  #otp entered by user   
wrong_attempts = 0  #used for 3 wrong attempt condition (incremented later)   
is_locked = False          
digit_map = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0] #translation of the list index to the physical button label

#Gateway 2 Variables
target_distance = 0.0 
TOLERANCE = 2.0     #+/- 2cm leeway for human error
steady_count = 0    #Timer to ensure hand is still
last_dist = 0.0     #Tracks previous hand position

#Gateway 3 Variables (Mini Locker)
list1 = ['3', '4', '1', '2'] #The target colour pattern [Back wall of the main locker painted accordingly]
list2 = []                   #Stores the app inputs for the pattern
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

#function to play different frequencies of every button pressed on keypad
def play_button_sound(digit_index):
    buzzer.duty(512)
    start_freq = 600 + (digit_index * 200)
    for f in range(start_freq, start_freq + 150, 10): 
        buzzer.freq(f)
        time.sleep(0.005)
    buzzer.duty(0)

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
    clear_leds()  #function defined ahead

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

# neopixel when no input
def clear_leds():
    for i in range(16):
        np[i] = (0, 0, 0)
    np.write()
#==========================================================================================

#==========================================================================================
#MAIN LOOP

clear_leds() #starts idle
print("System Idle. Waiting for App connection...")

while True:
    
    #==========================================================================================
    #CHECK BLUETOOTH COMMANDS
    if value: 
        
        #==========================================================================================
        #GATEWAY 3 (Mini Locker Sequence from App: '1', '2', '3', '4')
        
        if value in ['1', '2', '3', '4','9','10','7','8']:
            list2.append(value)
            print("Entered Pattern:", list2)
            value = ""
            time.sleep(0.5)
            
            if len(list2) == 4: 
                if list2 == list1:
                    print('yay! Mini Locker Unlocked!')
                    
                    #Buzzer (Distinct from main locker)
                    buzzer.duty(512)
                    buzzer.freq(1200) # Simple high pitch chime
                    time.sleep(0.3)
                    buzzer.freq(1500)
                    time.sleep(0.3)
                    buzzer.duty(0)
                    
                    #Custom NeoPixel Success Sequence for Gateway 3
                    for _ in range(3):
                        r = random.randint(0, 255)
                        g = random.randint(0, 255)
                        b = random.randint(0, 255)
                        for i in range(0, 16):
                            np[i] = (r, g, b)
                            np.write()
                            time.sleep(0.05) #Sped up slightly for smoother effect
                            
                    #Turn off NeoPixel
                    for i in range(0, 16):
                        np[i] = (0, 0, 0)
                    np.write()
                    time.sleep(0.05)
                    
                    #Stepper Motor Opens Mini Locker
                    print("Opening Mini Locker...")
                    for _ in range(256):
                        for step in seq:
                            in1.value(step[0])
                            in2.value(step[1])
                            in3.value(step[2])
                            in4.value(step[3])
                            time.sleep(0.005)
                            
                    time.sleep(10) #Keep Mini Locker open for 10 seconds
                    
                    #Stepper Motor Closes Mini Locker
                    print("Closing Mini Locker...")
                    for _ in range(300):
                        for r_step in reversed(seq):
                            in1.value(r_step[0])
                            in2.value(r_step[1])
                            in3.value(r_step[2])
                            in4.value(r_step[3])
                            time.sleep(0.005)
                            
                    #Depower coils to prevent overheating
                    in1.value(0)
                    in2.value(0)
                    in3.value(0)
                    in4.value(0)
                    
                    list2 = [] #Reset list after success
                    print("Mini Locker sequence reset.")
                    
                else:
                    print('Incorrect sequence!')
                    wrong_effect()
                    list2 = [] #Reset list after failure
                #==========================================================================================
                    
        #==========================================================================================
        #GATEWAY 1 ('5' - OTP Generator)
                    
        elif value == '5':
            OTP = random.randint(1000, 9999)   #generates a random 4 digit number
            print("Generated OTP:", OTP)
            
            #Convert string OTP to a list of integers [e.g., 4, 8, 2, 1]
            target_otp = [int(d) for d in str(OTP)] 
            otp_tag="A" + str(OTP)
            #Send back to App
            ble.gatts_write(char_handle, otp_tag.encode('utf-8') )   #Writes the new OTP string into the Characteristic's memory on the ESP32 (GATT language)
            if conn_handle is not None:     #if phone is not disconnected i.e if it is connected...
                ble.gatts_notify(conn_handle, char_handle)    #it "pushes" the new OTP directly to the phone via the NOTIFY flag we set up earlier
                
            active_mode = 1
            is_locked = False
            wrong_attempts = 0
            entered_otp = []
            list2 = [] 
            value = "" 
            print("System Switched to Gateway 1. Enter code on physical buttons.")
        #==========================================================================================
        
        #==========================================================================================
        # GATEWAY 2 ('6' - Math Equation Generator)
        
        elif value == '6':
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
            eqn_tag= "B" + equation_str
            #Sending the equation to the phone
            ble.gatts_write(char_handle,eqn_tag.encode('utf-8') )  
            if conn_handle is not None: 
                ble.gatts_notify(conn_handle, char_handle) 
                
            active_mode = 2 #Activate the ultrasonic sensor
            steady_count = 0
            last_dist = 0
            list2 = [] 
            value = "" 
            print("System Switched to Gateway 2. Waiting for hand placement...")

        else:
            value = "" #Clear any unused commands
        #==========================================================================================
    
    #==========================================================================================
    #GATEWAY 1 HARDWARE (Physical Pushbuttons)
    
    if active_mode == 1:
        if not is_locked: 
            for i in range(10):
                if buttons[i].value() == 0: 
                    
                    play_button_sound(i)
                    
                    #Look up the actual number this button represents
                    typed_digit = digit_map[i]
                    entered_otp.append(typed_digit) 
                    print("Typed:", typed_digit)
                    
                    #Debounce loop
                    while buttons[i].value() == 0:
                        time.sleep(0.01) 
                    
                    if len(entered_otp) == 4:
                        if entered_otp == target_otp:
                            success_effect()
                            open_locker()
                            time.sleep(10) 
                            close_locker()
                            
                            entered_otp = [] 
                            wrong_attempts = 0 
                            active_mode = 0 
                            print("System Idle. Waiting for App command...")
                            
                        else:
                            wrong_effect()
                            wrong_attempts += 1
                            entered_otp = [] 
                            
                            if wrong_attempts >= 3:
                                print("SYSTEM LOCKED! 3 Wrong Attempts.")
                                is_locked = True
                                active_mode = 0 
                                print("System Idle. Requires App to reset.")
    #==========================================================================================
    
    #==========================================================================================
    #GATEWAY 2 HARDWARE (Ultrasonic Sensor + Math)
    
    elif active_mode == 2:
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
                steady_count = 0 #Hand is actually moving, reset timer
                
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
            
    time.sleep(0.05) #Main loop delay for stability
    #==========================================================================================

#Thank you Nayan, we love ODT <3
#We had an absolute BLAST while doing this project, thanks to you!
#Charvi and Avantika - Section A
#========================================================================================================================
