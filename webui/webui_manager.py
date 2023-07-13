import queue
import asyncio
import requests
import threading

from nonebot import logger

from ..config import Plugin_Config

from .webui_proxy import WebUI_Proxy
from .webui_api import WebUI_API


class WebUI_Manager:
    class SubProcesser:
        @staticmethod
        def ping(host: str, port: int) -> str:
            try:
                response = requests.get(
                    "http://" + host + ":" + str(port) + "/internal/ping", timeout=1000
                )
            except:
                response = None

            if response and response.status_code == 200:
                logger.info("PING %s:%d %s" % (host, port, "OK"))
                return "online"
            else:
                logger.info("PING %s:%d %s" % (host, port, "UNVALIABLE"))
                return "offline"

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

    def __init__(self, Global_Config, Config: Plugin_Config) -> None:
        logger.info("正在加载WebUI_Manager")

        # 获取配置项
        self.GlobalConfig = Global_Config
        self.PluginConfig = Config

        # 创建回调队列
        self.TaskRetQueue = queue.Queue()
        self.RetQueueFlag = True
        self.RetQueueListener = threading.Thread(
            target=self.ret_queue_listener, daemon=True
        )
        self.RetQueueListener.start()
        logger.info("回调队列监听线程：%s" % (self.RetQueueListener.is_alive()))

        # 创建队列
        self.TaskQueue = queue.Queue()
        self.ConsumerList: list[WebUI_Proxy] = self.create_consumers()

    def __del__(self):
        self.RetQueueFlag = False
        self.RetQueueListener.join()

    def create_consumers(self):
        # 获取服务器列表
        servers_total = self.PluginConfig.servers

        servers_online = []

        # 检查服务器可用性
        for i in range(len(servers_total)):
            servers_total[i]["avalible"] = WebUI_Manager.SubProcesser.ping(
                servers_total[i]["host"], servers_total[i]["port"]
            )

            if servers_total[i]["avalible"] == "online":
                servers_online.append(servers_total[i])

        logger.info(
            "将加载以下服务器：%s"
            % str([item["host"] + ":" + str(item["port"]) for item in servers_online])
        )

        # 创建消费者列表
        consumers_list = []

        for i in range(len(servers_online)):
            consumers_list.append(
                WebUI_Proxy(self.TaskQueue, self.TaskRetQueue, servers_online[i])
            )

        return consumers_list

    def clear_consumers(self):
        for i in range(len(self.ConsumerList) - 1, -1, -1):
            self.ConsumerList[i].__del__()
            del self.ConsumerList[i]

    def task_queue_clear(self):
        import threading

        lock = threading.Lock()

        with lock:
            while self.TaskQueue.qsize():
                self.TaskQueue.get()
                self.TaskQueue.task_done()

    def ret_queue_listener(self):
        while True:
            # 判断FLAG
            if not self.RetQueueFlag:
                break
            # 获取任务
            task = self.TaskRetQueue.get()
            # 解包并执行
            try:
                callback, bot, event, funcret = task
                asyncio.run(callback(bot, event, funcret))
            except:
                pass
            # 标记完成
            self.TaskRetQueue.task_done()

        return None

    def push_task(self, func, bot, event, callback, *args):
        self.TaskQueue.put((func, bot, event, callback, *args))
        logger.info("压入函数：%s" % str(func))

    def push_task_toall(self, func_list: list[dict]) -> list[dict]:
        """
        func_list结构
        [
            {
                "function": func1,
                "args": args
            },
            {
                "function": func2,
                "args": args
            }
        ]
        res结构
        [
            {
                "info": server1.info,
                "function1_retval": any,
                "function2_retval": any,
                "function3_retval": any
            },
            {
                "info": server2.info,
                "function1_retval": any,
                "function2_retval": any,
                "function3_retval": any
            }
        ]
        """
        res = []

        for server in self.ConsumerList:
            res.append(server.run_funcs_without_queue(func_list))

        return res

    def get_queue_len(self):
        import threading

        lock = threading.Lock()

        with lock:
            queue_len = self.TaskQueue.qsize()

        return queue_len
