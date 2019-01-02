import urequests
import webrepl
import machine
import network
import time
import json

print("Starting up...")

wlan = network.WLAN(network.STA_IF)
ap = network.WLAN(network.AP_IF)
ap.active(False)
wlan.active(True)
wlan.connect('linksys wrt54g', 'welcometo2000')
for i in range(1000):
    if wlan.isconnected():
        break
    time.sleep(1)

print("Network config:")
print(wlan.ifconfig())
webrepl.start()
print("Entering main loop.")
time.sleep(2)

pins = [machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP),
        machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP),
        machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
]
states = [0,0,0]

while True:
    for i in range(len(pins)):
        current_state = pins[i].value()
        if current_state != states[i]:
            states[i] = current_state
            print("Pin {} went {}".format(i, "high" if current_state else "low"))
            urequests.post("https://coldbrew.magevent.net/api/tapstate", json={"pin": i, "state": current_state})
