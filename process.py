import sys
import os
import argparse
import asyncio
import time
import random
import json
import re

from nonebot import on_regex, on_notice
from nonebot.adapters import Bot, Event, Message
from nonebot.adapters.onebot.v11 import Event as v11event
from nonebot.adapters.onebot.v12 import Event as v12event
from nonebot.adapters.telegram import Event as tgevent
from nonebot.adapters.feishu import Event as fsevent
from nonebot.log import logger

from .protocol.default import Default_Protocol

from .utils.transfers import StdTransfer
from .utils.text import TextOptimization

from .sdapi.param import ParameterOperation

from .protocol.default import Default_Protocol
from .protocol.onebotv11 import OneBotV11_Protocol
from .protocol.feishu import Feishu_Protocol
from .protocol.telegram import Telegram_Protocol


class Process:
    @classmethod
    def inject_params(cls, func):
        async def wrapper(bot: Bot, event: Event):
            """
            注入流水号
            """
            # 获取当前时间戳，精确到毫秒级别
            current_time = int(time.time() * 1000)

            # 取时间戳后六位并加上两位随机数
            code = str(current_time)[-4:] + str(random.randint(10, 99))

            logger.info(f"启动 {code}{func.__name__}")

            """
            注入协议处理器
            """
            if isinstance(event, v11event):
                logger.info("注入 OneBotV11_Protocol")
                protocol = OneBotV11_Protocol

            elif isinstance(event, v12event):
                logger.info("注入 OneBotV12_Protocol")
                # protocol = OneBotV12_Protocol
                pass

            elif isinstance(event, tgevent):
                logger.info("注入 Telegram_Protocol")
                protocol = Telegram_Protocol

            elif isinstance(event, fsevent):
                logger.info("注入 Feishu_Protocol")
                protocol = Feishu_Protocol

            else:
                logger.info("注入 Default_Protocol")
                protocol = Default_Protocol

            try:
                await func(bot, event, protocol, code)
            except StdTransfer.StdStopEvent:
                logger.info(f"{code}{func.__name__} 被弹出")

            logger.info(f"{code}{func.__name__} 结束")

        return wrapper

    @staticmethod
    def check_result(res: StdTransfer.NodeResult):
        if isinstance(res, StdTransfer.NodeResult) is False:
            logger.error(f"{res.nodeinfo['host']}:{res.nodeinfo['port']} 请求结果非法")
            return False, "结果非法"

        if res.result is None:
            logger.error(f"{res.nodeinfo['host']}:{res.nodeinfo['port']} 请求节点层结果为空")
            return False, "节点层结果为空"

        if res.result.result is None:
            logger.error(
                f"{res.nodeinfo['host']}:{res.nodeinfo['port']} 请求过程中API层出现 {res.result.info}"
            )
            return False, res.result.info

        logger.info(f"{res.nodeinfo['host']}:{res.nodeinfo['port']} 请求结果检验正常")
        return True, "结果正常"

    def __init__(self, balancer) -> None:
        self.balancer = balancer

        # self.event_on_notice = on_notice(block=False)

        self.cmd_sd = on_regex(pattern=r"(#sd)\b", priority=5, block=True)

        self.cmd_sddraw = on_regex(pattern=r"(#sddraw)\b", priority=5, block=True)

        self.cmd_sdextra = on_regex(pattern=r"(#sdextra)\b", priority=5, block=True)

        self.cmd_sdtxt = on_regex(pattern=r"(#sdtxt)\b", priority=5, block=True)

        self.cmd_sdimg = on_regex(pattern=r"(#sdimg)\b", priority=5, block=True)

        self.cmd_sdext = on_regex(pattern=r"(#sdext)\b", priority=5, block=True)

        self.cmd_sdtagger = on_regex(pattern=r"(#sdtagger)\b", priority=5, block=True)

        self.cmd_sdlst = on_regex(pattern=r"(#sdlst)\b", priority=5, block=True)

        self.cmd_sdskip = on_regex(pattern=r"(#sdskip)\b", priority=5, block=True)

        self.cmd_sdfrev = on_regex(pattern=r"(#sdfrev)\b", priority=5, block=True)

        self.cmd_sdinf = on_regex(pattern=r"(#sdinf)\b", priority=5, block=True)

        @self.cmd_sd.handle()
        @self.inject_params
        async def _sd(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sd", "").strip()

            # 创建解析器对象
            parser = argparse.ArgumentParser(add_help=False)

            # 添加子解析器
            subparsers = parser.add_subparsers(dest="command")

            # 添加子参数定义
            add_parser = subparsers.add_parser("add", help="添加一个节点")
            add_parser.add_argument("-name", type=str, default=None, help="节点名称")
            add_parser.add_argument("-host", type=str, default=None, help="主机地址")
            add_parser.add_argument("-port", type=int, default=7860, help="端口号(默认7860)")
            add_parser.add_argument("-prio", type=int, default=6, help="优先级(默认6)")

            # 添加主参数定义
            # parser.add_argument(
            #     "-add", metavar="节点JSON配置", type=str, default=None, help="添加一个节点"
            # )
            parser.add_argument(
                "-delete", metavar="节点名称", type=str, default=None, help="删除一个节点"
            )
            parser.add_argument(
                "-act", metavar="节点名称", type=str, default=None, help="启用一个节点"
            )
            parser.add_argument(
                "-ban", metavar="节点名称", type=str, default=None, help="停用一个节点"
            )
            parser.add_argument(
                "-find", metavar="节点名称", type=str, default=None, help="查找一个节点"
            )
            parser.add_argument(
                "-skip", metavar="节点名称", type=str, default=None, help="让某个节点跳过一张"
            )
            parser.add_argument(
                "-skipall", metavar="节点名称", type=str, default=None, help="让某个节点跳过全部"
            )
            parser.add_argument("-alloc", action="store_true", help="启动分发")
            parser.add_argument("-stop", action="store_true", help="停止分发，并放弃所有未分发任务")
            parser.add_argument("-t", action="store_true", help="列出当前任务")
            parser.add_argument("-h", action="store_true", help="调出help菜单")

            help_text = parser.format_help()

            try:
                args = parser.parse_args(text.split())
            except:
                return None

            if args.h:
                # 获取当前运行的入口文件的名称（包括路径）
                entry_file = sys.argv[0]

                # 去掉路径，只保留文件名
                entry_filename = os.path.basename(entry_file)

                help_text = help_text.replace(entry_filename, "#sd")

                await bot.send(event, help_text)
                return None

            if args.t:
                task_dict = self.balancer.get_all_tasks()
                reply = await protocol.msg_dict(task_dict)
                await bot.send(event, f"当前一共 {len(task_dict)} 任务喵~\n{reply}")
                return None

            if args.command == "add":
                try:
                    if args.name is None or args.host is None:
                        raise RuntimeError("Not give NAME or HOST")

                    host_match = re.search(r"(?<=\[).+(?=\])", args.host)

                    target_node_json = {
                        "name": args.name,
                        "host": host_match.group()
                        if host_match is not None
                        else args.host,
                        "port": args.port,
                        "priority": args.prio,
                    }

                    self.balancer.add_node_cfg(target_node_json)

                    await bot.send(event, f"添加成功正在重启喵~")

                    self.balancer.reset_tasks_context()
                    await self.balancer.reload_nodes()

                    await bot.send(event, f"重启完毕喵~")
                except:
                    await bot.send(event, f"添加失败喵~")

                return None

            if args.delete:
                try:
                    self.balancer.del_node_cfg(args.delete)

                    await bot.send(event, f"删除成功正在重启喵~")

                    self.balancer.reset_tasks_context()
                    await self.balancer.reload_nodes()

                    await bot.send(event, f"重启完毕喵~")
                except:
                    await bot.send(event, f"删除失败喵~")

                return None

            if args.act:
                await bot.send(event, f"启用 {self.balancer.act_node(args.act)} 喵~")
                return None

            if args.ban:
                await bot.send(event, f"禁用 {self.balancer.ban_node(args.ban)} 喵~")
                return None

            if args.find:
                target_node = self.balancer.find_node(args.find)
                await bot.send(
                    event,
                    f"找到 {target_node.name}:{target_node.host}:{target_node.port} 喵~",
                )
                return None

            if args.skip:
                target_node = self.balancer.find_node(args.skip)
                await bot.send(event, f"正在弹出 {target_node.name} 的一张喵~")
                await self.balancer.fanout_task(
                    StdTransfer.StdParams(command="skip"), user_nodes_list=[target_node]
                )
                await bot.send(event, "已全部弹出喵~")
                return None

            if args.skipall:
                target_node = self.balancer.find_node(args.skip)
                await bot.send(event, f"正在弹出 {target_node.name} 的全部喵~")
                await self.balancer.fanout_task(
                    StdTransfer.StdParams(command="stop"), user_nodes_list=[target_node]
                )
                await bot.send(event, "已全部弹出喵~")
                return None

            if args.alloc:
                await bot.send(
                    event, f"当前 分发控制=={self.balancer.start_task_distribution()} 喵~"
                )
                return None

            if args.stop:
                await bot.send(
                    event, f"当前 分发控制=={self.balancer.stop_task_distribution()} 喵~"
                )
                return None

            # 并发 get_vram get_progress
            res_async = await asyncio.gather(
                self.balancer.fanout_task(StdTransfer.StdParams(command="get_vram")),
                self.balancer.fanout_task(
                    StdTransfer.StdParams(command="get_progress")
                ),
            )

            vram_nodes_result: list = res_async[0]
            progress_nodes_result: list = res_async[1]

            # 保持索引一致
            for vram_result, progress_result in zip(
                vram_nodes_result, progress_nodes_result
            ):
                if str(vram_result.nodeinfo) != str(progress_result.nodeinfo):
                    vram_nodes_result.sort(key=lambda x: str(x.nodeinfo))
                    progress_nodes_result.sort(key=lambda x: str(x.nodeinfo))
                    break

            # 构造返回文本
            reply = protocol.msg_nodeinfo(
                vram_nodes_result, progress_nodes_result, check=self.check_result
            )

            await bot.send(event, reply)

        @self.cmd_sddraw.handle()
        @self.inject_params
        async def _sddraw(
            bot: Bot, event: Event, protocol: Default_Protocol, code: str
        ):
            text = event.get_plaintext().replace("#sddraw", "").strip()

            # 获取回复的那条消息的图片
            raw_images = await protocol.get_image_from_reply(bot, event)

            # 提取参数
            raw_params: dict = ParameterOperation.extract_params(
                text,
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group,
            )

            if not raw_images:
                payload: dict = ParameterOperation.txt2img_params_normalization(
                    raw_params
                )

                await bot.send(event, f"压入一段咒语喵，流水号是 {code} 喵~")

                node_result = await self.balancer.push_queue_task(
                    StdTransfer.StdParams(
                        command="txt2img", params={"params": payload}, code=code
                    )
                )

            else:
                payload = ParameterOperation.img2img_params_normalization(
                    raw_params, raw_images
                )

                await bot.send(event, f"压入一张二向箔喵，流水号是 {code} 喵~")

                node_result = await self.balancer.push_queue_task(
                    StdTransfer.StdParams(
                        command="img2img", params={"params": payload}, code=code
                    )
                )

            check, _ = self.check_result(node_result)

            if not check:
                await bot.send(event, f"法阵 {code} 爆炸，已被停止喵")
                return None

            await bot.send(event, f"画完 {code} 了喵，正在弹出喵~")

            generate_images: list = node_result.result.result.images

            reply_images: list = await protocol.msg_image(bot, event, generate_images)

            for reply_image in reply_images:
                await bot.send(event, Message(reply_image))

        @self.cmd_sdextra.handle()
        @self.inject_params
        async def _sdextra(
            bot: Bot, event: Event, protocol: Default_Protocol, code: str
        ):
            text = event.get_plaintext().replace("#sdextra", "").strip()

            # 获取回复的那条消息的图片
            raw_images = await protocol.get_image_from_reply(bot, event)

            # 提取参数
            raw_params: dict = ParameterOperation.extract_params(
                text,
                ParameterOperation.extra_matcher.patterns_dict,
                ParameterOperation.extra_matcher.base_params,
                [],
                ParameterOperation.extra_matcher.float_group,
                ParameterOperation.extra_matcher.bool_group,
                [],
            )

            if not raw_images:
                await bot.send(event, f"没有二向箔是展不开的喵...")
                return None
            else:
                payload = ParameterOperation.extra_params_normalization(
                    raw_params, raw_images
                )

                await bot.send(event, f"展开一张二向箔喵，流水号是 {code} 喵~")

                node_result = await self.balancer.push_queue_task(
                    StdTransfer.StdParams(
                        command="extra", params={"params": payload}, code=code
                    )
                )

            check, _ = self.check_result(node_result)

            if not check:
                await bot.send(event, f"法阵 {code} 爆炸，已被停止喵")
                return None

            await bot.send(event, f"展完 {code} 了喵，正在弹出喵~")

            generate_images: list = node_result.result.result.images

            reply_images: list = await protocol.msg_image(bot, event, generate_images)

            for reply_image in reply_images:
                await bot.send(event, Message(reply_image))

        @self.cmd_sdinf.handle()
        @self.inject_params
        async def _sdinf(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sdinf", "").strip()

            # 获取回复的那条消息的图片
            raw_images = await protocol.get_image_from_reply(bot, event)

            if not raw_images:
                await bot.send(event, f"没有二向箔是求不了导的喵...")
                return None

            # 创建解析器对象
            parser = argparse.ArgumentParser(add_help=False)

            # 添加参数定义
            parser.add_argument("-tagger", action="store_true", help="启动 tagger 插件进行反推")
            parser.add_argument("-h", action="store_true", help="调出help菜单")

            # 获取帮助信息的字符串形式
            help_text = parser.format_help()

            try:
                args = parser.parse_args(text.split())
            except:
                return None

            if args.h:
                # 获取当前运行的入口文件的名称（包括路径）
                entry_file = sys.argv[0]

                # 去掉路径，只保留文件名
                entry_filename = os.path.basename(entry_file)

                help_text = help_text.replace(entry_filename, "#sdinf")

                await bot.send(event, help_text)

                return None

            # 使用tagger插件反推
            elif args.tagger:
                params: dict = ParameterOperation.extract_params(
                    text,
                    ParameterOperation.tagger_matcher.patterns_dict,
                    ParameterOperation.tagger_matcher.base_params,
                    [],
                    ParameterOperation.tagger_matcher.float_group,
                    [],
                    [],
                )

                # tagger插件导图片元数据
                tagger_node_result = await self.balancer.push_queue_task(
                    StdTransfer.StdParams(
                        command="tagger_image",
                        params={"params": params, "image": raw_images[0]},
                        code=code,
                    )
                )

                check, _ = self.check_result(tagger_node_result)

                if check is False:
                    await bot.send(event, "嗷呜, 导爆法阵了喵~")
                    return None

                taggerinfo = tagger_node_result.result.result

                for key in taggerinfo["rating"]:
                    taggerinfo["rating"][key] = "{:.2f}%".format(
                        taggerinfo["rating"][key] * 100
                    )

                tagger_tags = ", ".join(taggerinfo["tag"])
                tagger_rating = await protocol.msg_dict(taggerinfo["rating"])

                await bot.send(
                    event, f"涩涩鉴定喵\n{tagger_rating}\nTagger反推喵\n{tagger_tags}"
                )

            # 导图片元数据
            else:
                pnginfo_node_result = await self.balancer.push_queue_task(
                    StdTransfer.StdParams(
                        command="png_info", params={"image": raw_images[0]}, code=code
                    )
                )

                check, _ = self.check_result(pnginfo_node_result)

                if check is False:
                    await bot.send(event, "嗷呜, 导爆法阵了喵~")
                    return None

                pnginfo = pnginfo_node_result.result.result

                if pnginfo:
                    await bot.send(event, f"导出图片元数据如下喵\n{pnginfo}")
                else:
                    await bot.send(event, "导不出元数据喵")

        @self.cmd_sdtxt.handle()
        @self.inject_params
        async def _sdtxt(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sdtxt", "").strip()

            params: dict = ParameterOperation.extract_params(
                event.get_plaintext().replace("#sdtxt", ""),
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group,
            )

            """
            修正str类型参数
            """

            user_sampler = params.get("sampler_name", None)
            user_upscaler = params.get("hr_upscaler", None)
            user_vae = params.get("sd_vae", None)
            user_model = params.get("sd_model_checkpoint", None)

            tasks = [
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_sampler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_hires_upscaler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_extra_upscaler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_vae")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_model")
                    )
                ),
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

            result_list = []

            for i in range(len(tasks)):
                try:
                    result_list = []
                    index = done.index(tasks[i])

                    for node_result in done[index]:
                        check, _ = self.check_result(node_result)

                        if check is False:
                            continue

                        result_list += node_result.result.result

                    result_list = list(tuple(result_list))

                    if i == 0:
                        params["sampler_name"] = TextOptimization.find_similar_str(
                            result_list, user_sampler
                        )
                    if i == 1:
                        upscalers = result_list
                    if i == 2:
                        upscalers += result_list
                        params["hr_upscaler"] = TextOptimization.find_similar_str(
                            upscalers, user_upscaler
                        )
                    if i == 3:
                        params["sd_vae"] = TextOptimization.find_similar_str(
                            result_list, user_vae
                        )
                    if i == 4:
                        params[
                            "sd_model_checkpoint"
                        ] = TextOptimization.find_similar_str(result_list, user_model)
                except:
                    continue

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_txt2img.json"
            )

            if text:
                reply = await protocol.msg_dict(params)
                await bot.send(event, f"新的 txt2img 参数喵：\n{reply}")
            else:
                reply = await protocol.msg_dict(params_final)
                await bot.send(event, f"全部 txt2img 参数喵：\n{reply}")

        @self.cmd_sdimg.handle()
        @self.inject_params
        async def _sdimg(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sdimg", "").strip()

            params: dict = ParameterOperation.extract_params(
                text,
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group,
            )

            """
            修正str类型参数
            """

            user_sampler = params.get("sampler_name", None)
            user_upscaler = params.get("hr_upscaler", None)
            user_vae = params.get("sd_vae", None)
            user_model = params.get("sd_model_checkpoint", None)

            tasks = [
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_sampler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_hires_upscaler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_extra_upscaler")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_vae")
                    )
                ),
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_model")
                    )
                ),
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

            result_list = []

            for i in range(len(tasks)):
                try:
                    result_list = []
                    index = done.index(tasks[i])

                    for node_result in done[index]:
                        check, _ = self.check_result(node_result)

                        if check is False:
                            continue

                        result_list += node_result.result.result

                    result_list = list(tuple(result_list))

                    if i == 0:
                        params["sampler_name"] = TextOptimization.find_similar_str(
                            result_list, user_sampler
                        )
                    if i == 1:
                        upscalers = result_list
                    if i == 2:
                        upscalers += result_list
                        params["hr_upscaler"] = TextOptimization.find_similar_str(
                            upscalers, user_upscaler
                        )
                    if i == 3:
                        params["sd_vae"] = TextOptimization.find_similar_str(
                            result_list, user_vae
                        )
                    if i == 4:
                        params[
                            "sd_model_checkpoint"
                        ] = TextOptimization.find_similar_str(result_list, user_model)
                except:
                    continue

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_img2img.json"
            )

            if text:
                reply = await protocol.msg_dict(params)
                await bot.send(event, f"新的 img2img 参数喵：\n{reply}")
            else:
                reply = await protocol.msg_dict(params_final)
                await bot.send(event, f"全部 img2img 参数喵：\n{reply}")

        @self.cmd_sdext.handle()
        @self.inject_params
        async def _sdext(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sdext", "").strip()

            params: dict = ParameterOperation.extract_params(
                text,
                ParameterOperation.extra_matcher.patterns_dict,
                ParameterOperation.extra_matcher.base_params,
                [],
                ParameterOperation.extra_matcher.float_group,
                ParameterOperation.extra_matcher.bool_group,
                [],
            )

            """
            修正str类型参数
            """

            user_extraupscaler_1 = params.get("upscaler_1", None)
            user_extraupscaler_2 = params.get("upscaler_2", None)

            tasks = [
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="get_or_match_extra_upscaler")
                    )
                ),
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

            result_list = []

            for i in range(len(tasks)):
                try:
                    result_list = []
                    index = done.index(tasks[i])

                    for node_result in done[index]:
                        check, _ = self.check_result(node_result)

                        if check is False:
                            continue

                        result_list += node_result.result.result

                    result_list = list(tuple(result_list))

                    if i == 0:
                        if user_extraupscaler_1:
                            params["upscaler_1"] = TextOptimization.find_similar_str(
                                result_list, user_extraupscaler_1
                            )
                        if user_extraupscaler_2:
                            params["upscaler_2"] = TextOptimization.find_similar_str(
                                result_list, user_extraupscaler_2
                            )

                except:
                    continue

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_extra.json"
            )

            if text:
                reply = await protocol.msg_dict(params)
                await bot.send(event, f"新的 extra 参数喵：\n{reply}")
            else:
                reply = await protocol.msg_dict(params_final)
                await bot.send(event, f"全部 extra 参数喵：\n{reply}")

        @self.cmd_sdtagger.handle()
        @self.inject_params
        async def _sdtagger(
            bot: Bot, event: Event, protocol: Default_Protocol, code: str
        ):
            text = event.get_plaintext().replace("#sdtagger", "").strip()

            params: dict = ParameterOperation.extract_params(
                text,
                ParameterOperation.tagger_matcher.patterns_dict,
                ParameterOperation.tagger_matcher.base_params,
                [],
                ParameterOperation.tagger_matcher.float_group,
                [],
                [],
            )

            """
            修正str类型参数
            """

            user_tagger_model = params.get("model", None)

            tasks = [
                asyncio.ensure_future(
                    self.balancer.fanout_task(
                        StdTransfer.StdParams(command="tagger_get_models")
                    )
                ),
            ]

            done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

            result_list = []

            for i in range(len(tasks)):
                try:
                    result_list = []
                    index = done.index(tasks[i])

                    for node_result in done[index]:
                        check, _ = self.check_result(node_result)

                        if check is False:
                            continue

                        result_list += node_result.result.result

                    result_list = list(tuple(result_list))

                    if i == 0:
                        params["model"] = TextOptimization.find_similar_str(
                            result_list, user_tagger_model
                        )

                except:
                    continue

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_tagger.json"
            )

            if text:
                reply = await protocol.msg_dict(params)
                await bot.send(event, f"新的 tagger 参数喵：\n{reply}")
            else:
                reply = await protocol.msg_dict(params_final)
                await bot.send(event, f"全部 tagger 参数喵：\n{reply}")

        @self.cmd_sdlst.handle()
        @self.inject_params
        async def _sdlst(bot: Bot, event: Event, protocol: Default_Protocol, code: str):
            text = event.get_plaintext().replace("#sdlst", "").strip()

            # 创建解析器对象
            parser = argparse.ArgumentParser(add_help=False)

            # 添加参数定义
            parser.add_argument("-model", action="store_true", help="可用模型")
            parser.add_argument("-vae", action="store_true", help="可用VAE模型")
            parser.add_argument(
                "-hires", action="store_true", help="可用的Latent Upscale Modes"
            )
            parser.add_argument("-extra", action="store_true", help="可用的Upscaler")
            parser.add_argument("-sampler", action="store_true", help="可用的Sampler")
            parser.add_argument("-embed", action="store_true", help="可用的Embeddings")
            parser.add_argument("-lora", action="store_true", help="可用的Lora和Lycoris")
            parser.add_argument("-tagger", action="store_true", help="可用的Tagger反推模型")
            parser.add_argument("-h", action="store_true", help="调出help菜单")

            # 获取帮助信息的字符串形式
            help_text = parser.format_help()

            try:
                args = parser.parse_args(text.split())
            except:
                return None

            if args.h:
                # 获取当前运行的入口文件的名称（包括路径）
                entry_file = sys.argv[0]

                # 去掉路径，只保留文件名
                entry_filename = os.path.basename(entry_file)

                help_text = help_text.replace(entry_filename, "#sdtxt")

                await bot.send(event, help_text)

            async def get_list(command, **params):
                nodes_result: list = await self.balancer.fanout_task(
                    StdTransfer.StdParams(command=command, params=params)
                )

                result_list = []

                for node_result in nodes_result:
                    check, _ = self.check_result(node_result)

                    if check is False:
                        continue

                    result_list += node_result.result.result

                result_list = list(tuple(result_list))

                reply = await protocol.msg_list(result_list)

                await bot.send(event, reply)

            if args.model:
                await bot.send(event, "正在导出 model 列表喵~")
                await get_list("get_or_match_model")

            if args.vae:
                await bot.send(event, "正在导出 vae 列表喵~")
                await get_list("get_or_match_vae")

            if args.hires:
                await bot.send(event, "正在导出 latent upscale modes 列表喵~")
                # await get_list("get_or_match_model")
                latent_nodes_result: list = await self.balancer.fanout_task(
                    StdTransfer.StdParams(command="get_or_match_hires_upscaler")
                )
                extra_nodes_result: list = await self.balancer.fanout_task(
                    StdTransfer.StdParams(
                        command="get_or_match_extra_upscaler",
                        params={"add_pth_detailed": True},
                    )
                )

                result_list = []

                for node_result in latent_nodes_result + extra_nodes_result:
                    check, _ = self.check_result(node_result)

                    if check is False:
                        continue

                    result_list += node_result.result.result

                result_list = list(tuple(result_list))

                reply = await protocol.msg_list(result_list)

                await bot.send(event, reply)

            if args.extra:
                await bot.send(event, "正在导出 upscalers 列表喵~")
                await get_list("get_or_match_extra_upscaler", add_pth_detailed=True)

            if args.sampler:
                await bot.send(event, "正在导出 sampler 列表喵~")
                await get_list("get_or_match_sampler")

            if args.embed:
                await bot.send(event, "正在导出 embedding 列表喵~")
                await get_list("get_or_match_embeddings")  #

            if args.lora:
                await bot.send(event, "正在导出 lora/lycoris 列表喵~")
                await get_list("get_or_match_loras")

            if args.tagger:
                await bot.send(event, "正在导出 tagger model 列表喵~")
                await get_list("tagger_get_models")
