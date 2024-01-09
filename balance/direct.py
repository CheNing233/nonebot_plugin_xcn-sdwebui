import queue
import asyncio
import requests
import threading
import time

# from nonebot import logger
from typing import List
from pathlib import Path

from ..utils.text import TextOptimization
from ..utils.config import ConfigLoader
from ..utils.transfers import StdTransfer


class Direct_Balancer:
    """
    基于协程的任务管理系统
    """

    def event_set_one_node_available(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.one_node_available.set()
            return result

        return wrapper

    def __init__(self, node_class, logger) -> None:
        self.node_class = node_class
        self.nodes_cfg = self.get_nodes_cfg()
        self.nodes = list()

        self.logger = logger
        self.logger.info("使用 Direct_Balancer")

        self.reset_tasks_context()
        self.init_nodes()

    def reset_tasks_context(self):
        self.tasks = {}

        # 停止任务分发标志
        self.stop_task_alloc = asyncio.Event()
        self.stop_task_alloc.clear()

        # 至少一个节点可用标志
        self.one_node_available = asyncio.Event()
        self.one_node_available.set()

        # 任务分发完成
        self.task_complete_alloc = asyncio.Event()
        self.task_complete_alloc.set()

    def get_nodes_cfg(self):
        """
        获取节点配置
        """
        return ConfigLoader(
            str(Path(__file__).parent.resolve() / "config" / "nodes.json")
        )

    @event_set_one_node_available
    def add_node_cfg(self, node_json: dict):
        """
        添加节点配置
        """
        name = node_json.get("name", None)
        host = node_json.get("host", None)
        port = node_json.get("port", None)
        priority = node_json.get("priority", None)

        if name and host and port and priority:
            _node_json = {
                "name": str(name),
                "host": str(host),
                "port": int(port),
                "priority": int(priority),
            }
            self.nodes_cfg.data["nodes"].append(_node_json)
            self.nodes_cfg.save_json()
        else:
            raise RuntimeError("JSON that does not meet requirements")

        return None

    @event_set_one_node_available
    def del_node_cfg(self, node_name: str):
        """
        删除节点配置
        """
        node_index = self.find_node_cfg(node_name)

        del self.nodes_cfg.data["nodes"][node_index]
        self.nodes_cfg.save_json()

        return None

    def find_node_cfg(self, node_name: str) -> int:
        """
        搜索（一个）节点配置
        """
        name_list = [node_cfg["name"] for node_cfg in self.nodes_cfg.data["nodes"]]

        return name_list.index(TextOptimization.find_similar_str(name_list, node_name))

    @event_set_one_node_available
    def init_nodes(self):
        """
        初始化节点列表
        """
        for node_cfg in self.nodes_cfg.data["nodes"]:
            self.nodes.append(self.node_class(node_cfg, self.logger))

        self.logger.info(f"从配置中启动 {len(self.nodes)} 个节点")

        async def ping():
            ping_coros = [node.get_status() for node in self.nodes]
            await asyncio.gather(*ping_coros)

        asyncio.run(ping())

    @event_set_one_node_available
    async def reload_nodes(self):
        """
        重载节点列表
        """
        self.logger.info("正在重新初始化 Direct_Balancer")

        self.nodes = list()

        for node_cfg in self.nodes_cfg.data["nodes"]:
            self.nodes.append(self.node_class(node_cfg, self.logger))

        self.logger.info(f"从配置中重新启动 {len(self.nodes)} 个节点")

        ping_coros = [node.get_status() for node in self.nodes]
        await asyncio.gather(*ping_coros)

        self.logger.info("Direct_Balancer 重初始化完成")

    def find_node(self, name: str):
        """
        搜索一个已载入的节点
        """
        name_list = [
            "{}|{}|{}".format(node.name, node.host, node.port) for node in self.nodes
        ]

        similiar_name = TextOptimization.find_similar_str(name_list, name)

        return self.nodes[name_list.index(similiar_name)]

    @event_set_one_node_available
    def act_node(self, node_name: str) -> str:
        """
        启用一个节点
        """
        target_node = self.find_node(node_name)
        target_node.is_ban = False
        return f"{target_node.name}:{target_node.host}:{target_node.port}"

    @event_set_one_node_available
    def ban_node(self, node_name: str) -> str:
        """
        禁用一个节点
        """
        target_node = self.find_node(node_name)
        target_node.is_ban = True
        return f"{target_node.name}:{target_node.host}:{target_node.port}"

    @event_set_one_node_available
    def stop_task_distribution(self):
        """
        停止任务分发
        """
        self.stop_task_alloc.set()
        return self.stop_task_alloc.is_set()

    @event_set_one_node_available
    def start_task_distribution(self):
        """
        启动任务分发
        """
        self.stop_task_alloc.clear()
        return self.stop_task_alloc.is_set()

    def get_all_tasks(self):
        """
        获取任务列表
        """
        return self.tasks

    async def get_available_nodes(self, disable_condition: list = []):
        """
        获取可用节点列表
        """
        available_nodes = []

        while True:
            available_nodes = []

            for node in self.nodes:
                # 筛选可用的node放入列表
                await node.get_status()  # fresh node status
                if (node.is_available is True) and (node.is_ban is False):
                    available_nodes.append(node)

            if len(available_nodes) == 0:
                # 无节点可用
                self.one_node_available.clear()

                wait_list = [asyncio.ensure_future(self.one_node_available.wait())]

                # 失能条件
                wait_list += disable_condition

                # 等待至少一个节点可用
                done, pending = await asyncio.wait(
                    wait_list, return_when=asyncio.FIRST_COMPLETED
                )

                # 获取索引
                sema_index = wait_list.index(list(done)[0])

                # 立即失能本函数
                if sema_index >= 1:
                    return None

            else:
                break

        return available_nodes

    async def get_FIHP_node(self, disable_condition: list = []):
        """
        获取第一个空闲的高优先级节点
        """
        # 等待一个可用节点
        available_nodes = await self.get_available_nodes(disable_condition)

        if available_nodes is None:
            return None

        # 按priority排序
        available_nodes.sort(key=lambda x: x.priority)

        # 构造信号量列表
        available_nodes_sema = [
            asyncio.ensure_future(node.sem_working.wait()) for node in available_nodes
        ]

        # 添加失能条件
        available_nodes_sema += disable_condition

        # 等待第一个可用信号量
        done, pending = await asyncio.wait(
            available_nodes_sema, return_when=asyncio.FIRST_COMPLETED
        )

        # 获取可用节点索引
        available_node_index = available_nodes_sema.index(list(done)[0])

        # 立即失能本函数
        if available_node_index >= len(available_nodes):
            return None

        return available_nodes[available_node_index]

    def get_HP_task(self, priority):
        if not self.tasks:
            return None

        priority_list = self.get_task_priority_list()

        if priority_list:
            return True if priority == min(priority_list) else False
        else:
            return True

    def flag_task_signup(self, code, command, priority: float = None):
        if priority is None:
            priority_list = self.get_task_priority_list()

            if priority_list:
                priority = max(priority_list) + 1
            else:
                priority = 1

        self.tasks[str(code)] = {
            f"{code}": f"{command} 等待",
            f" {code}_priority": priority,
        }

    def flag_task_proccess(self, code, command, host, port):
        try:
            self.tasks[str(code)][f"{code}"] = f"{command} 运行中"
            del self.tasks[str(code)][f" {code}_priority"]
            self.tasks[str(code)][f" {code}_node"] = f"{host}:{port}"
        except:
            self.logger.warning(f"Direct_Balancer {code} 可能已被清理, 停止继续执行")
            raise StdTransfer.StdStopEvent()

    def flag_task_delete(self, code):
        try:
            del self.tasks[str(code)]
        except:
            self.logger.warning(f"Direct_Balancer {code} 可能已被清理, 停止继续执行")
            raise StdTransfer.StdStopEvent()

    def change_task_priority(self, code, new_priority: float = None):
        try:
            if new_priority is None:
                self.tasks[str(code)][f" {code}_priority"] -= 1
            else:
                self.tasks[str(code)][f" {code}_priority"] = new_priority
        except:
            self.logger.warning(f"Direct_Balancer {code} 可能已被清理, 停止继续执行")
            raise StdTransfer.StdStopEvent()

    def get_task_priority(self, code):
        try:
            return self.tasks[str(code)][f" {code}_priority"]
        except:
            self.logger.warning(f"Direct_Balancer {code} 可能已被清理, 停止继续执行")
            raise StdTransfer.StdStopEvent()

    def get_task_priority_list(self) -> list:
        priority_list = []

        for task_key in self.tasks:
            if self.tasks[task_key].get(f" {task_key}_priority", None):
                priority_list.append(self.tasks[task_key][f" {task_key}_priority"])
            else:
                continue

        return priority_list

    @event_set_one_node_available
    async def push_queue_task(
        self, params: StdTransfer.StdParams, priority: float = None
    ) -> StdTransfer.NodeResult:
        """
        压入一个任务到队列（信号量阻塞方法）
        """
        # 注册任务
        self.logger.info(f"Direct_Balancer 注册任务 {params.command}_{params.code}")
        self.flag_task_signup(params.code, params.command, priority)

        # 高优先级任务抢占节点
        while True:
            self.task_complete_alloc.clear()

            # 获取第一个空闲的高优先级节点
            available_node = await self.get_FIHP_node(
                [asyncio.ensure_future(self.stop_task_alloc.wait())]
            )

            # 获取第一个可用空闲节点失败
            if available_node is None:
                # 注销任务
                self.flag_task_delete(params.code)
                self.logger.info(f"Direct_Balancer 停止处理 {params.command}_{params.code}")
                raise StdTransfer.StdStopEvent()

            # 确定自身为最高优先级任务 否则重新等待节点
            if self.get_HP_task(self.get_task_priority(params.code)):
                # 抢占
                available_node.sem_working.clear()
                break
            else:
                # 等待其他节点抢占
                await self.task_complete_alloc.wait()
                continue

        # 使用该节点执行任务
        self.flag_task_proccess(
            params.code, params.command, available_node.host, available_node.port
        )

        node_result: StdTransfer.NodeResult = await available_node.call_api(params)

        # 注销任务
        self.flag_task_delete(params.code)
        available_node.sem_working.set()
        self.logger.info(f"Direct_Balancer 结束处理 {params.command}_{params.code}")

        # 标志抢占完成 解除保护
        self.task_complete_alloc.set()

        return node_result

    @event_set_one_node_available
    async def fanout_task(
        self, params: StdTransfer.StdParams, user_nodes_list: list = None
    ) -> List[StdTransfer.NodeResult]:
        """
        扇出一个任务（不计入任务列表）
        """
        nodes_list = user_nodes_list if (user_nodes_list is not None) else self.nodes
        nodes_result = []

        for node in nodes_list:
            node_result: StdTransfer.NodeResult = await node.call_api(params)
            nodes_result.append(node_result)

        return nodes_result
