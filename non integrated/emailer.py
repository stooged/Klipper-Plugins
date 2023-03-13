#!/usr/bin/python
# emailer.py -- https://github.com/stooged/Klipper-Plugins/blob/main/non%20integrated/emailer.py
import time
import datetime
import websocket               # websocket-client
from PIL import Image          # Pillow
import requests                # requests
from pathlib import Path
import configparser
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from io import BytesIO
try:
    import thread
except ImportError:
    import _thread as thread

printing = False
gfilename = None

cfg_file = Path("/home/pi/printer_data/config/emailer.cfg")
if cfg_file.is_file():
    config = configparser.ConfigParser()
    config.read("/home/pi/printer_data/config/emailer.cfg")
    send_email_notifications = config.getboolean("emailer", "send_email_notifications", fallback=False)
    machine_name = config.get("emailer", "machine_name")
    send_image = config.getboolean("emailer", "send_image", fallback=False)
    sender_email = config.get("emailer", "sender_email")
    sender_password = config.get("emailer", "sender_password")
    receiver_email = config.get("emailer", "receiver_email")
    smtp_host = config.get("emailer", "smtp_host")
    smtp_port = config.getint("emailer", "smtp_port", fallback=587)

else:                         #hard codeed values used if emailer.cfg is missing

    machine_name = "Printer"             # printer name used in email
    send_email_notifications = True      # enable email notification on print complete and error
    send_image = False                   # include snapshot from webcam with email notification
    sender_email = "email@email.com"     # email to send from
    sender_password = "password"         # password for sending email
    receiver_email = "email@email.com"   # email to send to
    smtp_host = "smtp.email.com"         # smtp host for email provider
    smtp_port = 587                      # smtp port



def subscribe():
    return {
        "jsonrpc": "2.0",
        "method": "printer.objects.subscribe",
        "params": {
            "objects": {
                "print_stats": ["filename", "state", "print_duration", "message"]
            }
        },
        "id": "8437"
    }



def send_email(status, filename, dura):
    try:
        if printing == True and send_email_notifications == True:
            subject = machine_name + ": " + status
            if filename == None:
                filename = "Print" 
            body = filename + " " + status + " in " + str(datetime.timedelta(seconds=int(dura)))
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            if send_image == True:
                response = requests.get("http://127.0.0.1/webcam/?action=snapshot")  
                with Image.open(BytesIO(response.content)) as img:
                    img_bytes = BytesIO()
                    img.save(img_bytes, format='JPEG')
                    img_bytes = img_bytes.getvalue()
                attachment = MIMEImage(img_bytes)
                attachment.add_header('Content-Disposition', 'attachment', filename='image.jpg')
                msg.attach(attachment)
            smtp_session = smtplib.SMTP(smtp_host, smtp_port)
            smtp_session.starttls()
            smtp_session.login(sender_email, sender_password)
            smtp_session.sendmail(sender_email, receiver_email, msg.as_string())
            smtp_session.quit()          
    except Exception:
        pass


def parse_json(json_obj, message):
    global printing
    global gfilename
    if "print_stats" in json_obj:
        print_stats = json_obj["print_stats"]
        if "filename" in print_stats:
            gfilename = print_stats["filename"]  
        if "state" in print_stats:
            state = print_stats["state"]
            if state == "printing" and printing == False:
                printing = True
            if state == "complete":
                send_email(state, gfilename, print_stats["print_duration"])
                printing = False
            if state == "error":
                send_email(print_stats["message"], "ERROR: ", print_stats["print_duration"])
                printing = False 
            if state == "cancelled":
                printing = False     


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
        time.sleep(30)
        ws = websocket.WebSocketApp(f"ws://127.0.0.1:7125/websocket", on_message=on_message, on_error=on_error, on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()
    thread.start_new_thread(run, ())
    
connect_websocket()


while True:
    time.sleep(1)