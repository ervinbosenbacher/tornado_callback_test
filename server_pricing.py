from flask import Flask, request
import json
import requests

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Pricing'


@app.route("/execute", methods=["POST"])
def do_something():
    data = json.loads(request.data)
    print(f"server_pricing: {data}")
    data["quote_number"] = f"QUOTE_NUMBER_{data['price']}"

    # get the callback URL and send the result back to callback
    resp = requests.post(data["url_callback"], data=json.dumps(data))
    print(f"server_pricing: {resp.text}")

    # this is the immediate response
    return data


