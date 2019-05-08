import string 
from flask import * 
from Database import *
from flask_sessionstore import Session
import json
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)
app.config.update(
    DATABASE = 'Smart'
)
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
#Session(app)

global db  
db = Database("mongodb://localhost:27017/")

# Set the secret key to some random bytes. Keep this really secret!
import os 
import random
app.secret_key = os.urandom(32)#bytes(str(hex(random.getrandbits(128))), 'ascii')

@app.errorhandler(404)
def page_not_found(e):
    return render_template("/404.html")

@app.route("/home", methods=["GET", "POST"])    # 
def home():
    return render_template('/overview/index.html')

@app.route("/", methods=["GET", "POST"])        # Home Page
@app.route("/login", methods=["GET", "POST"])
def login():
    if "login" in session:
        return dashboard()
    elif request.method == "POST":
        try:
            uid = request.form['email']
            upass = request.form['pass']
            print(uid)
            print(upass)
            if db.validateUser(uid, upass):
                session["login"] = uid
                session["feedpos"] = 0
                #session["database"] = Database("http://admin:ashish@localhost:5984")
                return redirect("/dashboard")
            else:
                return "Incorrect Username/Password"
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    return render_template('/login/login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if "login" in session:
        return dashboard()
    elif request.method == "POST":
        global db
        try:
            data = request.get_json(force=True) 
            if db.createUser(data) == 1:
               return jsonify("Success")
            else: return jsonify("Username Already Taken")
        except Exception as ex:
            print(ex)
            return render_template("/500.html")
    else:
        return render_template('/register/register.html')

############################################ Dashboard and internal stuffs ############################################

global diagnosisTable
diagnosisTable = {"prostateCancer":'python3 /root/Desktop/Reboot/TumorDetection/prostateInference.py /root/Desktop/Reboot/TumorDetection/ProstateTest.csv',
    "breastCancer":'python3 /root/Desktop/Reboot/TumorDetection/waste/breastCancer.py /root/Desktop/Reboot/TumorDetection/ProstateTest.csv',
    "heartDisease":'python3 /root/Desktop/Reboot/TumorDetection/waste/heartDisease.py /root/Desktop/Reboot/TumorDetection/ProstateTest.csv',
    "lungCancer":'python3 /root/Desktop/Reboot/TumorDetection/waste/lungCancer.py /root/Desktop/Reboot/TumorDetection/ProstateTest.csv',
    "brainTumor":'python3 /root/Desktop/Reboot/TumorDetection/waste/brainTumor.py /root/Desktop/Reboot/TumorDetection/ProstateTest.csv'}

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "login" in session: 
        if request.method == "POST":
            return render_template('/overview/dashboard.html')
        ss = session['login'] 
        #info = db.getUserInfo(ss)
        return render_template('/overview/dashboard.html')#, profile_name = info['name'], profile_email = info['email'])
    else:
        return redirect("/login")
    return render_template('/500.html')

@app.route("/logout", methods=["GET", "POST"])
def logout():
    global db
    del db 
    db = Database("mongodb://localhost:27017/")
    session.pop('login', None)
    session.pop('feedpos', None)
    return redirect("/login")#render_template("/login.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import json

@app.route("/upload", methods=['POST', 'GET'])
def upload():
    if "login" in session: 
        global diagnosisTable
        print("Got Here")
        option = request.form['option']
        #diagModel = diagnosisTable[option]
        # Use the ML Model for inference
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return render_template('/upload/upload.html', diagType = option)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return render_template('/upload/upload.html', diagType = option)

        if file and allowed_file(file.filename):
            print("asdsad")
            print(subprocess.run("whoami"))
            filename = secure_filename(file.filename)
            file.save(filename)#(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cmd = diagnosisTable[option]
            print(subprocess.getoutput('pwd; python3 --version'))
            g = subprocess.getoutput(cmd)
            print(g)
            b = dict({'output':g})
            return render_template("/output.html", inference = json.dumps(b))#redirect(url_for('uploaded_file', filename=filename))
        inference = "Hello World"
        return render_template('/output.html', inference = inference)
    else: 
        return redirect('/login')

@app.route("/methods/lungCancer", methods=['GET', 'POST'])
def lungCancer():
    if "login" in session: 
        option = "lungCancer"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/brainTumor", methods=['GET', 'POST'])
def brainTumor():
    if "login" in session: 
        option = "brainTumor"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/prostateCancer", methods=['GET', 'POST'])
def prostateCancer():
    if "login" in session: 
        option = "prostateCancer"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/breastCancer", methods=['GET', 'POST'])
def breastCancer():
    if "login" in session: 
        option = "breastCancer"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/heartDisease", methods=['GET', 'POST'])
def heartDisease():
    if "login" in session: 
        option = "heartDisease"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/ecgDiagnosis", methods=['GET', 'POST'])
def ecgDiagnosis():
    if "login" in session: 
        option = "ecgDiagnosis"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


@app.route("/methods/glaucoma", methods=['GET', 'POST'])
def glaucoma():
    if "login" in session: 
        option = "glaucoma"
        return render_template('/upload/upload.html', diagType = option)
    else:
        return redirect("/login")


############################################ JavaScript POST Handlers ############################################
