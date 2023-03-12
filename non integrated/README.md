# Non Integrated Scripts

these scripts are built to work with my printers and will probably require changes to suit your specific setup.
my printers run mainsail os/klipper on raspberry pi 4 using dht11 sensors with 20x4 i2c lcd screens.


this collection of scripts do not run within the klippy environment, they run on the host and use websockets to communicate with mainsail/fluid to retrive the data required to operate.





## enclosure.py


enclosure.py is used to control the temperature of the printer enclosure by reading a dht sensor, at set temps it will switch the extraction fan on or off,
it also displays the temperature on a lcd screen along with print progress in % if printing

to use it upload `enclosure.py` and `enclosure.cfg` to the config files section in mainsail/fluid.

edit the `enclosure.cfg` to match your gpio and sensor type etc.


then use ssh to do the following.


edit  "/etc/rc.local"

```
sudo nano /etc/rc.local

```

and add.

```
sudo python3 /home/pi/printer_data/config/enclosure.py &

```

enable i2c in the `raspi-config` for the lcd display.

install the these packages using the following command.

```

sudo pip3 install adafruit-circuitpython-dht RPi.GPIO RPLCD smbus

```

reboot and it should load on start up.