# generate_report.py -- https://github.com/stooged/Klipper-Plugins/blob/main/generate_report.py
import time
import logging
import os

class GENERATE_REPORT:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_mux_command("CREATE_REPORT", "AXIS", "Y", self.CREATE_REPORT, desc="Generate report image for Y axis")
        self.gcode.register_mux_command("CREATE_REPORT", "AXIS", "X", self.CREATE_REPORT, desc="Generate report image for X axis")


    def CREATE_REPORT(self, params):
        try:
            param = params.get('AXIS','')
            outfile = "shaper_" + param + "_" + time.strftime("%Y%m%d-%H%M%S") + ".png"
            if param == "X":
                response = os.system("~/klipper/scripts/calibrate_shaper.py /tmp/resonances_x_*.csv -o ~/printer_data/config/" + outfile)
                if response == 0:
                    self.gcode.respond_info("Saved: " + outfile)
                else:
                    self.gcode.respond_info("Error: failed to create report")
            elif param == "Y":
                response = os.system("~/klipper/scripts/calibrate_shaper.py /tmp/resonances_y_*.csv -o ~/printer_data/config/" + outfile)
                if response == 0:
                    self.gcode.respond_info("Saved: " + outfile)
                else:
                    self.gcode.respond_info("Error: failed to create report")
            else:
                self.gcode.respond_info("Error: unknown param '" + param + "'")
        except Exception as e:
            self.gcode.respond_info("Error: " + str(e))
            pass


def load_config(config):
    return GENERATE_REPORT(config)