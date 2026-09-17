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
    'display_bus_template',
    'display_bus_times',
    'display_citibike_times',
    'display_map'
]

from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from sys import path
path += ['../../']
from IT8951 import constants

Y_SPACING = 150
MED_FONT_SIZE = 60
BIG_FONT_SIZE = 125


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


def _resize_to_fill(image_path, screen_width, screen_height):
    img = Image.open(image_path)
    img_width, img_height = img.size
    
    # Calculate scale ratios for width and height
    ratio_w = screen_width / img_width
    ratio_h = screen_height / img_height
    
    # Use the larger ratio so the image completely fills the screen
    scale = max(ratio_w, ratio_h)
    
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    
    # Resize the image
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Optional: Center crop to exact screen dimensions
    left = (new_width - screen_width) / 2
    top = (new_height - screen_height) / 2
    right = left + screen_width
    bottom = top + screen_height
    
    cropped = resized.crop((left, top, right, bottom))
    return cropped

def display_map(display):
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))
    dims = (display.width, display.height)
    
    # For the Map
    map_img_path = '/home/jackwong07/Desktop/IT8951/test/integration/images/astoria_edited.jpg'
    map_img = Image.open(map_img_path)

    resized_map_img = _resize_to_fill(map_img_path, round(display.width), round(display.height*7/8))
    map_paste_coords = [round(dims[i]/2) - round(resized_map_img.size[i]/2) for i in (0,1)]
    display.frame_buf.paste(resized_map_img, map_paste_coords)   
    
    display.draw_full(constants.DisplayModes.GC16)

    
def display_bus_template(display):

    now = datetime.now(ZoneInfo("America/New_York"))
    dims = (display.width, display.height)

    # Clearing image to white
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))
    time.sleep(2)
    
    # Set image files, reduce to thumbnail as max size, set where to paste image, paste
    mta_bus_img_path = '/home/jackwong07/Desktop/IT8951/test/integration/images/mta_bus.png'
    mta_bus_img = Image.open(mta_bus_img_path)
    max_bus_size = (1000, 500)    
    mta_bus_img.thumbnail(max_bus_size)
    mta_bus_paste_coords = [dims[i] - mta_bus_img.size[i] for i in (0,1)]  # align image with bottom of display   
    display.frame_buf.paste(mta_bus_img, mta_bus_paste_coords)
    
    # Paste in image graphics
    # mta_logo_paste_coords = (0,0) # PIL image.paste pastes based off the top left of the image
    # paste_coords = [round(dims[i]/2) - round(img.size[i]/2) for i in (0,1)] # align image to middle

    # For the Bus Times section - the background box and text
    display.frame_buf.paste(0x37, box=(25, 150, 750, 250))
    _place_text(display.frame_buf, "21/Broadway", x_offset=100, y_offset=175, fontsize=MED_FONT_SIZE, color="#FFFFFF")
    
    display.frame_buf.paste(0x37, box=(25, 950, 750, 1050))
    _place_text(display.frame_buf, "Broadway/21", x_offset=100, y_offset=975, fontsize=MED_FONT_SIZE, color="#FFFFFF")
    
     
    # For Citibike section - the background box, the Normal and eBikes text    
    display.frame_buf.paste(0x37, box=(925, 150, 1750, 250))
    _place_text(display.frame_buf, "Citibike - 21 St / 34 Ave", x_offset= 1000, y_offset=175, fontsize=MED_FONT_SIZE, color="#FFFFFF")
    _place_text (display.frame_buf, "Normal Bikes", x_offset=1000, y_offset=350, fontsize=MED_FONT_SIZE)
    _place_text (display.frame_buf, "E-Bikes", x_offset=1000, y_offset=475, fontsize=MED_FONT_SIZE)
    
    # Background for the headline box
    display.frame_buf.paste(0x37, box=(0, 0, display.width, 125))

    # Write Header Text
    _place_text(display.frame_buf, f"Bus Wait Times ...... {now.date()}", x_offset= 20, y_offset=25, fontsize=MED_FONT_SIZE, color="#FFFFFF")

    # Display draw. GC16 means it's using grayscale
    display.draw_full(constants.DisplayModes.GC16)





# Function calls bus api and displays bus arrivals
def display_bus_times(url, display, x_shift, y_shift, num_buses):
    now = datetime.now(ZoneInfo("America/New_York"))
    # bus_dict = bus_dictionary(url)
    bus_list = _create_bus_list(url)

    list_index = 0
    for bus in bus_list:

        print (f"Process {bus["Line Name"]}")
        arrivaltime = datetime.fromisoformat(bus["Arrival Time"])
        difference = arrivaltime - now
        hours, minutes, seconds, minutes_full = _convert_timedelta(difference) 

        # Text to write
        bus_name_text = (f"{bus["Line Name"]}")
        bus_minute_text = (f"{minutes_full} m")
        
        # Clear text for Bus Name and Bus Minute
        _clear_text (display.frame_buf, bus_name_text, x_offset=x_shift, y_offset=y_shift + list_index * Y_SPACING, fontsize=BIG_FONT_SIZE, color="black")
        _clear_text (display.frame_buf, bus_minute_text, x_offset=x_shift + 500, y_offset=y_shift + list_index * Y_SPACING, fontsize=BIG_FONT_SIZE)
        
        time.sleep(1)

        # Place text
        _place_text (display.frame_buf, bus_name_text, x_offset=x_shift, y_offset=y_shift + list_index * Y_SPACING, fontsize=BIG_FONT_SIZE, color="white")
        _place_text (display.frame_buf, bus_minute_text, x_offset=x_shift + 500, y_offset=y_shift + list_index * Y_SPACING, fontsize=BIG_FONT_SIZE)
        
        # Refresh the changed area
        display.draw_partial(constants.DisplayModes.DU)
        list_index += 1
        print(f"Ran through For {list_index}")
        if list_index > num_buses-1:
            break



def display_citibike_times(url, display, station_id, x_shift, y_shift):
    response = requests.get(url)
    data_object = response.json()
    
    for station in data_object['data']['stations']:
        if station['station_id'] == station_id:
            bikes_available = station['num_bikes_available']
            ebikes_available = station['num_ebikes_available']
            normal_available = bikes_available - ebikes_available
        else:
            pass
    
    try:
        normal_available_text = str(normal_available)
        ebikes_available_text = str(ebikes_available)
        _clear_text (display.frame_buf, normal_available_text, x_offset=x_shift, y_offset=300, fontsize=BIG_FONT_SIZE)
        _place_text (display.frame_buf, normal_available_text, x_offset=x_shift, y_offset=300, fontsize=BIG_FONT_SIZE)

        _clear_text (display.frame_buf, ebikes_available_text, x_offset=x_shift, y_offset=450, fontsize=BIG_FONT_SIZE)
        _place_text (display.frame_buf, ebikes_available_text, x_offset=x_shift, y_offset=450, fontsize=BIG_FONT_SIZE)
    except ValueError:
        pass
    
    display.draw_partial(constants.DisplayModes.DU)
    
            

def _clear_text(img, text, x_offset=0, y_offset=0, fontsize=80, color="white"):
    '''
    Function to clear the space. Need to give time between this and the _place_text function
    '''
    fontsize = fontsize
    text = text
    text_position = (x_offset, y_offset)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    # Bounding box of the text. Returns a tuple of (left, top, right, bottom)
    bbox = draw.textbbox(text_position, text, font=font)
    
    #Extra space around the text
    padding = 10
    right_padding = 100
    rect_coords = (
        bbox[0] - padding,  # Left
        bbox[1] - padding,  # Top
        bbox[2] + right_padding,  # Right
        bbox[3] + padding,  # Bottom
    )
    
    draw.rectangle(rect_coords, fill=color)
    
    
# this function is just a helper for the others
def _place_text(img, text, x_offset=0, y_offset=0, fontsize=80, color="#000000"):
    '''
    Type text. Based on the text's center
    '''
    fontsize = fontsize
    text = text
    text_position = (x_offset, y_offset)

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', fontsize)
    except OSError:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSans.ttf', fontsize)

    # Bounding box of the text. Returns a tuple of (left, top, right, bottom)
    bbox = draw.textbbox(text_position, text, font=font)
    
    draw.text(bbox, text, font=font, fill=color)


def _convert_timedelta (duration):
    days, seconds = duration.days, duration.seconds
    hours = duration.days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = duration.seconds % 60
    minutes_full = hours * 60 + minutes
    return hours, minutes, seconds, minutes_full


# Create bus list 
def _create_bus_list (url):
    now = datetime.now(ZoneInfo("America/New_York"))
    response = requests.get(url)
    data_object = response.json()
    monitored_stops = (
        data_object ["Siri"]
        ["ServiceDelivery"]
        ["StopMonitoringDelivery"]
    )
    
    bus_list = []
    
    for stop in monitored_stops:
        for visit in stop.get("MonitoredStopVisit", []):

            journey = visit.get("MonitoredVehicleJourney", {})

            # Get the bus route name.
            line_name = journey.get("PublishedLineName")

            # Get the destination.
            destination = journey.get("DestinationName")

            # ExpectedArrivalTime is inside MonitoredCall.
            monitored_call = journey.get("MonitoredCall", {})

            arrival_time = monitored_call.get("ExpectedArrivalTime")

            # Some MTA records may not have an ExpectedArrivalTime.
            # Ignore those records rather than causing an error.
            if not arrival_time:
                continue

            # Ignore records missing the other fields we need.
            if not line_name or not destination:
                continue

            # Add the information to our output list.
            bus_list.append({
                "Line Name": line_name,
                "Destination": destination,
                "Arrival Time": arrival_time
            })
    
    # Sort the list chronologically using the ISO 8601
    # arrival timestamp.
    bus_list.sort(
        key=lambda bus: datetime.fromisoformat(
            bus["Arrival Time"]
        )
    )
    return bus_list    