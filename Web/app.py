import string 
from flask import * 
from Database import *
from flask_sessionstore import Session
import json
from werkzeug.utils import secure_filename
import subprocess
from bson import ObjectId

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

def valMap(i, imin, imax, omin, omax):
    aa = omin + (((omax - omin) / (imax - imin)) * (i - imin))  # The valuesula to map ranges
    return aa

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

            if db.verifyOtpUser(uid, otp):
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

@app.route("/createModel", methods=["GET", "POST"])
def createModel():
    if "login" in session:
        ss = session['login'] 
    else:
        return redirect("/login_user")
    return "Done"

############################################ JavaScript POST Handlers ############################################

# The Restful APIs are defined here


# Each unique pair of User and Model has a unique API Key, Hashed with a strong cryptographic function
# The User must make a post request to /inferAPI/universal with apiKey, user id and test.
# ApiKey is a hash of User ID and Model ID.  

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
        result = AIengine.classify({"text":text.lower(), "model_type":val['model_type'], "model_id":val['model_id']})
        callID = db.logApiCall({"user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "text":text, "result":result[0]})
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
        label = request.values['label']
    except:
        data = request.get_json(force=True)
        apiKey = data['apikey']
        user = data['user']
        callID = data['callid']
        feedback = data['feedback']
        label = data['label']
    callID = ObjectId(callID)
    print(callID)
    val = db.validateApikey(apiKey, user)    
    if val is None:
        return "Api key/User id invalid Invalid, Please try again!"
    label = reverseSent[label]
    if feedback == 'correct':
        return "Done"
    if val['model_type'] == 'vanilla':
        return jsonify("Sorry, but Vanilla model cannot be improved automatically")
    elif val['model_type'] == 'global':
        # Delayed Learning, Store the feedbacks for now in a global database:
        db.saveFeedBacks(callID, feedback)
        # A Cron Job would update the model at regular intervals
    elif val['model_type'] == 'private':
        # Send request immidiately for Online Learning
        print(callID)
        AIengine.engine.feedback({"model_type":val['model_type'], "model_id":val['model_id'], 'text':db.getTextFromCall(callID), "label":label})
    db.logApiFeedback({"user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "callid":callID, "corrected":label})
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
    db.logApiFeedback({"user":user, "api_key":apiKey, "model_type":val['model_type'], "model_id":val['model_id'], "dataset":datafile})
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