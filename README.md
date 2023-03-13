# Klipper Plugins

these scripts are built to work with my printers and will probably require changes to suit your specific setup.
my printers run mainsail os/klipper on raspberry pi 4 using dht11 sensors with 20x4 i2c lcd screens.






## emailer.py

emailer.py is used to send email notifications on print completion and error using smtp.

upload the `emailer.py` file to `/home/pi/klipper/klippy/extras/` or the klippy/extras directory within your klipper install.


to use it you must use the ssh console and install these packages into the klippy environment using the following command.

```

~/klippy-env/bin/pip3 install requests Pillow

```

you also need to add the following lines to your `printer.cfg` and edit them to suit your needs.


```

[emailer]
machine_name: Printer
send_email_notifications: True
send_image: False      ##-----if you have a webcam you can set this to True
sender_email: email@email.com
sender_password: password
receiver_email: email@email.com
smtp_host: smtp.email.com
smtp_port: 587

```






## enclosure.py


enclosure.py is used to control the temperature of the printer enclosure by reading a dht sensor, at set temps it will switch the extraction fan on or off,
it also displays the temperature on a lcd screen along with print progress in % if printing.
it is currently set to only run the fan while printing regardless of the temperature but you can change this in the code if you wish.


upload the `enclosure.py` file to `/home/pi/klipper/klippy/extras/` or the klippy/extras directory within your klipper install.


to use it you must use the ssh console and install these packages into the klippy environment using the following command.


```

~/klippy-env/bin/pip3 install adafruit-circuitpython-dht RPi.GPIO RPLCD smbus

```

and enable i2c in the `raspi-config` for the lcd display.



you also need to add the following lines to your `printer.cfg` and edit them to suit your needs.


```
[enclosure]
machine_name: Printer   
fan_relay_gpio: 17     ##-----gpio for fan relay to switch fan on and off
dht_sensor_gpio: 4     ##-----gpio for dht sensor
dht_sensor_type: 11    ##-----dht sensor type, 11, 21, 22
is_20x4_lcd: True      ##-----lcd type if set to false a 16x2 lcd will be used
temp_on: 26            ##-----temperature in °C to turn fan on
temp_off: 20           ##-----temperature in °C to turn fan off

```





## generate_report.py

generate_report.py is used to generate the frequency response report image from an accelerometer test and saves it to your machine config directory 
for viewing in the webbrowser, this just saves you having to use ssh to generate the images. 

upload the `generate_report.py` file to `/home/pi/klipper/klippy/extras/` or the klippy/extras directory within your klipper install.

then you can add the following macros to your printer.cfg to generate the images.


```
[generate_report]

[gcode_macro Create_Y_Report]
gcode:
   CREATE_REPORT AXIS=Y

[gcode_macro Create_X_Report]
gcode:
   CREATE_REPORT AXIS=X

```

i also have a few other macros for testing with an accelerometer here <a href=https://github.com/stooged/Config-For-Klipper/blob/main/adxl.cfg>adxl.cfg</a>