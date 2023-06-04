import queue
import asyncio
import requests
import threading

from nonebot import logger

from ..config import WebUI_Config

from .webui_proxy import WebUI_Proxy
from .webui_api import WebUI_API


class WebUI_Manager():

    class SubProcesser():

        @staticmethod
        def ping(host: str, port: int) -> str:

            try:
                response = requests.get(
                    'http://' + host + ':' + str(port) + '/internal/ping',
                    timeout=1000
                )
            except:
                response = None

            if response and response.status_code == 200:
                logger.info("PING %s:%d %s" % (host, port, "OK"))
                return ("online")
            else:
                logger.info("PING %s:%d %s" % (host, port, "UNVALIABLE"))
                return ("offline")

            # timeout = 5

            # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # sock.settimeout(timeout)

            # result = sock.connect_ex((host, port))

            # sock.close()

            # if result == 0:
            #     return ("online")
            # else:
            #     return ("offline")

        @staticmethod
        def wait(status: str):
            response = WebUI_Manager.SubProcesser.ping()
            while response != status:
                response = WebUI_Manager.SubProcesser.ping()

    def __init__(self, Config: WebUI_Config) -> None:
        logger.info("正在加载WebUI_Manager")

        # 获取配置项
        self.Config = Config

        # 创建回调队列
        self.TaskRetQueue = queue.Queue()
        self.RetQueueFlag = True
        self.RetQueueListener = threading.Thread(
            target=self.ret_queue_listener, daemon=True)
        self.RetQueueListener.start()

        # 创建队列
        self.TaskQueue = queue.Queue()
        self.ConsumerList: list[WebUI_Proxy] = self.create_consumers()

    def __del__(self):
        self.RetQueueFlag = False
        self.RetQueueListener.join()

    def create_consumers(self):
        # 获取服务器列表
        servers_total = self.Config.servers

        servers_online = []

        # 检查服务器可用性
        for i in range(len(servers_total)):
            servers_total[i]['avalible'] = WebUI_Manager.SubProcesser.ping(
                servers_total[i]['host'], servers_total[i]['port']
            )

            if servers_total[i]['avalible'] == 'online':
                servers_online.append(
                    servers_total[i]
                )

        logger.info("将加载以下服务器：%s" %
                    str([item['host'] + ":" + str(item['port']) for item in servers_online]))

        # 创建消费者列表
        consumers_list = []

        for i in range(len(servers_online)):
            consumers_list.append(
                WebUI_Proxy(
                    self.TaskQueue, self.TaskRetQueue, servers_online[i]
                )
            )

        return consumers_list

    def clear_consumers(self):
        for i in range(len(self.ConsumerList)-1, -1, -1):
            self.ConsumerList[i].__del__()
            del self.ConsumerList[i]

    def ret_queue_listener(self):

        while True:
            # 判断FLAG
            if not self.RetQueueFlag:
                break
            # 获取任务
            task = self.TaskRetQueue.get()
            # 解包并执行
            callback, bot, event, funcret = task
            asyncio.run(callback(bot, event, funcret))
            # 标记完成
            self.TaskRetQueue.task_done()

        return None

    def push_task(self, func, bot, event, callback, *args):
        self.TaskQueue.put(
            (func, bot, event, callback, *args)
        )
        logger.info("压入函数：%s" % str(func))

    def push_task_toall(self, func, *args):
        res = []
        for item in self.ConsumerList:
            res.append(item.direct_func_without_queue(func, *args))

        res_unique = []
        for item in res:
            if item not in res_unique:
                res_unique.append(item)

        return res_unique

    def get_queue_len(self):
        import threading
        lock = threading.Lock()

        with lock:
            queue_len = self.TaskQueue.qsize()

        return queue_len
