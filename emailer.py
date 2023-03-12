
import logging
from . import print_stats
import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from PIL import Image
from io import BytesIO



class EMAILER:


    def __init__(self, config):
        self.printer = config.get_printer()
        self.print_stats = self.printer.load_object(config, 'print_stats')
        self.printing = False
        self.send_email_notifications = config.getboolean("send_email_notifications")
        self.machine_name = config.get("machine_name")
        self.send_image = config.getboolean("send_image")
        self.sender_email = config.get("sender_email")
        self.sender_password = config.get("sender_password")
        self.receiver_email = config.get("receiver_email")
        self.smtp_host = config.get("smtp_host")
        self.smtp_port = config.getint("smtp_port")
        self.printer.register_event_handler('idle_timeout:printing', self.handle_printing)
        self.printer.register_event_handler('idle_timeout:ready', self.handle_not_printing)
        self.printer.register_event_handler('idle_timeout:idle', self.handle_not_printing)





    def send_email(self, status, filename, duration):
        try:
            if self.printing == True and self.send_email_notifications == True:
                subject = self.machine_name + ": " + status
                if filename == None:
                    filename = "Print" 
                body = filename + " " + status + " in " + str(datetime.timedelta(seconds=int(duration)))
                msg = MIMEMultipart()
                msg["From"] = self.sender_email
                msg["To"] = self.receiver_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
            
                if self.send_image == True:
                    response = requests.get("http://127.0.0.1/webcam/?action=snapshot")  
                    with Image.open(BytesIO(response.content)) as img:
                        img_bytes = BytesIO()
                        img.save(img_bytes, format='JPEG')
                        img_bytes = img_bytes.getvalue()
                    attachment = MIMEImage(img_bytes)
                    attachment.add_header('Content-Disposition', 'attachment', filename='image.jpg')
                    msg.attach(attachment)
            
                smtp_session = smtplib.SMTP(self.smtp_host, self.smtp_port)
                smtp_session.starttls()
                smtp_session.login(self.sender_email, self.sender_password)
                smtp_session.sendmail(self.sender_email, self.receiver_email, msg.as_string())
                smtp_session.quit()                  
        except Exception as e:
            pass
            logging.warn(str(e))




    def handle_printing(self, print_time):
        self.status = self.print_stats.get_status(print_time)
        if self.status['state'] == "printing":
            self.printing = True




    def handle_not_printing(self, print_time):
        self.status = self.print_stats.get_status(print_time)
        if self.status['state'] == "complete":
            self.send_email(self.status['state'] , self.status['filename']  , self.status['print_duration'] )
            self.printing = False
        elif self.status['state'] == "error":
            self.send_email(self.status['message'] , "ERROR:"  , self.status['print_duration'] )
            self.printing = False
            logging.warn(str(self.status))

    

def load_config(config):
    return EMAILER(config)
    
