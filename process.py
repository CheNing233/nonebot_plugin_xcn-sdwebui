from nonebot import on_regex, on_notice
from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Event as v11event
from nonebot.adapters.telegram import Event as tgevent
from nonebot.adapters.console import Event as cmdevent
from nonebot.adapters.feishu import Event as fsevent
from nonebot.log import logger

from .webui.webui_manager import WebUI_Manager
from .webui.webui_api import WebUI_API

from .utils.msg import UniversalMessageBuilder
from .utils.param import ParameterOperation

from .protocol.default import Default_Protocol
from .protocol.onebotv11 import OneBotV11_Protocol
from .protocol.console import Console_Protocol
from .protocol.feishu import Feishu_Protocol
from .protocol.telegram import Telegram_Protocol


class Message_Processer:
    @staticmethod
    def protocol(event: Event):
        if isinstance(event, v11event):
            return OneBotV11_Protocol

        elif isinstance(event, cmdevent):
            return Console_Protocol

        elif isinstance(event, tgevent):
            return Telegram_Protocol

        elif isinstance(event, fsevent):
            return Feishu_Protocol

        else:
            return Default_Protocol

    @staticmethod
    def init_protocol(plugin_config, global_cofig):
        try:
            Feishu_Protocol.app_config = global_cofig.feishu_bots
        except:
            logger.error("Fail to init config")
            pass

    def __init__(self, manager: WebUI_Manager) -> None:
        self.Manager = manager

        Message_Processer.init_protocol(
            self.Manager.PluginConfig, self.Manager.GlobalConfig
        )

        # self.event_on_message = on_message(block=False)

        self.event_on_notice = on_notice(block=False)

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

        # @self.event_on_message.handle()
        # async def _event_on_message(bot: Bot, event: Event):
        #     pass

        @self.event_on_notice.handle()
        async def _event_on_notice(bot: Bot, event: Event):
            if hasattr(event, "file"):
                await bot.send(event, event.file.id)

        @self.cmd_sd.handle()
        async def _sd(bot: Bot, event: Event):
            command = event.get_plaintext().replace("#sd", "").strip()

            if command == "":
                res, ingnore = self.Manager.push_task_toall(
                    [
                        {"function": WebUI_API.get_vram, "args": None},
                        {"function": WebUI_API.get_progress, "args": None},
                    ]
                )

                msg = UniversalMessageBuilder.server_info(
                    self.Manager.get_queue_len(),
                    res,
                    ingnore,
                    WebUI_API.get_vram.__name__,
                    WebUI_API.get_progress.__name__,
                )

                await bot.send(event, msg)
            elif command == "-ping":
                self.Manager.refresh_consumers_ping()

                await bot.send(event, "已刷新服务器状态喵~")
            elif command == "-slt":
                self.Manager.select_all_consumers()

                await bot.send(event, "SDWebUI，全部，启动！")
            elif "-slt " in command:
                user_name = command.replace("-slt ", "").strip()
                user_name = self.Manager.select_consumers(user_name)

                await bot.send(event, f"{user_name} 前进四！")

        @self.cmd_sddraw.handle()
        async def _sddraw(bot: Bot, event: Event):
            images = None

            if hasattr(Message_Processer.protocol(event), "get_img_reply"):
                images = await Message_Processer.protocol(event).get_img_reply(
                    bot, event
                )

            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace("#sddraw", ""),
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group,
            )

            if not images:
                self.Manager.push_task(
                    WebUI_API.txt2img,
                    bot,
                    event,
                    Message_Processer.protocol(event).send_img,
                    params,
                )

                await bot.send(event, "压入一段咒语喵 (●'◡'●)")

            else:
                self.Manager.push_task(
                    WebUI_API.img2img,
                    bot,
                    event,
                    Message_Processer.protocol(event).send_img,
                    params,
                    images,
                )

                await bot.send(event, "压入一张图咒喵 (●'◡'●)")

        @self.cmd_sdextra.handle()
        async def _sdextra(bot: Bot, event: Event):
            images = None

            if hasattr(Message_Processer.protocol(event), "get_img_reply"):
                images = await Message_Processer.protocol(event).get_img_reply(
                    bot, event
                )

            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace("#sdextra", ""),
                ParameterOperation.extra_matcher.patterns_dict,
                ParameterOperation.extra_matcher.base_params,
                [],
                ParameterOperation.extra_matcher.float_group,
                ParameterOperation.extra_matcher.bool_group,
                [],
            )

            if not images:
                await bot.send(event, "没有图片喵，虚空生图不是这样起咒的喵~")

            else:
                self.Manager.push_task(
                    WebUI_API.extra_batch_image,
                    bot,
                    event,
                    Message_Processer.protocol(event).send_img,
                    params,
                    images,
                )

                await bot.send(event, "压入一张图咒，正在EXTRA喵 (●'ω'●)")

        @self.cmd_sdinf.handle()
        async def _sdinf(bot: Bot, event: Event):
            command = event.get_plaintext().replace("#sdinf", "").strip()

            images = None

            if hasattr(Message_Processer.protocol(event), "get_img_reply"):
                images = await Message_Processer.protocol(event).get_img_reply(
                    bot, event
                )

            if not images:
                await bot.send(event, "没有图片喵，对着虚空导不出来喵~")

            else:
                pnginfo = self.Manager.push_task_toone(
                    [{"function": WebUI_API.png_info, "args": (images,)}]
                )[WebUI_API.png_info.__name__]

                if not pnginfo:
                    await bot.send(event, "没有元数据喵，可能需要进一步求导喵！")
                else:
                    await bot.send(event, pnginfo)

                if "-tagger" in command:
                    await bot.send(event, "正在对图片求导喵 (●'ω'●)")

                    params: dict = ParameterOperation.magic_trans_to_params(
                        command,
                        ParameterOperation.tagger_matcher.patterns_dict,
                        ParameterOperation.tagger_matcher.base_params,
                        [],
                        ParameterOperation.tagger_matcher.float_group,
                        [],
                        [],
                    )

                    self.Manager.push_task(
                        WebUI_API.tagger_image,
                        bot,
                        event,
                        Message_Processer.protocol(event).send_str,
                        params,
                        images,
                    )

        @self.cmd_sdtxt.handle()
        async def _sdtxt(bot: Bot, event: Event):
            params: dict = ParameterOperation.magic_trans_to_params(
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

            def get_std_lst(target_func):
                return list(
                    set(
                        [
                            item
                            for server in self.Manager.push_task_toall(
                                [{"function": target_func, "args": None}]
                            )[0]
                            for item in server[target_func.__name__]
                        ]
                    )
                )

            std_samplers = get_std_lst(WebUI_API.get_or_match_sampler)
            std_vae = get_std_lst(WebUI_API.get_or_match_vae)
            std_models = get_std_lst(WebUI_API.get_or_match_model)

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sampler_name",
                std_list=std_samplers,
                is_overridesettings=False,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="hr_upscaler",
                std_list=[hires_upscaler for hires_upscaler in WebUI_API.HiResUpscaler],
                is_overridesettings=False,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_vae",
                std_list=std_vae,
                is_overridesettings=True,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_model_checkpoint",
                std_list=std_models,
                is_overridesettings=True,
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_txt2img.json"
            )

            if event.get_plaintext().replace("#sdtxt", "").strip():
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params, "文生图参数已更新喵（￣︶￣）↗", " -> "
                    ),
                )

            else:
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params_final, "现在的文生图参数喵(^_-)db(-_^)"
                    ),
                )

        @self.cmd_sdimg.handle()
        async def _sdimg(bot: Bot, event: Event):
            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace("#sdimg", ""),
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

            def get_std_lst(target_func):
                return list(
                    set(
                        [
                            item
                            for server in self.Manager.push_task_toall(
                                [{"function": target_func, "args": None}]
                            )[0]
                            for item in server[target_func.__name__]
                        ]
                    )
                )

            std_samplers = get_std_lst(WebUI_API.get_or_match_sampler)
            std_vae = get_std_lst(WebUI_API.get_or_match_vae)
            std_models = get_std_lst(WebUI_API.get_or_match_model)

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sampler_name",
                std_list=std_samplers,
                is_overridesettings=False,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="hr_upscaler",
                std_list=[hires_upscaler for hires_upscaler in WebUI_API.HiResUpscaler],
                is_overridesettings=False,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_vae",
                std_list=std_vae,
                is_overridesettings=True,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_model_checkpoint",
                std_list=std_models,
                is_overridesettings=True,
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_img2img.json"
            )

            if event.get_plaintext().replace("#sdimg", "").strip():
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params, "图生图参数已更新喵（￣︶￣）↗", " -> "
                    ),
                )

            else:
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params_final, "现在的图生图参数喵(^_-)db(-_^)"
                    ),
                )

        @self.cmd_sdext.handle()
        async def _sdext(bot: Bot, event: Event):
            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace("#sdext", ""),
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

            def get_std_lst(target_func):
                return list(
                    set(
                        [
                            item
                            for server in self.Manager.push_task_toall(
                                [{"function": target_func, "args": None}]
                            )[0]
                            for item in server[target_func.__name__]
                        ]
                    )
                )

            std_extraupscaler = get_std_lst(WebUI_API.get_or_match_extra_upscaler)

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="upscaler_1",
                std_list=std_extraupscaler,
                is_overridesettings=False,
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="upscaler_2",
                std_list=std_extraupscaler,
                is_overridesettings=False,
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_extra.json"
            )

            if event.get_plaintext().replace("#sdext", "").strip():
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params, "图片放大参数已更新喵（￣︶￣）↗", " -> "
                    ),
                )

            else:
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params_final, "现在的图片放大参数喵(^_-)db(-_^)"
                    ),
                )

        @self.cmd_sdtagger.handle()
        async def _sdtagger(bot: Bot, event: Event):
            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace("#sdtagger", "").strip(),
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

            def get_std_lst(target_func):
                return list(
                    set(
                        [
                            item
                            for server in self.Manager.push_task_toall(
                                [{"function": target_func, "args": None}]
                            )[0]
                            for item in server[target_func.__name__]
                        ]
                    )
                )

            std_models = get_std_lst(WebUI_API.tagger_get_models)

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="model",
                std_list=std_models,
                is_overridesettings=False,
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, "param_tagger.json"
            )

            if event.get_plaintext().replace("#sdtagger", "").strip():
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params, "tagger插件参数已更新喵（￣︶￣）↗", " -> "
                    ),
                )

            else:
                await bot.send(
                    event,
                    UniversalMessageBuilder.key_value_show(
                        params_final, "现在的tagger插件参数喵(^_-)db(-_^)"
                    ),
                )

        @self.cmd_sdlst.handle()
        async def _sdlst(bot: Bot, event: Event):
            command = event.get_plaintext().replace("#sdlst", "").strip()

            def get_std_lst(target_func):
                return list(
                    set(
                        [
                            item
                            for server in self.Manager.push_task_toall(
                                [{"function": target_func, "args": None}]
                            )[0]
                            for item in server[target_func.__name__]
                        ]
                    )
                )

            if command == "model":
                models, _ = self.Manager.push_task_toall(
                    [{"function": WebUI_API.get_or_match_model, "args": None}]
                )

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show_withserver(
                        models,
                        [WebUI_API.get_or_match_model.__name__],
                        "当前可用模型喵 (✿◠‿◠)",
                    ),
                )

            elif command == "sampler":
                hires_upscalers = get_std_lst(WebUI_API.get_or_match_sampler)

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show(
                        hires_upscalers, "当前可用采样方法喵 (✿◠‿◠)"
                    ),
                )

            elif command == "hires":
                hires_upscalers = get_std_lst(WebUI_API.get_or_match_hires_upscaler)

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show(
                        hires_upscalers, "当前可用高清修复方法喵 (✿◠‿◠)"
                    ),
                )

            elif command == "extra":
                extra_upscalers = get_std_lst(WebUI_API.get_or_match_extra_upscaler)

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show(
                        extra_upscalers, "当前可用放大方法喵 (✿◠‿◠)"
                    ),
                )

            elif command == "vae":
                vaes, _ = self.Manager.push_task_toall(
                    [{"function": WebUI_API.get_or_match_vae, "args": None}]
                )

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show_withserver(
                        vaes,
                        [WebUI_API.get_or_match_vae.__name__],
                        "当前可用VAE喵 (✿◠‿◠)",
                    ),
                )

            elif command == "lora":
                loras, _ = self.Manager.push_task_toall(
                    [{"function": WebUI_API.get_or_match_loras, "args": None}]
                )

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show_withserver(
                        loras,
                        [WebUI_API.get_or_match_loras.__name__],
                        "当前可用LoRa喵 (✿◠‿◠)",
                    ),
                )

            elif command == "embed":
                embeddings, _ = self.Manager.push_task_toall(
                    [{"function": WebUI_API.get_or_match_embeddings, "args": None}]
                )

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show_withserver(
                        embeddings,
                        [WebUI_API.get_or_match_embeddings.__name__],
                        "当前可用Embeddings喵 (✿◠‿◠)",
                    ),
                )

            elif command == "tagger":
                models, _ = self.Manager.push_task_toall(
                    [{"function": WebUI_API.tagger_get_models, "args": None}]
                )

                await bot.send(
                    event,
                    UniversalMessageBuilder.value_show_withserver(
                        models,
                        [WebUI_API.tagger_get_models.__name__],
                        "当前可用tagger插件反推模型喵 (✿◠‿◠)",
                    ),
                )

        @self.cmd_sdskip.handle()
        async def _sdskip(bot: Bot, event: Event):
            if "-all" in event.get_plaintext().replace("#sdskip", "").strip():
                self.Manager.task_queue_clear()
                self.Manager.push_task_toall(
                    [{"function": WebUI_API.skip, "args": None}]
                )
                await bot.send(event, "已清除所有任务喵~")
            else:
                self.Manager.push_task_toslt(
                    [{"function": WebUI_API.skip, "args": None}]
                )
                await bot.send(event, "已弹出选中服务器的一个任务喵~")

        @self.cmd_sdfrev.handle()
        async def _sdfrev(bot: Bot, event: Event):
            if "-all" in event.get_plaintext().replace("#sdfrev", "").strip():
                self.Manager.push_task_toall(
                    [{"function": WebUI_API.reload_checkpoints, "args": None}]
                )
                await bot.send(event, "已全部重载模型释放喵~")
            else:
                self.Manager.push_task_toslt(
                    [{"function": WebUI_API.reload_checkpoints, "args": None}]
                )
                await bot.send(event, "已对选中服务器重载模型释放喵~")
