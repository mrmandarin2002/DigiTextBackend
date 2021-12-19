import smtplib, ssl
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.application import MIMEApplication
from os import listdir

def backup_dbs(path="schools"):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    gmail = "digitextdatabase@gmail.com"
    password = "Aligod2020!"

    message = MIMEMultipart("mixed")
    message["From"] = "Contact <{sender}>".format(sender = gmail)
    message["To"] = "digitextdatabase@gmail.com"
    message["CC"] = "digitextdatabase@gmail.com"
    message["Subject"] = "Database Backup"

    with open("meta.db", "rb") as attachment:
        p = MIMEApplication(attachment.read(),_subtype="pdf")
        p.add_header('Content-Disposition', "attachment; filename= %s" % "meta.db")
        message.attach(p) 

    for db_path in [path + "/" + i for i in listdir(path)]:
        try:
            with open(db_path, "rb") as attachment:
                p = MIMEApplication(attachment.read(),_subtype="pdf")	
                p.add_header('Content-Disposition', "attachment; filename= %s" % db_path.split("/")[-1]) 
                message.attach(p)
        except Exception as e:
            print(str(e))

    msg_full = message.as_string()

    # context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(gmail, password)
        server.sendmail(gmail, [message["To"]], msg_full)
        server.quit()

if __name__ == "__main__":
    from time import sleep

    while True:
        backup_dbs()
        sleep(3600)