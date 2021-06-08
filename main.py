from flask import Flask, request
from os import system as s
s('pip install flask[async]')
from twilio.twiml.messaging_response import MessagingResponse
import commands as c

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello, World!"

@app.route("/sms", methods=['POST'])
async def sms_reply():
	msg = request.values.get('Body', '').lower()


	resp = MessagingResponse()
	await c.process_commands(resp, msg)

	return str(resp)

if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=8888)