/InferenceRESTful Directory contains API_specs.txt, containing the API Specifications for the ML Engine

/Web Contains a Demo Website for providing Classifier as a service, with its own REST APIs, Documentation to come soon
REMEMBER, IF STARS >= 4 or STARS <= 2, IGNORE THE Classification itself!!!

INSTALLATION:
    RUN "pip3 install -r requirements.txt" in /Web and /InferenceRESTful Directories to install all python requirements

RUN:
    in /Web Directory, Enter command
        sudo uwsgi --master --workers 9 --threads 9 --socket 0.0.0.0:80 --protocol=http -w app:app --enable-threads
    in /InferenceRESTful, Enter command
        sudo FLASK_APP=app.py python3 -m flask run --host 0.0.0.0