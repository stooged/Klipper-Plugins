#Klipper Plugins

these scripts are built to work with my printers and will probably require changes to suit your specific setup




##emailer.py

emailer.py is used to send email notifications on print completion and error using smtp

upload the emailer.py file to `/home/pi/klipper/klippy/extras/` or the klippy/extras directory within your klipper install


to use it you must use the ssh console and install the following into the klippy environment using the following commands

```

~/klippy-env/bin/pip3 install requests Pillow

```

you also need to add the following lines to your printer.cfg and edit them to suit your needs


```

[emailer]
machine_name: Printer
send_email_notifications: True
send_image: False  ##-----if you have a webcam you can set this to True
sender_email: email@email.com
sender_password: password
receiver_email: email@email.com
smtp_host: smtp.email.com
smtp_port: 587

```



##enclosure.py


enclosure.py is used to control the temperature of the printer enclosure by reading a dht sensor, at set temps it will switch the extraction fan on or off
it also displays the temps on a lcd screen along with print progress in % if printing

to use it upload enclosure.py and enclosure.cfg to the config files section in mainsail/fluid

edit the enclosure.cfg to match your gpio and sensor type etc


then use ssh to do the following


edit  "/etc/rc.local"

```
sudo nano /etc/rc.local

```

and add

```
sudo python3 /home/pi/printer_data/config/enclosure.py &

```

enable SPI in the `raspi-config` for the lcd display

install the following packages

```

sudo pip3 install Adafruit_DHT RPi.GPIO RPLCD smbus

```

reboot and it should load on start up