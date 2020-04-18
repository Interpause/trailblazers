from flask import Flask, jsonify, render_template, g, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import UUIDType
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import datetime,uuid

from collections import namedtuple
NavBox = namedtuple('NavBox',('func','label'))
default_navbar = [NavBox('getHeatmap','Heatmap'),NavBox('getAbout','About')]
UserPublicData = namedtuple('UserPublicData',('name','userid','mc_expiry'))

def print(*args, **kwargs): raise Exception('print() is blocked in this scope! Use app.logger instead.')

app = Flask(__name__)
#app.config.from_envvar('SERVER_CONFIG')
app.config.update(
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///'+'test.db',
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    JWT_SECRET_KEY = 'lookMummyIamaSuperLongtestKeylol'
)
jwt = JWTManager(app)
db = SQLAlchemy(app)
#TODO: Since retrieving individual columns is a hassle, in-memory caching by last_activity_time?
class User(db.Model):
    uuid = db.Column(UUIDType(binary = False), primary_key = True)
    phone = db.Column(db.Integer, nullable = False)
    name = db.Column(db.String(200), nullable = False) #what is the longest name you can think of?
    pdpa = db.Column(db.String(9), nullable = True)

    last_activity_time = db.Column(db.Integer, nullable = True)
    user_created_time = db.Column(db.Integer, nullable = False)
    mc_expiry = db.Column(db.Integer, nullable = True)

    __tablename__ = 'Users'
    def __repr__(self): return f'<User: {self.uuid}'

    def getData(self):
        return UserPublicData(self.name,self.uuid,self.mc_expiry)
db.create_all()
db.session.commit()
test_user = User(uuid=uuid.UUID(int=0),phone=99999999,name='The Admin',pdpa='xxxx',user_created_time=datetime.datetime.now().timestamp())

'''
@jwt_required does quite a bit already for you
PUT EVERYTHING IN POST, USE THE JWT HANDLER OR SMTH TO APPEND TO G and INFORM CODE TO DO EXTRA STUFF
Posts are used, and posted to root '/' so that all info is encrypted. Apparently traces of get requests (content in URL) remain but not post (content in body).
if user device doesn't have uuid:
    userCreatePost() <- phone number, name, pdpa?
    verify(phone_num) #there is a good reason all services do this... impersonation.
    if phone_num in db:
        return db[phone_num].uuid
    else:
        new Visitor(new uuid,other info)
        return uuid
    proceed to if user device has uuid.
if user device has uuid:
    userLoginPost() <- uuid
    if uuid not in db:
        log shit
        tell client that their account doesn't exist or smth and send the template for the FAQ lol
    else:
        generate_session_token(uuid) stored in the db, expires after 1 hour without pings or smth idk.
        return token
The wrapper function is for tracking the last activity and last activity time of each user through their session id.
^good for logging too... how to record app route?
'''

@app.route('/',methods=['GET'])
def getRoot():
    return redirect(url_for('getMain'))

MenuBtn = namedtuple('MenuBtn',('func','label','icon'))
default_menu = [MenuBtn('checkMC','Order Food','place'),
                MenuBtn('getAbout','Deliver','local_shipping'),
                MenuBtn('getMain','Settings','settings'),
                MenuBtn('getMain','Get Help','help_outline')
                ]
@app.route('/main')
def getMain():
    g.user = test_user.getData() #TODO
    return render_template('main.html',
        time=datetime.datetime.now().strftime("%H:%M:%S, %d %b %Y"),
        navbar=default_navbar,
        menu=default_menu
    )

@app.route('/about')
def getAbout():
    g.user = test_user.getData() #TODO
    app.logger.debug(f'Login: {g.user.userid}')
    return render_template('about.html',
        #TODO: did you know datetime has locale? clientid can store user language.
        time=datetime.datetime.now().strftime("%H:%M:%S, %d %b %Y"),
        navbar=default_navbar
    )

@app.route('/heatmap')
def getHeatmap():
    g.user = test_user.getData() #TODO
    if g.userid is not None:
        pass
    abort(501)

@app.route('/camera')
def getCamera():
    g.user = test_user.getData() #TODO
    return render_template('camera.html',
        time=datetime.datetime.now().strftime("%H:%M:%S, %d %b %Y"),
        navbar=default_navbar
    )

@app.route('/mc_check')
def checkMC():
    g.user = test_user.getData() #TODO

    if g.user.mc_expiry is None:
        return redirect(url_for('getCamera'))
    return redirect(url_for('getOrder'))

@app.route('/order')
def getOrder():
    abort(501)

@app.errorhandler(404)
def on404(e):
    return render_template('baseFull.html',error=e,navbar=default_navbar),404

@app.errorhandler(501)
def on501(e):
    return render_template('baseFull.html',error=e,navbar=default_navbar),501

@app.errorhandler(Exception)
def onGeneralError(e):
    return render_template('baseFull.html',error=e,navbar=default_navbar),500

@app.teardown_appcontext
def cleanupTransection(param):
    user = g.pop('user',None)
    if user is not None:
        pass #user specific cleanup/logging
    #for streams, you could pop it then close it
    #anything that doesn't require cleaning up can be ignored

if __name__ == "__main__":  
    app.run(port=80)