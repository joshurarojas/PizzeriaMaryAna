from flask_mysqldb import MySQL, MySQLdb
from flask_jsglue import JSGlue
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from pathlib import Path
import bcrypt

sk_sendgrid = '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'

Mail = Mail
sendgrid = SendGridAPIClient(sk_sendgrid)
jsglue = JSGlue()
mysql = MySQL()
MySQLdb = MySQLdb
bcrypt = bcrypt

def getProjectRoot() -> Path:
    return Path(__file__).parent