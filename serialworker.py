import serial
import time
import multiprocessing
from datetime import datetime

class SerialProcess(multiprocessing.Process):
    def __init__(
        self,
        input_data_queue,
        output_data_queue,
        input_control_queue,
        output_control_queue,
        config,
    ):
        multiprocessing.Process.__init__(self)
        self.input_data_queue = input_data_queue
        self.output_data_queue = output_data_queue
        self.input_control_queue = input_control_queue
        self.output_control_queue = output_control_queue
        self.port = config["serial_port"]["port"]
        self.baudRate = config["serial_port"]["baudrate"]
        self.sp = serial.Serial(self.port, self.baudRate, timeout=1)
        if self.sp.is_open:
            print(
                "success opening port",
                config["serial_port"]["port"],
            )
        else:
            print(
                "failed to open port",
                config["serial_port"]["port"],
            )

    def close(self):
        self.sp.close()

    def writeSerial(self, data):
        self.sp.write(data.encode())
        # time.sleep(1)

    def readSerial(self, n):
        return self.sp.readline()

    def run(self):
        self.sp.flushInput()

        while True:
            # look for incoming tornado request
            if not self.input_data_queue.empty():
                data = self.input_data_queue.get()
                # send it to the serial device
                self.writeSerial(data)
                print("2-writing to serial: ", data)

            # look for incoming serial data
            n = self.sp.inWaiting()
            if n > 0:
                print("read serial n bytes: ", n)
                data = self.readSerial(n)
                print("reading from serial: ", data)
                # send it back to tornado
                self.output_data_queue.put(data)

            print(datetime.now().strftime("%H:%M:%S.%f"))
