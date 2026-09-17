
from time import sleep
import time
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from gpiozero import Button
from bus_functions import *

# API for Bus Times
API_KEY = API
STOP_MONITORING_URL = 'https://bustime-classic.mta.info/api/siri/stop-monitoring.json'
broadway_ns = 550685
broadway_ew = 552169
broadway_ns_url = "{}?key={}&OperatorRef=MTA&MonitoringRef={}".format(STOP_MONITORING_URL, API_KEY, broadway_ns)
broadway_ew_url = "{}?key={}&OperatorRef=MTA&MonitoringRef={}".format(STOP_MONITORING_URL, API_KEY, broadway_ew)

# API for Citibike
citibike_url = 'https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json'
station_id = "0fa27bd7-b182-4e7a-b5bb-90f4249cb368"

now = datetime.now(ZoneInfo("America/New_York"))        


def parse_args():
    p = argparse.ArgumentParser(description='Test EPD functionality')
    p.add_argument('-v', '--virtual', action='store_true',
                   help='display using a Tkinter window instead of the '
                        'actual e-paper device (for testing without a '
                        'physical device)')
    p.add_argument('-r', '--rotate', default=None, choices=['CW', 'CCW', 'flip'],
                   help='run the tests with the display rotated by the specified value')
    p.add_argument('-m', '--mirror', action='store_false',
                   help='Mirror the display (use this if text appears backwards)')
    return p.parse_args()

args = parse_args()

if not args.virtual:
    from IT8951.display import AutoEPDDisplay

    print('Initializing EPD...')

    # here, spi_hz controls the rate of data transfer to the device, so a higher
    # value means faster display refreshes. the documentation for the IT8951 device
    # says the max is 24 MHz (24000000), but my device seems to still work as high as
    # 80 MHz (80000000)
    display = AutoEPDDisplay(vcom=-2.15, rotate=args.rotate, mirror=args.mirror, spi_hz=24000000)

    print('VCOM set to', display.epd.get_vcom())

else:
    from IT8951.display import VirtualEPDDisplay
    display = VirtualEPDDisplay(dims=(1872, 1404), rotate=args.rotate, mirror=args.mirror)

BUTTON_PIN = 26
current_screen = 0
total_screens = 2
# is_refreshing = False # flag so it prevents button spam during slow E-ink updates

button = Button(BUTTON_PIN, pull_up=True)

def draw_screen_0():
    display_bus_template (display)
    sleep(1)

    display_bus_times (broadway_ns_url, display, x_shift = 40, y_shift = 300, num_buses = 4)
    display_bus_times (broadway_ew_url, display, x_shift = 40, y_shift = 1100, num_buses = 2)        
    display_citibike_times(citibike_url, display, station_id, x_shift = 1500, y_shift = 300)        
    print('Done with bus draw')    

def update_screen_0():
    display_bus_times (broadway_ns_url, display, x_shift = 40, y_shift = 300, num_buses = 4)
    display_bus_times (broadway_ew_url, display, x_shift = 40, y_shift = 1100, num_buses = 2)        
    display_citibike_times(citibike_url, display, station_id, x_shift = 1500, y_shift = 300) 
    print ('Update bus')    

def draw_screen_1():
    display_map(display)
    sleep(1)
    print('Done with map draw')

SCREEN_MAP = {
    0: draw_screen_0,
    1: draw_screen_1
}

def refresh_current_screen():
    global is_refreshing
    
    is_refreshing = True
    print(f"Refreshing screen to {current_screen +1}")
    if current_screen == 0:
        draw_screen_0()
    elif current_screen == 1:
        draw_screen_1()
        
    is_refreshing = False


def on_button_press():
    global current_screen, is_refreshing

    if is_refreshing:
        print ("Refreshing, ignoring button")
        return

    current_screen = (current_screen + 1) % total_screens
    print (f"Button pressed, switching to {current_screen}")

    refresh_current_screen()


if __name__ == '__main__':
    print("Starting Program. Loading first screen")
    refresh_current_screen() # show first screen
    
    # listen to when button is pressed and then run on button press
    button.when_pressed = on_button_press
    print ("Ready to press button on GPIO 5 to cycle screens")
    
    last_api_update = time.time()
    
    while True:
        # look at now
        current_time = time.time()
        
        if current_time - last_api_update >= 60:
            
            #only refresh if on screen_0
            if current_screen == 0 and not is_refreshing:
                print ("60 seconds elapsed. Auto-updating dashboard")
                update_screen_0()
            
            last_api_update = current_time
    
    sleep(0.2)
    
