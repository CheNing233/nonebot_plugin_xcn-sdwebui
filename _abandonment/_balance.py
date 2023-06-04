import queue
import threading


class LoadBalancing():

    def __init__(self) -> None:
        # 线程安全队列
        self.FIFO_Queue = queue.Queue()
        self.Queue_Consumer = threading.Thread(target=self._queue_consumer)
        self.Queue_Consumer.start()

    def _queue_consumer(self):

        while True:
            # 获取任务
            task = self.FIFO_Queue.get()
            # 解包并执行
            func, *args = task
            func(*args)
            # 标记完成
            self.FIFO_Queue.task_done()

    def thread_reload(self):
        self.Queue_Consumer.join(timeout=0.1)
        self.Queue_Consumer.start()

    def thread_alive(self):
        return self.Queue_Consumer.is_alive()

    def add_task(self, func, *args):
        # 载入函数
        self.FIFO_Queue.put(
            (func, *args)
        )

    def get_len(self):
        return self.FIFO_Queue.qsize()
