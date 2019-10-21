import warnings
from sklearn.exceptions import DataConversionWarning
warnings.filterwarnings(action='ignore', category=DataConversionWarning)

import sys
from functions import *
import requests
#from bs4 import BeautifulSoup
from datetime import datetime
import re
import pandas as pd
import concurrent.futures
import requests
import threading
import time
from multiprocessing import Pool
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from termcolor import colored
import argparse
from sklearn.externals import joblib
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
import os.path



parser = argparse.ArgumentParser(description='Discover WordPress version with Machine Learning')
parser.add_argument('-m', '--method', help='train or test', type=str, action="store")
parser.add_argument('-gd', '--gendataset', help='Generate a new dataset specifying how much urls do you want ej: --gen-dataset 1000', type=int, action="store")
parser.add_argument('-d', '--dataset', help='Select a dataset .csv', type=str, action="store")
parser.add_argument('-u', '--url', help='Introduce an IP address to scan', type=str, action="store")
args = parser.parse_args()

if args.gendataset:
	df = pd.read_csv('dataset/cols.csv').drop(columns="Unnamed: 0")
	client = df['Files'].values

	df = pd.read_csv('dataset/172-urls.csv')
	urls = df['URLs'].head(200)
	urls = df['URLs'].sample(n=args.gendataset)

	df = pd.DataFrame(columns=client)
	start = time.time()
	print("Creating dataset:")
	print("Checking URLs:")
	df = create_dataset_multiple(urls)

	now = datetime.now()
	time = now.strftime("%Y-%m-%d-%H-%M-%S")
	df.to_csv("dataset/"+time)
	#print(f'Tiempo ejecucion: {time.time() - start}')

elif args.method == "train":
	if not args.dataset:
		print("Dataset not specify using default csv with 20000 urls")
		df = pd.read_csv('dataset/20000.csv')
	else:
		df = pd.read_csv(args.dataset)

	X = df.iloc[:, 1:-1].values
	y = df.iloc[:, -1].values
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
	model = RandomForestClassifier(n_estimators=10, criterion='entropy', random_state=42)
	model.fit(X_train, y_train)
	scores = cross_val_score(model, X_test, y_test, cv=5)
	print("Accuracy Random Forest: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))
	joblib.dump(model, 'randomforestmodel.pkl')


elif args.method == "test":
	if not args.url:
		print("Introduce an url")
		sys.exit()

	if not os.path.exists("randomforestmodel.pkl"):
		sys.exit()

	model = joblib.load('randomforestmodel.pkl')
	print(model)
	X = create_dataset_to_predict(args.url)
	pred = model.predict(X)
	print("[*] WordPress Version: "+pred[0])

else:
    print("Method not valid")



