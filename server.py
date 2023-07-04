import webbrowser
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.gen
from tornado.options import define, options

# import os
# import time
import multiprocessing
import serialworker
import json
import configparser

from dataclasses import dataclass

@dataclass
class serverQueueIo:
    input: multiprocessing.Queue()
    output: multiprocessing.Queue()


@dataclass
class serverQueue:
    data: serverQueueIo
    control: serverQueueIo


clients = []
server_queue = serverQueue(
    data=(serverQueueIo(multiprocessing.Queue(), multiprocessing.Queue())),
    control=(serverQueueIo(multiprocessing.Queue(), multiprocessing.Queue())),
)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class StaticFileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.js")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        print("new connection")
        clients.append(self)
        print("clients len: ", len(clients))
        self.write_message("connected")

    def on_message(self, message):
        print("tornado received from client: %s" % json.dumps(message))
        server_queue.data.input.put(message)

    def on_close(self):
        print("connection closed")
        clients.remove(self)


# check the queue for pending messages, and rely that to all connected clients
def checkQueue():
    if not server_queue.data.output.empty():
        message = server_queue.data.output.get()
        for c in clients:
            c.write_message(message)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("./server.cfg")
    webPort = config["web_server"]["port"]
    # start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess(server_queue, config)
    sp.daemon = True
    sp.start()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./"}),
            (r"/ws", WebSocketHandler),
        ]
    )
    httpServer = tornado.httpserver.HTTPServer(app)
    httpServer.listen(webPort)

    mainLoop = tornado.ioloop.IOLoop.instance()
    # adjust the scheduler_interval according to the frames sent by the serial port
    scheduler_interval = 100
    scheduler = tornado.ioloop.PeriodicCallback(
        checkQueue, scheduler_interval, io_loop=mainLoop
    )

    url = "http://127.0.0.1:" + str(webPort)
    print("Listening on ", url)
    webbrowser.open(url)

    scheduler.start()
    mainLoop.start()
