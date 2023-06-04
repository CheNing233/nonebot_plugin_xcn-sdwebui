import asyncio


from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment, PrivateMessageEvent, GroupMessageEvent

# from nonebot.rule import to_me
# from nonebot.permission import SUPERUSER

# from nonebot.params import CommandArg

# from nonebot.log import logger
# from nonebot.exception import MatcherException

# from nonebot.matcher import Matcher

from ..utils.img import PILImageOperation
from ..utils.cqcode import CQCodeProcess

from ..webui.webui_api import WebUI_API

from .default import Default_Protocol


class OneBotV11_Protocol(Default_Protocol):

    @ staticmethod
    async def _utils_search_cqcode(
        bot: Bot,
        target_cqcode: str,
        plain_text: str = "",
        message_id: int = None,
        final_cqcode: list = list()
    ):
        """递归搜索指定cqcode+进入回复"""

        # 检测message_id是否存在
        if bool(message_id):
            future_result = await bot.get_msg(message_id=message_id)
            cqcode_all: list = future_result['message']
        else:
            cqcode_all: list = CQCodeProcess.strToCqCodeToDict(plain_text)

        flag_cqcode_reply = None

        # 遍历所有Cqcode
        for cqcode in cqcode_all:

            if cqcode['type'] == target_cqcode:
                final_cqcode.append(cqcode)

            if cqcode['type'] == 'reply':
                flag_cqcode_reply = cqcode

        if bool(flag_cqcode_reply):
            return await OneBotV11_Protocol._utils_search_cqcode(
                bot=bot,
                plain_text=None,
                message_id=int(flag_cqcode_reply['data']['id']),
                final_cqcode=final_cqcode,
                target_cqcode=target_cqcode
            )

        else:

            return final_cqcode

    @ staticmethod
    async def _utils_cqcode_to_pil(cqcode_s: str | dict | list) -> list:
        """cqcode到url导pil图片"""

        import io
        import requests
        from PIL import Image

        imgs = []
        urls = []

        if isinstance(cqcode_s, list):
            for cqcode in cqcode_s:
                urls.append(cqcode['data']['url'])

        elif isinstance(cqcode_s, dict):
            urls.append(cqcode_s['data']['url'])

        elif isinstance(cqcode_s, str):
            cqcodes = CQCodeProcess.strToCqCodeToDict(str(cqcode_s))
            for cqcode in cqcodes:
                urls.append(cqcode['data']['url'])

        for url in urls:

            try:
                res = requests.get(url=url)
            except:
                res = None

            if res and res.status_code == 200:
                imgs.append(Image.open(io.BytesIO(res.content)))

        return imgs

    @ staticmethod
    async def _utils_get_reply_imgs(bot: Bot, event: Event | GroupMessageEvent | PrivateMessageEvent, *args):

        cqcode_img = await OneBotV11_Protocol._utils_search_cqcode(
            bot=bot,
            plain_text=str(event.original_message),
            final_cqcode=[],
            target_cqcode='image'
        )

        if cqcode_img:
            return await OneBotV11_Protocol._utils_cqcode_to_pil(cqcode_img)
        else:
            return None

    @ staticmethod
    async def send_str(bot: Bot, event: Event | GroupMessageEvent | PrivateMessageEvent, *args):
        for string in args:
            if isinstance(string, str):
                await bot.send(event, string)

    @ staticmethod
    async def send_img(bot: Bot, event: Event | GroupMessageEvent | PrivateMessageEvent, *args):

        imgs_pack: WebUI_API.WebUIApiResult = args[0]

        asyncio.create_task(
            bot.send(event, Message("画好了，正在从法阵中提取图片喵 ( •̀ ω •́ )y")))

        imgs_path = PILImageOperation.save_imgs(
            imgs_pack.images, imgs_pack.info)

        for img_path in imgs_path:
            asyncio.create_task(
                bot.send(
                    event,
                    Message(
                        MessageSegment.reply(event.message_id) +
                        MessageSegment.image(file='file:///' + img_path)
                    ))
            )
