import serial
import multiprocessing
import serial.threaded


class SerialToQueue(serial.threaded.Protocol):
    def __init__(self, queue):
        self.queue = queue

    def __call__(self):
        return self

    def data_received(self, data):
        self.queue.put(data)


class SerialProcess(multiprocessing.Process):
    def __init__(self, serial2web, web2serial, config):
        multiprocessing.Process.__init__(self)
        self.serial2web = serial2web
        self.web2serial = web2serial

        self.port = config["serial_port"]["port"]
        self.baudrate = config["serial_port"]["baudrate"]

        self.sp = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
        self.sp.flushInput()

        ser_to_net = SerialToQueue(self.serial2web)
        serial_worker = serial.threaded.ReaderThread(self.sp, ser_to_net)
        serial_worker.start()

    def close(self):
        self.sp.close()

    def open(self):
        if self.sp.is_open is False:
            self.sp.open()
            self.sp.flushInput()

    def run(self):
        while True:
            self.sp.write(self.web2serial.get().encode())
