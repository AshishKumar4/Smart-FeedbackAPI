
import pickle
import numpy as np
import json
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers
import keras
from sklearn.model_selection import train_test_split
import keras.backend as K
import seaborn as sn
import pandas as pd
from sklearn.metrics import *
import sklearn
import re
import tensorflow_hub as hub

np.random.seed(10)
embed_method = 'nnlm128'

print("\nLoading embedding layer...")
embed = hub.load("https://tfhub.dev/google/tf2-preview/nnlm-en-dim128/1")
print("Fetched the hub module...")
sentDict = {0:["Negative", "Red"], 1:["Positive", "Green"]}