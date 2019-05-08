#!/usr/bin/python3
from flask import *
from flask_restful import *
from json import dumps

from AIengine import *

app = Flask(__name__)
api = Api(app)

privateModels = dict()
def cleaner(text):
    return text.lower

class vanillaEngine(Resource):
    def post(self):
        obj = request.get_json(force=True)
        print(obj)
        val = evalModel.predict(embed(tf.constant([cleaner(obj['text'])]))[:1])
        rr = sentDict[np.argmax(val)]
        #rr.append(list(val))
        print(rr)
        return jsonify(rr)

class globalEngine(Resource):
    def post(self):
        obj = request.get_json(force=True)
        print(obj)
        return None

class privateEngine(Resource):
    def post(self):
        obj = request.get_json(force=True)
        print(obj)
        if obj['model_id'] not in privateModels:
            # Model not already in memory, load it
            privateModels[obj['model_id']] = tf.keras.models.load_model('./models/private/' + obj['model_id'] + '.h5')
        val = privateModels[obj['model_id']].predict(embed(tf.constant([obj['sentence']]))[:1])
        rr = sentDict[np.argmax(val)]
        #rr.append(list(val))
        print(rr)
        print(val)
        return jsonify(rr)

# Online Learning APIs ==>
class privateOnlineTrainer(Resource):
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

class privateBatchTrainer(Resource):
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

class privateOnlineLoad(Resource):
    def post(self):
        obj = request.get_json(force=True)
        privateModels[obj['model_id']] = tf.keras.models.load_model('./models/private/' + obj['model_id'] + '.h5')
        return jsonify("Loaded")

class privateOnlineSave(Resource):
    def post(self):
        obj = request.get_json(force=True)
        privateModels[obj['model_id']].save('./models/private/' + obj['model_id'] + '.h5')
        return jsonify("Saved")

api.add_resource(vanillaEngine, '/infer/vanilla')
api.add_resource(globalEngine, '/infer/global')
api.add_resource(privateEngine, '/infer/private')

api.add_resource(privateOnlineTrainer, '/feedback/private')
api.add_resource(privateBatchTrainer, '/train/private')
api.add_resource(privateOnlineSave, '/save/private')
api.add_resource(privateOnlineLoad, '/load/private')

# WARNING: DO NOT RUN THIS ON MULTITHREADED WSGI SERVERS!
if __name__ == '__main__':
     app.run(port='5000')

