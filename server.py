import webbrowser
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

import tornado.gen
from tornado.options import define, options
import multiprocessing
import serialworker
import configparser

clients = []
serial2web = multiprocessing.Queue()
web2serial = multiprocessing.Queue()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("./static/index.html")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.append(self)

    def on_message(self, message):
        web2serial.put(message)

    def on_close(self):
        clients.remove(self)


# check the queue for pending messages, and rely that to all connected clients
def checkQueue():
    if not serial2web.empty():
        message = serial2web.get()
        for c in clients:
            c.write_message(message)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("./server.cfg")
    webPort = config["web_server"]["port"]
    # start the serial worker in background (as a deamon)
    sp = serialworker.SerialProcess(serial2web, web2serial, config)
    sp.daemon = True
    sp.start()
    app = tornado.web.Application(
        handlers=[
            (r"/", IndexHandler),
            (r"/ws", WebSocketHandler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
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
