import string 
from flask import * 
from Database import *
from flask_sessionstore import Session
import json
from werkzeug.utils import secure_filename
import subprocess
from bson import ObjectId
import hashlib
import time 
import requests

from Inference import *

app = Flask(__name__)
app.config.update(
    DATABASE = 'Smart'
)
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
#Session(app)
AIengine = InferenceWrapper(NNLM_InferenceEngine())

global db  
db = Database("mongodb://localhost:27017/")

# Set the secret key to some random bytes. Keep this really secret!
import os 
import random
app.secret_key = os.urandom(32)#bytes(str(hex(random.getrandbits(128))), 'ascii')

from flask_mail import Mail, Message


app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'tagclub.vitu@gmail.com'#'tagclub.vituniversity@gmail.com'
app.config['MAIL_PASSWORD'] = 'TAGnumba1'#'tagTHEclub@19'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route("/send_email")
def send_email(email, uid, otp):
    try:
        msg = Message('Hello ' + uid, sender=app.config.get("MAIL_USERNAME"), recipients = [email], body = "Hello! " + uid + ", Greetings from Tag club. Please use the following otp : " + otp + " on the link http://phoenix.tagclub.in/registerVerify" )
        mail.send(msg)
        return True
    except Exception as e:
        print(e)
        return None

@app.errorhandler(404)
def page_not_found(e):
    return render_template("/404.html")

@app.route("/", methods=["GET", "POST"])        # Home Page
@app.route("/home", methods=["GET", "POST"])    # Future Home Page
def home():
    if "login" in session:
        return redirect("/dashboard")
    else:
        return redirect("/login")#render_template('/homes.html')

@app.route("/login", methods=["GET", "POST"])
@app.route("/login_user", methods=["GET", "POST"])
def login_user():
    if "login" in session:
        return redirect("/dashboard")
    elif request.method == "POST":
        try:
            uid = request.form['uname']
            upass = request.form['pass']
            if(uid == '' or upass == ''):
                return render_template('/login.html')
            val = db.validateUser(uid, upass)
            if val:
                if val == "unverified":     # Don't let them login!
                    return redirect("/registerVerify")
                session["login"] = uid
                session["feedpos"] = 0
                session["type"] = val
                #session["database"] = Database("http://admin:ashish@localhost:5984")
                if val == "admin":
                    return redirect("/admin")
                else:
                    return redirect("/dashboard")
            else:
                return "Incorrect Username/Password"
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    return render_template('/login.html')

@app.route("/register", methods=["GET", "POST"])
@app.route("/register_user", methods=["GET", "POST"])
def register_user():
    if "login" in session:
        return redirect("/dashboard")
    elif request.method == "POST":
        global db
        try:
            data = dict(request.form)
            status = db.userExists(data)
            if status == 2:
                return render_template('/register.html', resp = "alert('Username Already Taken!');")
            elif status == 3:
                return render_template('/register.html', resp = "alert('Email Already Taken!');")
            if data['pass'] != data['cpass']:
                return render_template('/register.html', resp = "alert('Passwords do not match!');")
                
            data['otp'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            
            if send_email(data['email'], data['uname'], data['otp']) is None:
                return jsonify("Problem in sending Email!")
                
            if db.createUser(data) == 1:
               return render_template("/registerVerify.html", uid = data['uname'], resp = '')
            else: return render_template('/register.html', resp = "alert('Username Already Taken');")
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    else:
        return render_template('/register.html', resp = "")


@app.route("/registerVerify", methods=["GET", "POST"])
def registerVerify():
    if "login" in session:
        return redirect("/dashboard")
    elif request.method == "POST":
        global db
        try:
            uid = request.form['uname']
            otp = request.form['otp']

            if True:#db.verifyOtpUser(uid, otp):
                # Create default API keys for the user
                val1 = db.createNewAPIKey(uid, uid + "_vanilla", "vanilla", "vanilla")
                val2 = db.createNewAPIKey(uid, uid + "_global", "global", "global")
                if val1 and val2:
                    return render_template("/success.html")
            else: return render_template("/registerVerify.html", uid = uid, resp = "alert('Wrong otp!');")
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    else:
        return render_template("/registerVerify.html", uid = "", resp = "")
        #return render_template('/landing/login/register.html', resp = "")


@app.route("/resendOTP", methods=["GET", "POST"])
def resendOTP():
    if "login" in session:
        return redirect("/dashboard")
    elif request.method == "POST":
        global db
        try:
            email = request.form['email']
            otp,uname = db.getOTPbyEmail(email)
            g = send_email(email, uname, otp)
            if g:
               return render_template("/resendOTP.html", resp = "alert('OTP sent again, may take few minutes! Contact us on Facebook if it dosent work')");
            else: return render_template("/resendOTP.html", resp = "alert('Email address not found, Incorrect or Not Registered?')");
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    else:
        return render_template("/resendOTP.html", resp = "")
        #return render_template('/landing/login/register.html', resp = "")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    global db
    del db 
    db = Database("mongodb://localhost:27017/")
    session.pop('login', None)
    session.pop('feedpos', None)
    return redirect("/login_user")#render_template("/login_user.html")


########################################## ADMIN Dashboard and Secret Stuffs ##########################################

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if ("login" in session) and ("admin" in session["type"]):
        print("HLP")
        try:
            return redirect("/dashboard")#render_template('admin.html')
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    return render_template('/404.html')


############################################ Dashboard and internal stuffs ############################################


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "login" in session: 
        if request.method == "POST": # Redeem Flags
            #pp = request.form[]
            return render_template('/internal/home.html')
        ss = session['login'] 
        info = db.getUserInfo(ss)
        try:
            apiKeys = db.getUserApiKeys(ss)
        except Exception as e:
            print(e)
        print(info)
        return render_template('/internal/home.html', acc_level = info['type'], api_call_count = len(info['calls']), 
                                api_keys = json.dumps({"data":info['keys']}), api_key_count = len(info['keys']), profile_id = info['_id'], 
                                profile_name = info['name'], profile_email = info['email'])
    else:
        return redirect("/login_user")
    return render_template('/500.html')

############################################ RESTFUL APIs, STATELESS ############################################

# The Restful APIs are defined here


# Each unique pair of User and Model has a unique API Key, Hashed with a strong cryptographic function
# The User must make a post request to /inferAPI/universal with apiKey, user id and test.
# ApiKey is a hash of User ID and Model ID or can be a string defined by the user 

# Example Usage ==>
#   re.post("http://127.0.0.1:8000/inferAPI/universal", data={'apikey':'default', 'user':'admin', 'text':'Hello World'})
@app.route("/inferAPI/universal", methods=["GET", "POST"])    # Vanilla Model, Baseline original model, is untrainable
def inferAPI_universal():
    try:
        print("non json request")
        text = request.values['text']
        apiKey = request.values['apikey']
        user = request.values['user']
    except:
        data = request.get_json(force=True)
        print("json request")
        apiKey = data['apikey']
        user = data['user']
        text = data['text']
        print(data)
    try:
        print(apiKey)
        print(user)
        val = db.validateApikey(apiKey, user)    
        if val is None:
            return "Api key/User id invalid Invalid, Please try again!"
        result = AIengine.classify({"text":text.lower(), "model_type":val['model_type'], "model_id":val['model_id'], "user":user})
        callID = db.logApiCall({"timestamp":time.time(), "user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "text":text, "result":result[0]})
        result.append(str(callID))
        return jsonify(result)#jsonify({"callid":callID, "result":result['text']})
    except Exception as e:
        print(e)
        return e

reverseSent = {"Negative":"Positive", "Positive":"Negative"}

@app.route("/inferAPI/feedback", methods=["GET", "POST"])
def inferAPI_feedback():
    try:
        callID = request.values['callid']
        apiKey = request.values['apikey']
        user = request.values['user']
        feedback = request.values['feedback']
        #label = request.values['label']
    except:
        data = request.get_json(force=True)
        apiKey = data['apikey']
        user = data['user']
        callID = data['callid']
        feedback = data['feedback']
        #label = data['label']
    callID = ObjectId(callID)
    print(callID)
    val = db.validateApikey(apiKey, user)    
    if val is None:
        return "Api key/User id invalid Invalid, Please try again!"
    if db.validateCallID(callID, apiKey) is False:
        return "This callid wasn't made from the given API Key!"
    callData = db.getCallData(callID)
    label = reverseSent[callData['result']]
    if feedback == 'correct':
        return "Done"
    if val['model_type'] == 'vanilla':
        return jsonify("Sorry, but Vanilla model cannot be improved automatically")
    elif val['model_type'] == 'global':
        # Delayed Learning, Store the feedbacks for now in a global database:
        #db.saveFeedBacks(callID, feedback)
        # A Cron Job would update the model at regular intervals
        print(callID)
        AIengine.engine.feedback({"model_type":val['model_type'], "model_id":val['model_id'], 'text':callData['text'], "label":label})
    elif val['model_type'] == 'private':
        # Send request immidiately for Online Learning
        print(callID)
        AIengine.engine.feedback({"model_type":val['model_type'], "model_id":val['model_id'], 'text':callData['text'], "label":label})
    db.logApiFeedback({"timestamp":time.time(), "user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "callid":callID, "corrected":label})
    return "Done"

@app.route("/inferAPI/train", methods=["POST"])
def inferAPI_train():
    # A Priviledged feature wherein User can train a particular classifier for certain task by providing a dataset
    try:
        datafile = request.files['data']
    except:
        try:
            datafile = request.values['data']
        except:
            return "Please provide some proper dataset"
    user = request.values['user']
    val = db.validateApikey(apiKey, user)    
    if val is None:
        return "Api key/User id invalid Invalid, Please try again!"
    if(val['model_type'] != 'private'):
        return 'This Feature is not available for you, Sorry!'
    AIengine.engine.trainDirect({"model_type":val['model_type'], "model_id":val['model_id'], "dataset":datafile})
    db.logApiFeedback({"timestamp":time.time(), "user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "dataset":datafile})
    return "Done..."

@app.route("/inferAPI/save", methods=["POST"])
def inferAPI_save():
    # A Priviledged feature wherein User can train a particular classifier for certain task by providing a dataset
    try:
        print("non json request")
        apiKey = request.values['apikey']
        user = request.values['user']
    except:
        data = request.get_json(force=True)
        print("json request")
        apiKey = data['apikey']
        user = data['user']
        print(data)
    try:
        print(apiKey)
        print(user)
        val = db.validateApikey(apiKey, user)    
        if val is None:
            return "Api key/User id invalid Invalid, Please try again!"
        v = AIengine.engine.saveModel(val)
        return jsonify(v)
    except:
        return "Done"

@app.route("/inferAPI/load", methods=["POST"])
def inferAPI_load():
    # A Priviledged feature wherein User can train a particular classifier for certain task by providing a dataset
    try:
        print("non json request")
        apiKey = request.values['apikey']
        user = request.values['user']
    except:
        data = request.get_json(force=True)
        print("json request")
        apiKey = data['apikey']
        user = data['user']
        print(data)
    try:
        print(apiKey)
        print(user)
        val = db.validateApikey(apiKey, user)    
        if val is None:
            return "Api key/User id invalid Invalid, Please try again!"
        v = AIengine.engine.loadModel(val)
        return jsonify(v)
    except:
        return "Done"


@app.route("/inferAPI/create", methods=["GET", "POST"])
def createModel():
    if "login" in session:
        try:
            print("non json request")
            templatekey = request.values['templatekey']
            newkey = request.values['newkey']
            newuser = request.values['newuser']
            originaluser = request.values['originaluser']
        except:
            data = request.get_json(force=True)
            print("json request")
            templatekey = data['templatekey']
            newkey = data['newkey']
            newuser = data['newuser']
            originaluser = data['originaluser']
            print(data)
        v1 = db.validateApikey(templatekey, originaluser)    
        if (v1) is None:
            return "Api key/User id invalid Invalid, Please try again!"
        # TODO: Check if Original User allowed new user to share 
        if(originaluser == newuser):
            # No check required 
            pass
        elif db.validateSharing(originaluser, newuser, templatekey) is False:
            return "The Original user did not intend to share the model with you"
        if newkey == "none":
            newkey = hashlib.md5(bytes(str(hash(newuser+templatekey + str(time.time()))), 'utf-8')).hexdigest()
        val,org = db.createNewModel(newuser, templatekey, newkey)
        if val is None:
            return "the provided New api key is already taken, Provide new key or let us create one for you by using the name 'none'"
        result = AIengine.engine.createModel({"original":org, "new":val})
        return jsonify({"key":val['_id'], "result":result})
    else:
        return redirect("/login_user")
    return "Done"
