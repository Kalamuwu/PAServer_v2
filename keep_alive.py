from flask import Flask
from threading import Thread
from random import randint


app = Flask('')

@app.route('/')
def home():
	return '<code>Bot ready</code>'

def run():
  app.run(
		host='0.0.0.0',
		port=randint(2000,9000)
	)

def keep_alive():
	'''
	Creates and starts new thread that runs the function `run.`
	'''
	t = Thread(target=run)
	t.start()