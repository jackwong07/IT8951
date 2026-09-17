'''
This file contains various functions to test different aspects
of the module's display capabilities. Each function takes only
an AutoDisplay object (or, probably, an object of a type derived
from that class) as an argument, so they can be used with either
an actual AutoEPDDisplay, or a VirtualEPDDisplay, or something else.

See test.py for an example.
'''

# functions defined in this file
__all__ = [
    'print_system_info',
    'clear_display',
    'display_gradient',
    'display_image_8bpp',
    'partial_update',
    'display_bus_times'
]

from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from sys import path
path += ['../../']
from IT8951 import constants



def print_system_info(display):
    epd = display.epd

    print('System info:')
    print('  display size: {}x{}'.format(epd.width, epd.height))
    print('  img buffer address: {:X}'.format(epd.img_buf_address))
    print('  firmware version: {}'.format(epd.firmware_version))
    print('  LUT version: {}'.format(epd.lut_version))
    print()

def clear_display(display):
    print('Clearing display...')
    display.clear()

def display_gradient(display):
    print('Displaying gradient...')

    # set frame buffer to gradient
    for i in range(16):
        color = i*0x10
        box = (
            i*display.width//16,      # xmin
            0,                        # ymin
            (i+1)*display.width//16,  # xmax
            display.height            # ymax
        )

        display.frame_buf.paste(color, box=box)

    # update display
    display.draw_full(constants.DisplayModes.GC16)

    # then add some black and white bars on top of it, to test updating with DU on top of GC16
    box = (0, display.height//5, display.width, 2*display.height//5)
    display.frame_buf.paste(0x00, box=box)

    box = (0, 3*display.height//5, display.width, 4*display.height//5)
    display.frame_buf.paste(0xF0, box=box)

    display.draw_partial(constants.DisplayModes.DU)

def display_image_8bpp(display):
    img_path = '/home/jackwong07/Desktop/IT8951/test/integration/images/astoria_map.PNG'
    print('Displaying "{}"...'.format(img_path))

    # clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    img = Image.open(img_path)

    # TODO: this should be built-in
    # Coordinates for Box are where the Top Left Corner is
    dims = (display.width, display.height)
    
    # thumbnail defines the max size of image. It will keep aspect ratio. It will print the current image size if the dims are larger
    img.thumbnail(dims)
    # paste_coords = (0,0) # PIL image.paste pastes based off the top left of the image
    paste_coords = [round(dims[i]/2) - round(img.size[i]/2) for i in (0,1)] # align image to middle
    # paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
    display.frame_buf.paste(img, paste_coords)

    display.draw_full(constants.DisplayModes.GC16)

def partial_update(display):
    print('Starting partial update...')

    # clear image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    print('  writing full...')
    _place_text(display.frame_buf, 'partial', x_offset=-display.width//4)
    display.draw_full(constants.DisplayModes.GC16)

    # TODO: should use 1bpp for partial text update
    print('  writing partial...')
    _place_text(display.frame_buf, 'update', x_offset=+display.width//4)
    display.draw_partial(constants.DisplayModes.DU)



def find_values_by_key (data, target_key):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                yield value
            # Recursively check the value if it's a nested dict or list
            yield from find_values_by_key(value, target_key)
    elif isinstance(data, list):
        for item in data:
            yield from find_values_by_key(item, target_key)

def convert_timedelta (duration):
    days, seconds = duration.days, duration.seconds
    hours = duration.days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = duration.seconds % 60
    minutes_full = hours * 60 + minutes
    return hours, minutes, seconds, minutes_full

# Function calls bus api and displays bus arrivals
def display_bus_times (broadway_ns_url, display):
    print ("Displaying Bus Times")

    now = datetime.now(ZoneInfo("America/New_York"))

    response_ns = requests.get(broadway_ns_url)
    data_object_ns = response_ns.json()
    all_buses_ns = list(find_values_by_key(data_object_ns,"LineRef"))
    all_expectedtimes_ns = list(find_values_by_key(data_object_ns,"ExpectedArrivalTime"))
    # Creating bus dictionary that combines buses and arrival times
    bus_dict_ns = {}
    for all_buses_ns, all_expectedtimes_ns in zip(all_buses_ns, all_expectedtimes_ns):
        # If key doesn't exist, set it to [] first, then append the value
        bus_dict_ns.setdefault(all_buses_ns, []).append(all_expectedtimes_ns)

    # Display BUS 1 from NS
    bus_q100 = "MTABC_Q100"
                        
    print(now)
    print(bus_dict_ns)
    
    _place_text(display.frame_buf, f"{bus_q100} to F Train: 5 minute walk", fontsize=40)
    display.draw_partial(constants.DisplayModes.DU)

    try:
        # bus_draw.rectangle((0, 14, 250, 28), fill = 255)
        arrivaltime = datetime.fromisoformat(bus_dict_ns[bus_q100][0])
        difference = arrivaltime - now
        print(difference)
        hours, minutes, seconds, minutes_full = convert_timedelta(difference)
        _place_text(display.frame_buf, f"1. {minutes_full} minute, {seconds} seconds", y_offset=50, fontsize=40)
        display.draw_partial(constants.DisplayModes.DU)
    except IndexError:
        pass     
    
    
    
    
    
    
# this function is just a helper for the others
def _place_text(img, text, x_offset=0, y_offset=0, fontsize=80):
    '''
    Put some centered text at a location on the image.
    '''
    fontsize = fontsize

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    img_width, img_height = img.size
    text_width = font.getlength(text)
    text_height = fontsize

    # draw_x = (img_width - text_width)//2 + x_offset # Centers text in middle of display
    draw_x = x_offset
    # draw_y = (img_height - text_height)//2 + y_offset # Centers text in middle of display
    draw_y = text_height//2 + y_offset

    draw.text((draw_x, draw_y), text, font=font)