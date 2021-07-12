# -*- coding: utf-8 -*-
 
import threading
from queue import Queue
import websocket
import signal
import time

class ThreadForOneChar(threading.Thread):
    """Потоковый загрузчик киллов"""
    
    def __init__(self, queue, ws):
        """Инициализация потока"""
        threading.Thread.__init__(self)
        self.queue = queue
        self.ws = ws
        self.shutdown_flag = threading.Event()
    
    def run(self):
        """Запуск потока"""
        # while True:
        #     # Получаем url из очереди
        print('Start of thread %s:' % self.name)
        url = self.queue.get()
        
        # Скачиваем килл
        while not self.shutdown_flag.is_set():
            #print(self.shutdown_flag.is_set())
            try :
                print('DEBUG-WHILE')
                self.ws.send('{"action":"sub","channel":"alliance:'+url+'"}')
                print(self.ws.recv())
            except websocket._exceptions.WebSocketTimeoutException :
                pass
            except websocket._exceptions.WebSocketConnectionClosedException :
                raise ServiceExit
        
        # Отправляем сигнал о том, что задача завершена
        self.queue.task_done()
    
    @staticmethod
    def service_shutdown(signum, frame):
        print('Caught signal %d' % signum)
        raise ServiceExit  

class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass

def main(urls):
    """
    Запускаем программу
    """
    signal.signal(signal.SIGINT,ThreadForOneChar.service_shutdown)
    signal.signal(signal.SIGTERM, ThreadForOneChar.service_shutdown)

    queue = Queue()
    threads = []
    #websocket.enableTrace(True)

    websocket.setdefaulttimeout(3)
    # Запускаем потом и очередь

    try:

        for i in range(len(urls)):
            print('DEBUG-FOR')
            ws = websocket.create_connection("wss://zkillboard.com/websocket/")
            threads.append(ThreadForOneChar(queue, ws))
            threads[-1].start()       

        # Даем очереди нужные нам ссылки для скачивания
        for url in urls:
            queue.put(url)

        while True :
            time.sleep(.5)

    except ServiceExit :
        for i in threads :
            i.shutdown_flag.set()
        for i in threads :
            i.join()
    
    # Ждем завершения работы очереди
    queue.join()

if __name__ == "__main__":

    urls = []
    with open('ids1.txt') as OP :
        urls = OP.read().replace('\n', '').split(',')
    
    main(urls)