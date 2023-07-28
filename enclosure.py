# enclosure.py -- https://github.com/stooged/Klipper-Plugins/blob/main/enclosure.py
from . import print_stats, virtual_sdcard, gcode_move, display_status
import time
import adafruit_dht           
import RPi.GPIO as GPIO        
from RPLCD.i2c import CharLCD 
try:
    import thread
except ImportError:
    import _thread as thread


class ENCLOSURE:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.print_stats = self.printer.load_object(config, 'print_stats')
        self.virtual_sdcard = self.printer.load_object(config, 'virtual_sdcard')
        self.gcode_move = self.printer.load_object(config, 'gcode_move')
        self.display_status = self.printer.load_object(config, 'display_status')
        self.printing = False
        self.lcd_display = None
        self.fan_relay_gpio = config.getint("fan_relay_gpio")
        self.dht_sensor_gpio = config.getint("dht_sensor_gpio")
        self.dht_sensor_type = config.getint("dht_sensor_type")
        self.is_20x4_lcd = config.getboolean("is_20x4_lcd")
        self.temp_on = config.getint("temp_on")
        self.temp_off = config.getint("temp_off")
        self.machine_name = config.get("machine_name")
        self.printer.register_event_handler('klippy:ready', self.handle_ready) 
        self.printer.register_event_handler('klippy:disconnect', self.handle_disconnect)
        self.printer.register_event_handler('idle_timeout:printing', self.handle_printing)
        self.printer.register_event_handler('idle_timeout:ready', self.handle_not_printing)
        self.printer.register_event_handler('idle_timeout:idle', self.handle_not_printing)
        
        try:
            if self.dht_sensor_type == "21":
                self.dht_sensor = adafruit_dht.DHT21(self.dht_sensor_gpio)
            elif self.dht_sensor_type == "22":
                self.dht_sensor = adafruit_dht.DHT22(self.dht_sensor_gpio)
            else:
                self.dht_sensor = adafruit_dht.DHT11(self.dht_sensor_gpio)
        except Exception:
            self.dht_sensor = None
            pass

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.fan_relay_gpio, GPIO.OUT)
        except Exception:
            pass

        try:
            if self.is_20x4_lcd == True:
                self.lcd_display = CharLCD(i2c_expander="PCF8574", address=0x27, cols=20, rows=4, backlight_enabled=True, charmap="A00")
                if self.lcd_display is not None:
                    self.lcd_display._set_cursor_mode("hide")
                    self.lcd_display.clear()
                    self.machine_name = self.machine_name[0:20]
                    self.lcd_display.cursor_pos = (1, int((20 - len(self.machine_name)) / 2))
                    self.lcd_display.write_string(self.machine_name)
                    self.lcd_display.cursor_pos = (2, 5)
                    self.lcd_display.write_string("Loading...")
            else:
                self.lcd_display = CharLCD(i2c_expander="PCF8574", address=0x27, cols=16, rows=2, backlight_enabled=True, charmap="A00")
                if self.lcd_display is not None:
                    self.lcd_display._set_cursor_mode("hide")
                    self.lcd_display.clear()
                    self.machine_name = self.machine_name[0:16]
                    self.lcd_display.cursor_pos = (0, int((16 - len(self.machine_name)) / 2))
                    self.lcd_display.write_string(self.machine_name)
                    self.lcd_display.cursor_pos = (1, 0)
                    self.lcd_display.write_string("   Loading...   ")
        except Exception:
            self.lcd_display = None
            pass


    def run_lcd_display(self):
        def run(*args):
            while True:
                time.sleep(3)
                try:
                    if self.dht_sensor != None:
                        temperature = self.dht_sensor.temperature
                        humidity = self.dht_sensor.humidity 
                        if humidity != None and temperature != None: 
                            if int(temperature) >= int(self.temp_on) and self.printing == True:
                                GPIO.output(self.fan_relay_gpio, GPIO.HIGH)
                            elif int(temperature) <= int(self.temp_off) or self.printing == False:
                                GPIO.output(self.fan_relay_gpio, GPIO.LOW)
                                
                            if self.is_20x4_lcd == True and self.lcd_display != None:
                                enctemp = str(int(temperature)) + "C"
                                enchum = str(int(humidity)) + "%"
                                if self.printing == True and self.virtual_sdcard != None:
                                    progress = str(int(self.virtual_sdcard.progress() * 100)) + "%"
                                    self.lcd_display.cursor_pos = (0, 0)
                                    self.lcd_display.write_string("Printing: ")
                                    self.lcd_display.cursor_pos = (0, 10)
                                    self.lcd_display.write_string(chr(32) * (10 - len(progress)))
                                    self.lcd_display.cursor_pos = (0, 10)
                                    self.lcd_display.write_string(progress)
                                    self.lcd_display.cursor_pos = (1, 0)
                                    self.lcd_display.write_string("Enclosure Temp:")
                                    self.lcd_display.cursor_pos = (1, 15)
                                    self.lcd_display.write_string(chr(32) * (5 - len(enctemp)))
                                    self.lcd_display.cursor_pos = (1, 20 - len(enctemp))
                                    self.lcd_display.write_string(enctemp)
                                    self.lcd_display.cursor_pos = (2, 0)
                                    self.lcd_display.write_string("Enclosure Humi:")
                                    self.lcd_display.cursor_pos = (2, 15)
                                    self.lcd_display.write_string(chr(32) * (5 - len(enchum)))
                                    self.lcd_display.cursor_pos = (2, 20 - len(enchum))
                                    self.lcd_display.write_string(enchum)
                                    p_status = self.print_stats.get_status(self.reactor.monotonic())
                                    g_status = self.gcode_move.get_status(self.reactor.monotonic())
                                    d_status = self.display_status.get_status(self.reactor.monotonic())
                                    duration = p_status['print_duration']
                                    prog =  d_status['progress']
                                    spf = g_status['speed_factor']
                                    total = duration / prog
                                    seconds = int((total - duration) / spf)
                                    hours = seconds // (60*60)
                                    seconds %= (60*60)
                                    minutes = seconds // 60
                                    seconds %= 60
                                    left = "%02i:%02i:%02i" % (hours, minutes, seconds)
                                    self.lcd_display.cursor_pos = (3, 0)
                                    self.lcd_display.write_string("Remaining: ")
                                    self.lcd_display.cursor_pos = (3, 11)
                                    self.lcd_display.write_string(chr(32) * (9 - len(left)))
                                    self.lcd_display.cursor_pos = (3, 20 - len(left))
                                    self.lcd_display.write_string(left)
                                    
                                else:
                                    self.lcd_display.cursor_pos = (0, 0)
                                    self.lcd_display.write_string(chr(32) * 20)
                                    self.lcd_display.cursor_pos = (1, 0)
                                    self.lcd_display.write_string("Enclosure Temp:")
                                    self.lcd_display.cursor_pos = (1, 15)
                                    self.lcd_display.write_string(chr(32) * (5 - len(enctemp)))
                                    self.lcd_display.cursor_pos = (1, 20 - len(enctemp))
                                    self.lcd_display.write_string(enctemp)
                                    self.lcd_display.cursor_pos = (2, 0)
                                    self.lcd_display.write_string("Enclosure Humi:")
                                    self.lcd_display.cursor_pos = (2, 15)
                                    self.lcd_display.write_string(chr(32) * (5 - len(enchum)))
                                    self.lcd_display.cursor_pos = (2, 20 - len(enchum))
                                    self.lcd_display.write_string(enchum)
                                    self.lcd_display.cursor_pos = (3, 0)
                                    self.lcd_display.write_string(chr(32) * 20)

                            elif self.lcd_display != None:
                                self.lcd_display.cursor_pos = (0, 0)
                                self.lcd_display.write_string("Temp: %d C   " % int(temperature))
                                self.lcd_display.cursor_pos = (1, 0)
                                self.lcd_display.write_string("Humidity: %d %% " % int(humidity))

                except RuntimeError:
                    continue
                except Exception:
                    continue  
        thread.start_new_thread(run, ())


    def handle_printing(self, print_time):
        self.pstatus = self.print_stats.get_status(print_time)
        if self.pstatus['state'] == "printing":
            self.printing = True

    def handle_not_printing(self, print_time):
        self.pstatus = self.print_stats.get_status(print_time)
        if self.pstatus['state'] == "complete":
            self.printing = False
        elif self.pstatus['state'] == "error":
            self.printing = False

    def handle_ready(self):
        self.run_lcd_display()

    def handle_disconnect(self):
        if self.lcd_display is not None:
            self.lcd_display.close(clear=True)
            self.lcd_display = None
            self.dht_sensor.exit()


def load_config(config):
    return ENCLOSURE(config)
    
