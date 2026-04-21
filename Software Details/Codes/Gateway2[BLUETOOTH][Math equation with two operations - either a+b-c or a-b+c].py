#Gateway 2 (math equation) bluetooth at the end with either a+b-c or a-b+c type equations [2 operations]
#Code to send value to ESP
from machine import Pin
import bluetooth
import time
import random

conn_handle = None #global variable to check whether phone is currently connected. None means disconnected 
value = "" #Empty string variable 
name = "Chika" #Name of ESP32 
ble = bluetooth.BLE() #Initializes bluetooth hardware on ESP32

ble.active(False) #This turns the Bluetooth radio off, waits half a second, and turns it back on, ensuring it starts in a reset state
time.sleep(0.5)
ble.active(True)
ble.config(gap_name=name)

service_UUID = bluetooth.UUID("6e400001-b5a3-f393-e0a9-e50e24dcca9e")
char_UUID = bluetooth.UUID("6e400002-b5a3-f393-e0a9-e50e24dcca9e")

char = (char_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY) #Data can be both written, read and then notified (pushed) to the app
service = (service_UUID, (char,),)
((char_handle,),) = ble.gatts_register_services((service,))

def event_occured(event, data):
    
    global conn_handle 

    if event == 1: #Event 1 means a device (your phone) just connected. It saves the connection ID to conn_handle
        conn_handle = data[0]
        print("Connected")
        
    elif event == 2: #Event 2 means the phone disconnected. It resets conn_handle to None.
        print("Disconnected")
        advertise(name) #Advertise() function so the ESP32 becomes discoverable again.
        
    elif event == 3:
        conn_handle, value_handle = data
        if value_handle == char_handle: #reading the Value written on characteristics by Phone/client
            raw_msg = ble.gatts_read(char_handle).rstrip(b'\x00')
            msg = raw_msg.decode().strip()
            print("Received:", msg)
                
            global value
            value = msg
            

def advertise(device_name):
    
    name_bytes = device_name.encode()

    flags = bytearray([0x02, 0x01, 0x06])
    short_name = bytearray([len(name_bytes) + 1, 0x08]) + name_bytes #These lines construct a "payload packet" out of raw bytes, so phones can read the device's name ("Chika") before connecting.
    full_name = bytearray([len(name_bytes) + 1, 0x09]) + name_bytes
    adv_data = flags + short_name + full_name

    ble.gap_advertise(50, adv_data=adv_data) #Starts the actual broadcasting, sending out a signal every 50 milliseconds.
    print("Awating Connection...Advertising as:", device_name)

advertise(name)
ble.irq(event_occured)

list1=['3','4','1','2']
list2=[]

#We need a variable to store the answer so the Ultrasonic sensor can check it later
target_distance = 0 

while True:
    if value == '1':
        list2.append(value)
        value = ""
        print(list2)
        time.sleep(0.5)    
    elif value == '2':
        list2.append(value)
        value = ""
        print(list2)
        time.sleep(0.5)
    elif value == '3':
        list2.append(value)
        value = ""
        print(list2)
        time.sleep(0.5)
    elif value == '4':
        list2.append(value)
        value = ""
        time.sleep(0.5)
        print(list2)
        time.sleep(2)
        
    if list2==list1: #if the buttons are pressed in right sequence
        print('yay')
        time.sleep(10)
        list2 = [] # Reset list after success
        
    elif value == '5':
        OTP = random.randint(1000, 9999) #generates a random 4 digit number
        print("Generated OTP:", OTP)
        value = ""
        ble.gatts_write(char_handle, str(OTP))  #Writes the new OTP string into the Characteristic's memory on the ESP32 (GATT language)
        if conn_handle is not None: #if phone is not disconnected i.e if it is connected...
            ble.gatts_notify(conn_handle, char_handle) #...it "pushes" the new OTP directly to the phone via the NOTIFY flag we set up earlier
        time.sleep(0.1)

#========================================================================================================================
    #NEW: GATEWAY 2 [My part]
    elif value == '6':
        #Picking the answer first (between 10 and 15)
        target_distance = random.randint(10, 15)     #for example, 12
        
        #Randomly choosing the pattern: A + B - C or A - B + C
        pattern = random.choice(['+-', '-+'])
        
        if pattern == '+-':
            #Pattern: num1 + num2 - num3 = target_distance
            num3 = random.randint(1, 9)              #Pick a random number to subtract, for example 8 = num3
            subtotal = target_distance + num3        #subtotal = 12+8 = 20
            num1 = random.randint(1, subtotal - 1)   #(1,19) = lets say, 15 = num1
            num2 = subtotal - num1                   #num2 = 20-15 = 5            
            equation_str = str(num1) + " + " + str(num2) + " - " + str(num3) + " = ?" #15+5-8 = ? (12!)
            
        else:
            # Pattern: num1 - num2 + num3 = target_distance
            num3 = random.randint(1, 9)              # Pick a random number to add, for example 6 = num3
            subtotal = target_distance - num3        #subtotal = 12-6 = 6
            num2 = random.randint(1, 9)              #Pick a random number to subtract, for example 3 = num2
            num1 = subtotal + num2                   #6+3 = 9
            equation_str = str(num1) + " - " + str(num2) + " + " + str(num3) + " = ?"  #9-3+6=? (12!) [BODMAS - addition & subtraction have equal priority, solve from left to right]
            
        print("Generated Equation:", equation_str, "| Target Distance:", target_distance, "cm")
        value = ""
        
        #Sending the equation string to the phone
        ble.gatts_write(char_handle, equation_str)  
        if conn_handle is not None: 
            ble.gatts_notify(conn_handle, char_handle) 
        time.sleep(0.1)
#========================================================================================================================


