import queue
import threading

from nonebot import logger

from .webui_api import WebUI_API


class WebUI_Proxy:
    def __init__(self, queue: queue.Queue, retqueue: queue.Queue, info: dict) -> None:
        # 获取队列
        self.Queue = queue
        self.RetQueue = retqueue
        # 获取当前服务器信息
        self.info = info

        # 创建队列监听线程
        self.QueueFlag = True
        self.QueueListener = threading.Thread(target=self.queue_listener, daemon=True)
        self.QueueListener.start()
        logger.info(
            "队列监听线程：%s:%d %s"
            % (info["host"], info["port"], self.QueueListener.is_alive())
        )
        self.info["listen"] = self.QueueListener.is_alive()

    def __del__(self) -> None:
        # 停止队列监听线程
        self.QueueFlag = False

    def queue_listener(self):
        while self.QueueFlag:
            # 判断服务器状态
            self.info["avalible"] = WebUI_API.ping(self.info["host"], self.info["port"])

            # 不接任务，挂起线程
            if self.info["avalible"] == False or self.info["select"].is_set() == False:
                self.info["select"].clear()
                self.info["select"].wait()
                continue

            # 获取任务
            task = self.Queue.get()

            # 判断服务器状态
            self.info["avalible"] = WebUI_API.ping(self.info["host"], self.info["port"])

            if self.info["avalible"]:
                # 解包并执行
                try:
                    func, bot, event, callback, *args = task
                    funcret = None
                    funcret = func(self.info["host"], self.info["port"], *args)
                except:
                    logger.error(
                        "%s:%s 任务执行失败！" % (self.info["host"], self.info["port"])
                    )

                # 启动回调函数
                if funcret:
                    try:
                        self.RetQueue.put((callback, bot, event, funcret))
                    except:
                        logger.error(
                            "%s:%s 回调任务执行失败！" % (self.info["host"], self.info["port"])
                        )

            else:
                # 离线，重新压入
                self.Queue.put((func, bot, event, callback, *args))
                logger.info("服务器离线，重压入函数：%s" % str(func))

            self.Queue.task_done()

        return None

    def run_funcs_without_queue(self, func_list: list[dict]) -> dict:
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
        {
            "info": server.info,
            "function1_retval": any,
            "function2_retval": any,
            "function3_retval": any,
        }
        """
        res = {"info": self.info}

        for function_info in func_list:
            args = function_info["args"]
            try:
                if args == None:
                    res.update(
                        {
                            function_info["function"].__name__: function_info[
                                "function"
                            ](self.info["host"], self.info["port"]),
                        }
                    )
                else:
                    res.update(
                        {
                            function_info["function"].__name__: function_info[
                                "function"
                            ](self.info["host"], self.info["port"], *args),
                        }
                    )
            except:
                logger.debug("fail run_funcs_without_queue")

        return res
