import queue
import threading

from nonebot import logger


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
        self.info["avalible"] = self.QueueListener.is_alive()

    def __del__(self) -> None:
        # 停止队列监听线程
        self.QueueFlag = False
        if self.QueueListener.is_alive():
            self.QueueListener.join()

    def queue_listener(self):
        while True:
            # 判断FLAG
            if not self.QueueFlag:
                break
            # 获取任务
            task = self.Queue.get()
            # 解包并执行
            try:
                func, bot, event, callback, *args = task
                funcret = None
                funcret = func(self.info["host"], self.info["port"], *args)
            except:
                pass
            # 标记完成
            if funcret:
                self.RetQueue.put((callback, bot, event, funcret))
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
            if args == None:
                res.update(
                    {
                        function_info["function"].__name__: function_info["function"](
                            self.info["host"], self.info["port"]
                        ),
                    }
                )
            else:
                res.update(
                    {
                        function_info["function"].__name__: function_info["function"](
                            self.info["host"], self.info["port"], *args
                        ),
                    }
                )

        return res
