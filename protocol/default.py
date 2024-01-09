from nonebot.log import logger
from nonebot.adapters import Bot, Event, Message, MessageSegment

from tabulate import tabulate


class Default_Protocol:
    @staticmethod
    def msg_nodeinfo(
        vram_nodes_result: list, progress_nodes_result: list, **kwarg
    ) -> str:
        check = kwarg.get("check", None)

        """
        构造表格
        """
        table = []

        for vram_result, progress_result in zip(
            vram_nodes_result, progress_nodes_result
        ):
            """
            常规信息
            """
            name = vram_result.nodeinfo["name"]
            host = vram_result.nodeinfo["host"]
            port = vram_result.nodeinfo["port"]
            is_available = vram_result.nodeinfo["is_available"]
            is_ban = vram_result.nodeinfo["is_ban"]
            priority = vram_result.nodeinfo["priority"]
            sem_working = vram_result.nodeinfo["sem_working"].is_set()

            if check is not None:
                check_1, _ = check(vram_result)
                check_2, _ = check(progress_result)
            else:
                check_1 = True
                check_2 = True

            if check_1 and check_2:
                """
                正常信息
                """
                (
                    vram_free,
                    vram_used,
                    vram_total,
                    vram_percent,
                ) = vram_result.result.result

                (
                    job_count,
                    eta_relative,
                    progress,
                    sampling_step,
                    sampling_steps,
                ) = progress_result.result.result

                """
                node state
                """
                if is_available:
                    if is_ban is False:
                        if job_count > 0:
                            indicator = "🔵"
                        else:
                            indicator = "🟢"
                    else:
                        indicator = "⚪"
                else:
                    indicator = "🔴"

                table += [
                    [
                        f"{indicator}{job_count}",
                        "{} {:.0f}%".format(name, progress),
                    ],
                    ["节点", f"{host}:{port} ({priority})"],
                    [
                        "进度",
                        "{:.2f}s ({:.0f}/{:.0f})".format(
                            eta_relative, sampling_step, sampling_steps
                        ),
                    ],
                    [
                        "显存",
                        "{:.0f}% ({:.2f}/{:.2f})".format(
                            vram_percent, vram_used, vram_total
                        ),
                    ],
                ]

            else:
                """
                丢失链接信息
                """
                logger.info(f"{host}:{port} 任务失败")

                indicator = "🔴"

                table += [
                    [
                        f"{indicator}{0}",
                        "{} {:.1f}%".format(name, 0),
                    ],
                    ["节点", f"{host}:{port} ({priority})"],
                ]

        return tabulate(table, tablefmt="simple")

    @classmethod
    async def msg_dict(cls, target: dict, _in_recursion=False) -> str:
        """
        构造字典消息
        """
        # 提取键值对
        extracted_keyvalue = {}
        for key, value in target.items():
            if isinstance(value, dict):
                extracted_keyvalue.update(await cls.msg_dict(value, True))
            else:
                extracted_keyvalue[key] = value

        if _in_recursion:
            return extracted_keyvalue
        else:
            return "\n".join(
                [
                    "{} = {}".format(key, value)
                    for key, value in extracted_keyvalue.items()
                ]
            )

    @staticmethod
    async def msg_list(target: list) -> str:
        return "\n".join(target)

    @staticmethod
    async def msg_image(bot: Bot, event: Event, images: list):
        pass

    @staticmethod
    async def get_image_from_reply(bot: Bot, event: Event):
        pass
