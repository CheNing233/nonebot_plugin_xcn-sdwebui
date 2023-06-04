import queue
import threading

from nonebot import logger


class WebUI_Proxy():

    def __init__(self, queue: queue.Queue, retqueue: queue.Queue, info: dict) -> None:
        # 获取队列
        self.Queue = queue
        self.RetQueue = retqueue
        # 获取当前服务器信息
        self.info = info

        # 创建队列监听线程
        self.QueueFlag = True
        self.QueueListener = threading.Thread(
            target=self.queue_listener, daemon=True)
        self.QueueListener.start()
        logger.info(
            "队列监听线程：%s:%d %s" % (
                info['host'],
                info['port'],
                self.QueueListener.is_alive()
            ))

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
            func, bot, event, callback, *args = task
            funcret = None
            funcret = func(self.info['host'], self.info['port'], *args)
            # 标记完成
            if funcret:
                self.RetQueue.put((callback, bot, event, funcret))
            self.Queue.task_done()

        return None

    def direct_func_without_queue(self, func, *args):
        return func(self.info['host'], self.info['port'], *args)
