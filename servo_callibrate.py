import pigpio
import json
from tkinter import *

root = Tk()

servo_pins = [
    25,
    8,
    7,
    16,
    20,
    21,
]
angle = 0
l = 0

pi = pigpio.pi()

callibration = []

def map(val, min_start, max_start, min_finish, max_finish):
    return ((val - min_start) / (max_start - min_start)) * (max_finish - min_finish) + min_finish
    
def key_press(event):
    global angle, callibration, l, loop
    
    if 'Left' == event.keysym:
        angle -= 1
    elif 'Right' == event.keysym:
        angle += 1
    elif 'Up' == event.keysym:
        angle += 45
    elif 'Down' == event.keysym:
        angle -= 45
    elif 'w' == event.keysym:
        callibration.append(angle)
        l += 1
        angle = 0
    elif 's' == event.keysym:
        callibration = callibration[:-1]
        l -= 1
        angle = 0
    elif 'Escape' == event.keysym:
        loop = False
        
    
root.bind('<KeyPress>', key_press)
    
loop = True
        
while loop:
    if l >= len(servo_pins):
        with open('servo_offsets.json', 'w') as file:
            json_object = json.dumps(callibration)
            file.write(json_object)
            
        quit()
    try:
        pi.set_servo_pulsewidth(servo_pins[l], map(angle, 0, 180, 500, 2500))
    except:
        pass
        
    root.update()
    print(angle)
    
with open('servo_offsets.json', 'w') as file:
    json.dump(callibration, file)
