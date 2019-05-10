#!/usr/bin/python3
from flask import *
from flask_restful import *
from json import dumps
import subprocess

from AIengine import *

app = Flask(__name__)
api = Api(app)

# Filtering and Tokening Data text
def tokenizer(data):
    badWords = ['and', 'a', 'travelling', 'to', 'of', 'Platiunum', 'techkie', 'cPs']
    #inputSet = [[x for x in i['reviewText'].replace(',',' ').split(' ')] for i in dataset[:1]]
    inputSet = [re.sub("#[A-Za-z0-9]+|@[A-Za-z0-9]+|\\w+(?:\\.\\w+)*/\\S+", "", i) for i in data]
    inputSet = [[(x) for x in re.split('\W+', re.sub("[!@#$+%*:()'-]", ' ', i)) if x != ''] for i in inputSet]
    for i in inputSet:
        for j in range(0,len(i)):
            if re.match('^\d{4}$', i[j]):
                #print(i[j])
                i[j] = 'year'
            elif re.search('[0-9]', i[j]):
                if re.search('[a-zA-Z]', i[j]):
                    i[j] = 'item'
                else:
                    i[j] = 'num'
            elif i[j] in badWords:
                i[j] = 'AXTREMOVE'
    inputSet = [re.sub('AXTREMOVE', '', '-'.join(i)).split('-') for i in inputSet]
    return inputSet

sentiDict = {0:'negative', 1:'positive'}
sarcasmDict = {1:'negative', 0:'positive'}

privateModels = dict()
privateModels['global'] = evalModel
privateModels['vanilla'] = tf.keras.models.load_model('./models/vanilla.h5')

modelLocationMap = dict()
modelLocationMap['vanilla'] = lambda obj: obj['model_type'] + '/' + obj['model_id'] + '.h5'
modelLocationMap['global'] = lambda obj: obj['model_type'] + '/' + obj['model_id'] + '.h5'
modelLocationMap['private'] = lambda obj: obj['model_type'] + '/' + obj['user'] + '/' + obj['model_id'] + '.h5'

def cleaner(text):
    return ' '.join(tokenizer([text.lower()])[0])

class universalInference(Resource):
    def post(self):
        obj = request.get_json(force=True)
        print(obj)
        if obj['model_id'] not in privateModels:
            # Model not already in memory, load it
            privateModels[obj['model_id']] = tf.keras.models.load_model('./models/' + modelLocationMap[obj['model_type']](obj))
        val = privateModels[obj['model_id']].predict(embed(tf.constant([cleaner(obj['text'])]))[:1])
        rr = sentDict[np.argmax(val)]
        #rr.append(list(val))
        print(rr)
        print(val)
        return jsonify(rr)

# Online Learning APIs ==>
class universalOnlineTrainer(Resource):
    def post(self):
        obj = request.get_json(force=True)
        print(obj)
        x = np.array(embed(tf.constant([cleaner(obj['text'])]))[:1])
        if obj['label'] == 'Negative':
            y = [1., 0.]
        else:
            y = [0., 1.]
        y = np.array([y])
        print(x)
        print(y)
        st = tf.keras.callbacks.EarlyStopping(monitor='accuracy', min_delta=0.1, mode='max', verbose=1, patience=100, restore_best_weights=True)
        privateModels[obj['model_id']].fit(x, y, epochs = 500, callbacks=[st])
        privateModels[obj['model_id']].evaluate(x, y)
        val = privateModels[obj['model_id']].predict(x)
        print(val)
        print(obj['text'])
        return jsonify("Done")

class universalBatchTrainer(Resource):
    def post(self):
        # Format => should consist of data pairs (x, y)
        obj = request.get_json(force=True)
        print(obj)
        X = [cleaner(i[0]) for i in obj['dataset']]
        Y = [i[1] for i in obj['dataset']]
        x = np.array(embed(tf.constant(X)))
        y = keras.utils.to_categorical(np.array(Y))
        #print(x)
        #print(y)
        st = tf.keras.callbacks.EarlyStopping(monitor='accuracy', min_delta=0.1, mode='max', verbose=1, patience=500, restore_best_weights=True)
        privateModels[obj['model_id']].fit(x, y, epochs = 5000, callbacks=[st])
        privateModels[obj['model_id']].evaluate(x, y)
        val = privateModels[obj['model_id']].predict(x)
        print(val)
        print(obj['text'])
        return jsonify("Done")

# Utilities ->

class loadModel(Resource):
    def post(self):
        obj = request.get_json(force=True)
        privateModels[obj['model_id']] = tf.keras.models.load_model('./models' + modelLocationMap[obj['model_type']](obj))
        return jsonify("Loaded")

class saveModel(Resource):
    def post(self):
        obj = request.get_json(force=True)
        privateModels[obj['model_id']].save('./models/' + modelLocationMap[obj['model_type']](obj))
        return jsonify("Saved")

class createModel(Resource):
    def post(self):
        obj = request.get_json(force=True)
        if "No such file or directory" in (subprocess.getoutput("ls ./models/private/" + obj['new']['user'])):
            # If the directory of the user has not been created yet, create it
            r = subprocess.getoutput('mkdir ./models/private/' + obj['new']['user'])
        out = subprocess.getoutput("cp ./models/" + modelLocationMap[obj['original']['model_type']](obj['original']) + " ./models/private/" + obj['new']['user'] + '/' + obj['new']['model_id'] + '.h5')
        return jsonify("Created")


#api.add_resource(vanillaEngine, '/infer/vanilla')
#api.add_resource(globalEngine, '/infer/global')
#api.add_resource(privateEngine, '/infer/private')


api.add_resource(universalInference, '/infer/universal')

api.add_resource(universalOnlineTrainer, '/feedback/universal')
api.add_resource(universalBatchTrainer, '/train/universal')

api.add_resource(saveModel, '/save/universal')
api.add_resource(loadModel, '/load/universal')

api.add_resource(createModel, '/create/universal')

# WARNING: DO NOT RUN THIS ON MULTITHREADED WSGI SERVERS!
if __name__ == '__main__':
     app.run(host='0.0.0.0', port='5000')



