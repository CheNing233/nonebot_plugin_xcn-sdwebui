from nonebot import on_regex

from nonebot.adapters import Bot, Event, Message
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


class Protocol_Router:

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

    def __init__(self, manager: WebUI_Manager) -> None:

        self.Manager = manager

        self.cmd_sd = on_regex(
            pattern=r'(#sd)\b',
            priority=5,
            block=True
        )

        self.cmd_sddraw = on_regex(
            pattern=r'(#sddraw)\b',
            priority=5,
            block=True
        )

        self.cmd_sdtxt = on_regex(
            pattern=r'(#sdtxt)\b',
            priority=5,
            block=True
        )

        self.cmd_sdimg = on_regex(
            pattern=r'(#sdimg)\b',
            priority=5,
            block=True
        )

        @self.cmd_sd.handle()
        async def _sd(
            bot: Bot,
            event: Event
        ):
            gpu: list[tuple] = self.Manager.push_task_toall(
                WebUI_API.get_vram, ())
            progress: list[tuple] = self.Manager.push_task_toall(
                WebUI_API.get_progress, ())

            msg = UniversalMessageBuilder.server_info(
                self.Manager.get_queue_len(), gpu, progress
            )

            await Protocol_Router.protocol(event).send_str(bot, event, msg)

        @self.cmd_sddraw.handle()
        async def _sddraw(
            bot: Bot,
            event: Event
        ):

            images = None

            if hasattr(Protocol_Router.protocol(event), 'get_reply_imgs'):
                images = await Protocol_Router.protocol(event).\
                    _utils_get_reply_imgs(bot, event)

            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace('#sddraw', ''),
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group
            )

            if not images:

                self.Manager.push_task(
                    WebUI_API.txt2img,
                    bot, event,
                    Protocol_Router.protocol(event).send_img,
                    params
                )

                await Protocol_Router.protocol(event).send_str(bot, event, "压入一段咒语喵 (●'◡'●)")

            else:

                self.Manager.push_task(
                    WebUI_API.img2img,
                    bot, event,
                    Protocol_Router.protocol(event).send_img,
                    params, images
                )

                await Protocol_Router.protocol(event).send_str(bot, event, "压入一张图咒喵 (●'◡'●)")

        @self.cmd_sdtxt.handle()
        async def _sdtxt(
            bot: Bot,
            event: Event
        ):

            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace('#sdtxt', ''),
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group
            )

            """
            修正str类型参数
            """

            std_samplers = list(set([
                sampler for sampler_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_sampler
                )
                for sampler in sampler_list
            ]))

            std_vae = list(set([
                vae for vae_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_vae
                )
                for vae in vae_list
            ]))

            std_models = list(set([
                model for models_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_model
                )
                for model in models_list
            ]))

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sampler_name",
                std_list=std_samplers,
                is_overridesettings=False
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="hr_upscaler",
                std_list=[
                    hires_upscaler for hires_upscaler in WebUI_API.HiResUpscaler
                ],
                is_overridesettings=False
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_vae",
                std_list=std_vae,
                is_overridesettings=True
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_model_checkpoint",
                std_list=std_models,
                is_overridesettings=True
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, 'param_txt2img.json')

            if event.get_plaintext().replace('#sdtxt', '').strip():

                await bot.send(
                    event, UniversalMessageBuilder.params_show(
                        params, '文生图参数已更新喵（￣︶￣）↗', ' -> ')
                )

            else:

                await bot.send(
                    event, UniversalMessageBuilder.params_show(
                        params_final, '现在的文生图参数喵(^_-)db(-_^)')
                )

        @self.cmd_sdimg.handle()
        async def _sdimg(
            bot: Bot,
            event: Event
        ):

            params: dict = ParameterOperation.magic_trans_to_params(
                event.get_plaintext().replace('#sdimg', ''),
                ParameterOperation.txtimg_matcher.patterns_dict,
                ParameterOperation.txtimg_matcher.base_params,
                ParameterOperation.txtimg_matcher.int_group,
                ParameterOperation.txtimg_matcher.float_group,
                ParameterOperation.txtimg_matcher.bool_group,
                ParameterOperation.txtimg_matcher.override_settings_group
            )

            """
            修正str类型参数
            """

            std_samplers = list(set([
                sampler for sampler_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_sampler
                )
                for sampler in sampler_list
            ]))

            std_vae = list(set([
                vae for vae_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_vae
                )
                for vae in vae_list
            ]))

            std_models = list(set([
                model for models_list in
                self.Manager.push_task_toall(
                    WebUI_API.get_or_match_model
                )
                for model in models_list
            ]))

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sampler_name",
                std_list=std_samplers,
                is_overridesettings=False
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="hr_upscaler",
                std_list=[
                    hires_upscaler for hires_upscaler in WebUI_API.HiResUpscaler
                ],
                is_overridesettings=False
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_vae",
                std_list=std_vae,
                is_overridesettings=True
            )

            params = ParameterOperation.fix_string_params(
                user_params=params,
                target_key="sd_model_checkpoint",
                std_list=std_models,
                is_overridesettings=True
            )

            params_final: dict = ParameterOperation.params_to_file(
                params, 'param_img2img.json')

            if event.get_plaintext().replace('#sdimg', '').strip():

                await bot.send(
                    event, UniversalMessageBuilder.params_show(
                        params, '图生图参数已更新喵（￣︶￣）↗', ' -> ')
                )

            else:

                await bot.send(
                    event, UniversalMessageBuilder.params_show(
                        params_final, '现在的图生图参数喵(^_-)db(-_^)')
                )
