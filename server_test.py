import pytest
import tornado.web
import os
from os.path import isfile, join
from tornado.web import Application
from tornado import gen
import requests
import json
import threading
import bottle
import queue
import logging
import sys

log = logging.getLogger()
log.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

message_queue = queue.Queue()

@bottle.post('/callback')
def callback():
    body = bottle.request.body.read()
    message_queue.put(body)
    log.info(f"server_callback: {body}")

class MainHandler(tornado.web.RequestHandler):    
    @gen.coroutine
    def get(self):
        self.write("Hello, world")

    @tornado.gen.coroutine
    def post(self):
        # this is where we get the pricing request json...
        data_s = self.request.body
        data_j = json.loads(data_s)
        log.info(f"server_test payload: {data_j}")
        resp = requests.post("http://localhost:5000/execute", data=data_s)

        # immediate response
        # check for RAML types
        log.info(f"{resp.text} {resp.status_code}")

        # delayed response with the actual quote coming from the pricing server
        # comes from the queue. The queue is fed by the callback call.
        # we check here the RAML types
        quote = message_queue.get() # blocking for simplicity
        quote_j = json.loads(quote)
        log.info(f"quote: {quote_j}")
        assert quote_j['price'] == data_j['price']

class ApplicationServer(Application):
    def __init__(self):
        handlers = [
            (r"/execute", MainHandler)
        ]
        super(ApplicationServer, self).__init__(handlers)

# test suite
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIR = os.path.join(TEST_DIR, 'request_files')
FIXTURE_FILES = [
    os.path.join(FIXTURE_DIR, name)
    for name in os.listdir(FIXTURE_DIR) if isfile(join(FIXTURE_DIR, name))
]

@pytest.fixture
def app():
    server = ApplicationServer()
    return server

@pytest.mark.gen_test
def test_tornado_get(http_client, base_url):
    log.info(f"base_url: {base_url}")
    response = yield http_client.fetch(f"{base_url}/execute")
    log.info(f"test_tornado_get: {response.body}")
    assert response.code == 200

@pytest.mark.datafiles(*FIXTURE_FILES)
@pytest.mark.gen_test
def test_tornado_post(http_client, base_url, datafiles):
    # start the server which receives the callback
    callback_thread = threading.Thread(target=bottle.run, kwargs={'host': '0.0.0.0', 'port': 8888})
    callback_thread.setDaemon(True)
    callback_thread.start()

    # read all the files and send them using post to the pricing server
    for request_file in datafiles.listdir():
        with open(request_file, "r") as f:
            data_s = f.read()
            data_j = json.loads(data_s)
            log.info(f"test_tornado_post: {os.path.basename(f.name)} {data_j}")
            response = yield http_client.fetch(f"{base_url}/execute", method="POST", headers=None, body=data_s)
            assert response.code == 200


