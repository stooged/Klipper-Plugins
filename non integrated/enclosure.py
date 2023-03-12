#!/usr/bin/python

import sys
import time
import datetime
import adafruit_dht            #  adafruit-circuitpython-dht 
import RPi.GPIO as GPIO        #  RPi.GPIO
from RPLCD.i2c import CharLCD  #  RPLCD
import websocket               #  websocket-client
from pathlib import Path
import configparser
import json
try:
    import thread
except ImportError:
    import _thread as thread



printing = False
progress = 0
lcd_display = None
gfilename = None


cfg_file = Path("/home/pi/printer_data/config/enclosure.cfg")
if cfg_file.is_file():
    config = configparser.ConfigParser()
    config.read("/home/pi/printer_data/config/enclosure.cfg")
    fan_relay_gpio = config.getint("enclosure", "fan_relay_gpio", fallback=17)
    dht_sensor_gpio = config.getint("enclosure", "dht_sensor_gpio", fallback=4)
    dht_sensor_type = config.getint("enclosure", "dht_sensor_type", fallback=11)
    is_20x4_lcd = config.getboolean("enclosure", "is_20x4_lcd", fallback=True)
    temp_on = config.getint("enclosure", "temp_on", fallback=26)
    temp_off = config.getint("enclosure", "temp_off", fallback=20)
    machine_name = config.get("enclosure", "machine_name")


else:                         #hard codeed values used if enclosure.cfg is missing
    fan_relay_gpio = 17                  # gpio used for fan relay
    dht_sensor_gpio = 4                  # gpio used for dht sensor
    dht_sensor_type = 11                 # dht sensor type   11, 12, 21, 22
    is_20x4_lcd = True                   # define if lcd is 20x4, if False 16x2 is used
    temp_on = 26                         # temperature in °C to turn extraction fan on
    temp_off = 20                        # temperature in °C to turn extraction fan off
    machine_name = "Printer"             # printer name used for display


dht_sensor = adafruit_dht.DHT11(self.dht_sensor_gpio)
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(fan_relay_gpio, GPIO.OUT)


try:
    if is_20x4_lcd:
        lcd_display = CharLCD(i2c_expander="PCF8574", address=0x27, cols=20, rows=4, backlight_enabled=True, charmap="A00")
        if lcd_display is not None:
            lcd_display.clear()
            machine_name = machine_name[0:20]
            lcd_display.cursor_pos = (1, int((20 - len(machine_name)) / 2))
            lcd_display.write_string(machine_name)
            lcd_display.cursor_pos = (2, 5)
            lcd_display.write_string("Loading...")
    else:
        lcd_display = CharLCD(i2c_expander="PCF8574", address=0x27, cols=16, rows=2, backlight_enabled=True, charmap="A00")
        if lcd_display is not None:
            lcd_display.clear()
            machine_name = machine_name[0:16]
            lcd_display.cursor_pos = (0, int((16 - len(machine_name)) / 2))
            lcd_display.write_string(machine_name)
            lcd_display.cursor_pos = (1, 0)
            lcd_display.write_string("   Loading...   ")
except Exception as e:
    lcd_display = None
    pass


def subscribe():
    return {
        "jsonrpc": "2.0",
        "method": "printer.objects.subscribe",
        "params": {
            "objects": {
                "print_stats": ["filename", "state"],
                "configfile": ["config"],
                "display_status": ["progress"],
            }
        },
        "id": "8337"
    }


def parse_json(json_obj, message):
    global printing
    global machine_name
    global gfilename
    global progress

    if "print_stats" in json_obj:
        print_stats = json_obj["print_stats"]
        if "filename" in print_stats:
            gfilename = print_stats["filename"]  
        if "state" in print_stats:
            state = print_stats["state"]
            if state == "printing" and printing == False:
                printing = True
                progress = 0
            if state == "complete" or state == "error":
                printing = False
                progress = 0
            if state == "cancelled":
                printing = False
                progress = 0        
    if "display_status" in json_obj and printing == True:
        json_prog1 = json_obj["display_status"]["progress"]
        json_prog = json_prog1*100
        progress = int(json_prog)




def on_message(ws, message):
   
    if "notify_klippy_ready" in message:
        ws.send(json.dumps(subscribe()))
    if "Klipper state: Ready" in message:
        ws.send(json.dumps(subscribe()))
    if "jsonrpc" in message:
        python_json_obj = json.loads(message)
        if "result" in python_json_obj and "status" in python_json_obj["result"]:
             parse_json(python_json_obj["result"]["status"], message)
        if "method" in python_json_obj and python_json_obj["method"] == "notify_status_update":
             parse_json(python_json_obj["params"][0], message)
        if "result" in python_json_obj and "value" in python_json_obj["result"]:    
             parse_json(python_json_obj["result"]["value"], message)
             
             
            

def on_error(ws, error):
    print("Error: " + str(error))


def on_close(ws):
    time.sleep(10)
    connect_websocket() 


def on_open(ws):
    def run(*args):
        for i in range(1):
            time.sleep(1)
            ws.send(json.dumps(subscribe()))
        time.sleep(5)
    thread.start_new_thread(run, ())


def connect_websocket():
    def run(*args):
            ws = websocket.WebSocketApp(f"ws://127.0.0.1:7125/websocket", on_message=on_message, on_error=on_error, on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
    thread.start_new_thread(run, ())


time.sleep(30) 
connect_websocket()


while True:

    try:
        time.sleep(3)
        if lcd_display is not None:

            temperature = dht_sensor.temperature
            humidity = dht_sensor.humidity
            
            if humidity != None and temperature != None:
                if int(temperature) >= int(temp_on) and printing == True:
                    GPIO.output(fan_relay_gpio, GPIO.HIGH)
                elif int(temperature) <= int(temp_off) or printing == False:
                    GPIO.output(fan_relay_gpio, GPIO.LOW)
                    
                if is_20x4_lcd:
                
                    enctemp = str(int(temperature)) + "C"
                    enchum = str(int(humidity)) + "%"
                    prgss = str(int(progress)) + "%"

                    if printing == True:
                        lcd_display.cursor_pos = (0, 0)
                        lcd_display.write_string("Printing: ")
                        lcd_display.cursor_pos = (0, 10)
                        lcd_display.write_string(chr(32) * (10 - len(prgss)))
                        lcd_display.cursor_pos = (0, 10)
                        lcd_display.write_string(prgss)
                        lcd_display.cursor_pos = (1, 0)
                        lcd_display.write_string("Enclosure Temp:")
                        lcd_display.cursor_pos = (1, 15)
                        lcd_display.write_string(chr(32) * (5 - len(enctemp)))
                        lcd_display.cursor_pos = (1, 20 - len(enctemp))
                        lcd_display.write_string(enctemp)
                        lcd_display.cursor_pos = (2, 0)
                        lcd_display.write_string("Enclosure Humi:")
                        lcd_display.cursor_pos = (2, 15)
                        lcd_display.write_string(chr(32) * (5 - len(enchum)))
                        lcd_display.cursor_pos = (2, 20 - len(enchum))
                        lcd_display.write_string(enchum)
                        lcd_display.cursor_pos = (3, 0)
                        lcd_display.write_string(chr(32) * 20)
                    else:
                        lcd_display.cursor_pos = (0, 0)
                        lcd_display.write_string(chr(32) * 20)
                        lcd_display.cursor_pos = (1, 0)
                        lcd_display.write_string("Enclosure Temp:")
                        lcd_display.cursor_pos = (1, 15)
                        lcd_display.write_string(chr(32) * (5 - len(enctemp)))
                        lcd_display.cursor_pos = (1, 20 - len(enctemp))
                        lcd_display.write_string(enctemp)
                        lcd_display.cursor_pos = (2, 0)
                        lcd_display.write_string("Enclosure Humi:")
                        lcd_display.cursor_pos = (2, 15)
                        lcd_display.write_string(chr(32) * (5 - len(enchum)))
                        lcd_display.cursor_pos = (2, 20 - len(enchum))
                        lcd_display.write_string(enchum)
                        lcd_display.cursor_pos = (3, 0)
                        lcd_display.write_string(chr(32) * 20)


                elif temperature != None and humidity != None:
                    lcd_display.cursor_pos = (0, 0)
                    lcd_display.write_string("Temp: %d C   " % int(temperature))
                    lcd_display.cursor_pos = (1, 0)
                    lcd_display.write_string("Humidity: %d %% " % int(humidity))

    except RuntimeError as e:
        continue
    except Exception as e:
        continue
    
