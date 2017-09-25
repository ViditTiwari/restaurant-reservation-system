import json
import requests
import time
import urllib.parse

import config
from info_extraction import extract_names, extract_email_addresses
from dbhelper import DBHelper

import smtplib
from email.mime.text import MIMEText

db = DBHelper()

TOKEN = config.token

URL = "https://api.telegram.org/bot{}/".format(TOKEN)

available_tables = ['1', '2', '3', '4', '5']

confirm_choices = ['yes', 'no']

details_dict = {"Name":0, "Email":1, "Table Number":2}

help_message = '''/start : Starting conversation with Restaurant Table Reservation System \n
/help : Providing you with all the available commands and information about them \n
/retrieve: Get the table number you booked for \n
/receipt: Get the reciept for the order \n
/cancel: Cancel your confirmed booking \n'''

start_message = '''Welcome to Jumper Restaurant Table Reservation System. We will be helping you throughout the table reservation process.\n
Send /help if you need any other information.'''

single_slash_message = '''Forgot the commands. Type /help to get the list.'''

step_0_message = "Tell us your name."

step_1_message = "Tell us your email address."

step_2_message = "Great. Now select the table from the available options."

step_3_message = "Thanks for providing the information. Provided details are: \n"

confirm_message = "Your booking is confirmed. Thank you for using Jumper Restaurant Table Reservation System. Have a nice day."

discard_message = "You have chosen not to confirm your booking. To start again type /start"

cancel_message = "Your booking has been cancelled. To start again type /start"


def get_url(url):
	response = requests.get(url)
	content = response.content.decode("utf8")
	return content


def get_json(url):
	content = get_url(url)
	json_content = json.loads(content)
	return json_content


def get_updates(offset=None):
	url = URL + "getUpdates"
	if offset:
		url += "?offset={}".format(offset)
	json_content = get_json(url)
	return json_content


def get_last_update_id(updates):
	update_ids = []
	for update in updates["result"]:
		update_ids.append(int(update["update_id"]))
	return max(update_ids)


def build_keyboard(items):
	keyboard = [[item] for item in items]
	reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
	return json.dumps(reply_markup)


def get_available_choices():
	record = db.get_booked_tables()
	global available_tables
	
	if record:
		not_available = [str(item[0]) for item in record]
		local_available_tables = [table for table in available_tables if table not in not_available]
		available_tables = local_available_tables
		return available_tables
	else:
		return available_tables


def get_step_message(step, chat, text=None):
	if step == 0:
		return step_0_message
	elif step == 1:
		return step_1_message
	elif step == 2:
		return step_2_message
	elif step ==3:
		booking_details = db.get_bookings(chat)
		message = step_3_message + "\n"
		for key, value in details_dict.items():
			if key == "Table Number" and text not in [None, '/start']:
				message += key + ": "+ str(text) +"\n"
			else:
				message += key + ": "+ str(booking_details[0][value]) +"\n"

		message+="\nDo you confirm (Select from the options) ?"

		return message
	elif step == 4:
		return confirm_message


def determine_step(chat):
	record = db.get_bookings(chat)
	step = 0
	if record:
		step = 1
		if record[0][1]:
			step = 2
		if record[0][2]:
			step = 3
		if record[0][3]:
			step = 4

	print (record, step)
	return step, record


def send_message(text, chat_id, reply_markup=None):
	text = urllib.parse.quote_plus(text)
	url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
	if reply_markup:
		url += "&reply_markup={}".format(reply_markup)
	get_url(url)


def retrieve_table_no(step, record):
	if step == 4:
		return "Booking Table No : " + str(record[0][2])
	else:
		return "Your don't have any booking. Type /start to start booking procedure."


def generate_receipt(step, record):
	if step == 4:
		message = "Receipt: \n\n"
		for key, value in details_dict.items():
			message += key + ": "+ str(record[0][value]) +"\n"

		message += "Confirmed: Yes"
		return message
	else:
		return "Your don't have any booking. Type /start to start booking procedure."

def cancel_booking(chat, step, record):
	if step == 4:
		db.delete_booking(chat)
		return cancel_message
	else:
		return "Your don't have any booking. Type /start to start booking procedure."

def send_mail(receipt, record):
	msg = MIMEText(receipt)
	msg['Subject'] = 'Booking Confirmation'
	msg['From'] = config.login_address
	msg['To'] = str(record[0][1])

	try:
		s = smtplib.SMTP_SSL(config.mail_server, config.mail_server_port)
		s.login(config.login_address, config.password)
		s.send_message(msg)
		s.quit()
	except SMTPException:
		pass



def handle_updates(updates):
	for update in updates["result"]:
		text = update["message"]["text"]
		chat = update["message"]["chat"]["id"]
		step, record = determine_step(chat)

		if text == "/start":
			send_message(start_message, chat)
			step_message = get_step_message(step, chat, text)
			if step == 2 :
				keyboard = build_keyboard(get_available_choices())
				if available_tables:
					print(available_tables)
					send_message(step_message, chat, keyboard)
				else:
					db.delete_booking(chat)
					send_message("Currently all tables are occupied. Please try after sometime.", chat)
			elif step == 3:
				keyboard = build_keyboard(confirm_choices)
				send_message(step_message, chat, keyboard)
			else:
				send_message(step_message, chat)

		elif text == "/retrieve":
			message = retrieve_table_no(step, record)
			send_message(message, chat)

		elif text == "/receipt":
			receipt = generate_receipt(step, record)
			send_message(receipt, chat)

		elif text == "/cancel":
			message = cancel_booking(chat, step, record)
			send_message(message, chat)

		elif text == "/help":
			send_message(help_message, chat)

		elif text.startswith("/"):
			send_message(single_slash_message, chat)

		else:
			step_message = get_step_message(step+1, chat, text)
			if step == 0:
				name = extract_names(text)
				if name:
					db.add_name(name[0], chat)
					send_message(step_message, chat)
				else:
					send_message("Hey we didn't get your name. Please tell us your name again", chat)

			elif step == 1 :
				email_address = extract_email_addresses(text)
				if email_address:
					db.add_email(email_address[0], chat)
					keyboard = build_keyboard(get_available_choices())
					send_message(step_message, chat, keyboard)
				else:
					send_message("Hey we didn't get your email. Please tell us your email again", chat)

			elif step == 2:
				if available_tables:
					if text in available_tables:
						db.add_table_booking(text, chat)
						keyboard = build_keyboard(confirm_choices)
						send_message(step_message, chat, keyboard)
					else:
						keyboard = build_keyboard(get_available_choices())
						send_message("You have provided wrong input. Please provide correct input.", chat, keyboard)
				else:
					send_message("Currently all tables are occupied. Please try after sometime.", chat)

			elif step == 3:
				if text == 'yes':
					db.confirm_booking(chat)
					send_message(confirm_message, chat)
					receipt = generate_receipt(step+1, record)
					send_message(receipt, chat)
					send_mail(receipt, record)
				elif text == 'no':
					db.delete_booking(chat)
					send_message(discard_message, chat)
				else:
					keyboard = build_keyboard(confirm_choices)
					send_message("You have provided wrong input. Please provide correct input.", chat, keyboard)
					


def main():
	db.setup()
	last_update_id = None
	while True:
		updates = get_updates(last_update_id)
		if len(updates["result"]) > 0:
			last_update_id = get_last_update_id(updates) + 1
			handle_updates(updates)
		time.sleep(0.5)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		raise