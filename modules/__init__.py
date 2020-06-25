from flask import Flask
from extensions import mysql, jsglue

app = Flask(__name__)

# App Settings
app.secret_key = 'rmyao84v-qubt0e7flc@-nr5rx5+29!fje=r+dxwow5vos%zy0r%!e'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'sql10.freemysqlhosting.net'
app.config['MYSQL_USER'] = 'sql10350571'
app.config['MYSQL_PASSWORD'] = 'hv6XGdMc5e'
app.config['MYSQL_DB'] = 'sql10350571'
# Configure plugins
mysql.init_app(app)
jsglue.init_app(app)

from modules.client.routes import mod as clientmod
from modules.admin.routes import mod as adminmod

app.register_blueprint(clientmod)
app.register_blueprint(adminmod, url_prefix='/admin')
