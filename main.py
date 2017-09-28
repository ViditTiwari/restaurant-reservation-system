import webapp2
import json
import requests
import requests_toolbelt.adapters.appengine
import os
import traceback

from sqlhelper import DBHelper

from reservation_bot import handle_updates

requests_toolbelt.adapters.appengine.monkeypatch()

db = DBHelper()
db.setup()

def make_requests(update=None):
	if not update:
		text = chat_id = None
	else:
		text = update["message"]["text"]
		chat_id = update["message"]["chat"]["id"]

	my_json = {"text":text, "chat_id": chat_id}
	url = "https://posthere.io/e8e4-49fa-aea4"
	r = requests.post(url, json = my_json)


class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Bot Initialized\n')


class DataInfoPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		cursor = db.conn.cursor()
		
		#Show databases
		self.response.write('\nDATABASES\n')
		cursor.execute('SHOW DATABASES')
		for r in cursor.fetchall():
			self.response.write('{}\n'.format(r))
		
		#Show tables
		self.response.write('\nTABLES\n')
		cursor.execute('SHOW TABLES')
		for r in cursor.fetchall():
			self.response.write('{}\n'.format(r))

		#Show logs
		self.response.write('\nLOGS\n')
		cursor.execute('SELECT * FROM logs')
		for r in cursor.fetchall():
			self.response.write('{}\n'.format(r))

		#Show rows
		self.response.write('\nROWS\n')
		cursor.execute('SELECT * FROM bookings')
		for r in cursor.fetchall():
			self.response.write('{}\n'.format(r))


class WebHookHandler(webapp2.RequestHandler):
	def get(self):
		self.response.write("hey")

	def post(self):
		json_content = json.loads(self.request.body)
		try:
			handle_updates(json_content)
		except:
			tb = traceback.format_exc()
			db.add_log(str(tb))


app = webapp2.WSGIApplication([
	('/', MainPage),
	('/info', DataInfoPage),
	('/webhook/bot427284879:AAG5eLO4geFp5QpqujEC9SpHiGmZE108Hvs', WebHookHandler),
], debug=True)
