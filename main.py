from flask import Flask, request
from os import system as s

s('pip install flask[async]')
from twilio.twiml.messaging_response import MessagingResponse
import commands as c
import rtfm

app = Flask(__name__)


@app.route("/")
def hello():
	return "Hello, World!"


@app.route("/sms", methods=['POST'])
async def sms_reply():
	msg = request.values.get('Body', '')
	resp = MessagingResponse()

	await c.process_commands(resp, msg)

	if msg.lower().startswith("run"):
		msg = msg.split(" ", 1)
		await rtfm.run(resp, msg[1])

	elif msg.lower().startswith("ref"):
		msg = msg.split(" ", 2)
		await rtfm.reference(resp, msg[1], msg[2])

	elif msg.lower().startswith("doc"):
		msg = msg.split(" ", 2)
		await rtfm.documentation(resp, msg[1], msg[2])

	elif msg.lower().startswith("hash"):
		msg = msg.split(" ", 2)
		await rtfm._hash(resp, msg[1], msg[2])

	elif msg.lower().startswith("list"):
		msg = msg.split(" ", 1)
		await rtfm.list(resp, msg[1])

	elif msg.lower().startswith("ascii"):
		msg = msg.split(" ", 1)
		await rtfm.ascii(resp, msg[1])

	elif msg.lower().startswith("unascii"):
		msg = msg.split(" ", 1)
		await rtfm.unascii(resp, msg[1])

	elif msg.lower().startswith("byteconvert") or msg.lower().startswith(
	    "byc"):
		msg = msg.split(" ", 2)
		await rtfm.byteconvert(resp, msg[1], msg[2])

	elif msg.lower().startswith("man"):
		msg = msg.split(" ", 1)
		await rtfm.man(resp, msg[1])

	return str(resp)


if __name__ == "__main__":
	app.run(debug=True, host='0.0.0.0', port=8888)
