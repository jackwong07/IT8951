
from time import sleep
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from gpiozero import Button
from bus_functions import *

# API for Bus Times
API_KEY = 'c148cb26-1a9a-4073-abc7-70b21c262f96'
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

def main():

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

    BUTTON_PIN = 5
    current_screen = 0
    total_screens = 3
    is_refreshing = False # flag so it prevents button spam during slow 3-ink updates
    
    button = Button(BUTTON_PIN, pull_up=True)



    display_bus_template (display)
    sleep(1)
    
    num = 0
    while (True):
        display_bus_times (broadway_ns_url, display, x_shift = 40, y_shift = 300, num_buses = 4)
        display_bus_times (broadway_ew_url, display, x_shift = 40, y_shift = 1100, num_buses = 2)        
        display_citibike_times(citibike_url, display, station_id, x_shift = 1500, y_shift = 300)        
        sleep(5)
        num +=1
        if num>1:
            break     
        sleep(60 - (int(now.timestamp()) % 60))
    print('Done!')




if __name__ == '__main__':
    main()
