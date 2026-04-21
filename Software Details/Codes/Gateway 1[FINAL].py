#Gateway 1 wherein user generates random OTP and enters it into the locker through a custom made keypad (10 pushbuttons).
#User gets 3 tries to enter the correct code, if not, the code breaks.
#==========================================================================================
#IMPORT MODULES

from machine import Pin, PWM
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

char = (char_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY)  #Data can be both written, read and then notified (pushed) to the app
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
        if value_handle == char_handle:     #reading the Value written on characteristics by Phone/client
            raw_msg = ble.gatts_read(char_handle).rstrip(b'\x00')
            value = raw_msg.decode().strip()
            print("Bluetooth Received:", value)

def advertise(device_name):
    name_bytes = device_name.encode()
    flags = bytearray([0x02, 0x01, 0x06])
    short_name = bytearray([len(name_bytes) + 1, 0x08]) + name_bytes   #These lines construct a "payload packet" out of raw bytes, so phones can read the device's name ("Chika") before connecting.
    full_name = bytearray([len(name_bytes) + 1, 0x09]) + name_bytes
    adv_data = flags + short_name + full_name
    ble.gap_advertise(50, adv_data=adv_data)   #Starts the actual broadcasting, sending out a signal every 50 milliseconds.
    print("Awating Connection... Advertising as:", device_name)

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
# before gpio 35, we had gpio 26, we made 35 work by adding an external "PullUp" resistor using Nayan's brilliant teachings.
# 10k ohm resistor was attached externally (we had to resort to this coz of lack of gpios)
button_pins = [15, 4, 5, 18, 19, 21, 22, 23, 25, 35]    #usage of lists to shorten initialisation code, big brain
buttons = [Pin(p, Pin.IN, Pin.PULL_UP) for p in button_pins]

#Servo Motor
servo = PWM(Pin(13), freq=50)
S_CLOSED = 40   #0 degrees - start position
S_OPEN = 115    #180 degrees - end position
servo.duty(S_CLOSED) 
#==========================================================================================

#==========================================================================================
#SYSTEM VARIABLES

active_mode = 0 # 0 = Idle, 1 = Gateway 1 (OTP Mode) #code starts idle

target_otp = []  #otp to match
entered_otp = []  #otp entered by user   
wrong_attempts = 0  #used for 3 wrong attempt condition (incremented later)   
is_locked = False          

#translatation of the list index to the physical button label
digit_map = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]
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

#correct scenario (buzzer, neopixel - green)
def success_effect():
    print("Access Granted!")
    buzzer.duty(512)
    for freq in [1000, 1500, 2000]:
        buzzer.freq(freq)
        time.sleep(0.1)
    buzzer.duty(0)
    
    for i in range(0,16):
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
    
    if value: 
        
        #Gateway 1 ('5')
        if value == '5':
            OTP = random.randint(1000, 9999)   #generates a random 4 digit number
            print("Generated OTP:", OTP)
            
            #Convert string OTP to a list of integers [e.g., 4, 8, 2, 1]
            target_otp = [int(d) for d in str(OTP)] 
            
            #Send back to App
            ble.gatts_write(char_handle, "A" + str(OTP))   #Writes the new OTP string into the Characteristic's memory on the ESP32 (GATT language)
            if conn_handle is not None:     #if phone is not disconnected i.e if it is connected...
                ble.gatts_notify(conn_handle, char_handle)    #...it "pushes" the new OTP directly to the phone via the NOTIFY flag we set up earlier
                
            active_mode = 1
            is_locked = False
            wrong_attempts = 0
            entered_otp = []
            value = "" 
            print("System Switched to Gateway 1. Enter code on physical buttons.")

        else:
            value = ""

    
    #(Physical Pushbuttons)
   
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
                            
    time.sleep(0.05)
#==========================================================================================
