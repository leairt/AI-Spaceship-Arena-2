import ctypes
import os
import time
from datetime import datetime
from threading import Timer, Thread

import config


class Timeout(Exception):
    pass


def send_thread_exception(*args):
    for t_id in args:
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(t_id), ctypes.py_object(Timeout))
        if not res:
            print(f'ERR: Thread {t_id} not found')
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(t_id, 0)
            print(f'ERR: Failed to send exception to thread {t_id}')


class TimedFunction(Thread):
    def __init__(self, parent_id, queue, max_time_sec, method, *args):
        super().__init__()
        self.parent_id = parent_id
        self.queue = queue
        self.max_time_sec = max_time_sec
        self.method = method
        self.args = args

    def get_id(self):
        return self.ident

    def run(self) -> None:
        if self.max_time_sec:
            timer = Timer(interval=self.max_time_sec,
                          function=send_thread_exception, args=[self.ident, self.parent_id])
            timer.start()
        else:
            timer = None
        try:
            start_time = time.time()
            result = self.method(*self.args)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.queue.put((result, elapsed_time), block=False)
        except Timeout:
            pass
        except Exception as e:
            raise e
        finally:
            if timer:
                timer.cancel()


class Logger:
    def __init__(self):
        if not os.path.exists(config.LOG_FOLDER):
            os.mkdir(config.LOG_FOLDER)
        self.lg = open(os.path.join(config.LOG_FOLDER, f'LOG_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.txt'), 'w')

    def close(self):
        self.lg.close()

    def log(self, message, kind='', to_std_out=False):
        self.lg.write((txt := f'{kind}: {message}') + '\n')
        if to_std_out:
            print(txt)

    def log_info(self, message, to_std_out=False):
        self.log(message, 'INFO', to_std_out)

    def log_error(self, message, to_std_out=False):
        self.log(message, 'ERROR', to_std_out)
