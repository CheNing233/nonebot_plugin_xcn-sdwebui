import asyncio
import requests
import json

from requests_toolbelt import MultipartEncoder

from typing import Type

from nonebot.adapters.feishu import Bot, Event, Message, MessageSegment
# from nonebot.adapters.feishu.adapter import Adapter

# from nonebot.rule import to_me
from nonebot.permission import SUPERUSER

# from nonebot.params import CommandArg

from nonebot.log import logger
# from nonebot.exception import MatcherException

# from nonebot.matcher import Matcher

from ..utils.img import PILImageOperation

from ..webui.webui_api import WebUI_API

from .default import Default_Protocol


class Feishu_Protocol(Default_Protocol):

    @staticmethod
    def _utils_get_tenant_access_token(app_id, app_secret):

        return json.loads(
            requests.post(
                url='https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
                json={
                    "app_id": app_id,
                    "app_secret": app_secret
                }
            ).content
        )['tenant_access_token']

    @staticmethod
    def _utils_upload_img(img_path: str, tenant_access_token: str):
        url = "https://open.feishu.cn/open-apis/im/v1/images"
        with open(img_path, 'rb') as f:
            form = {'image_type': 'message', 'image': f}
            multi_form = MultipartEncoder(form)
            headers = {
                # 获取tenant_access_token, 需要替换为实际的token
                'Authorization': 'Bearer ' + tenant_access_token,
            }
            headers['Content-Type'] = multi_form.content_type
            response = requests.request(
                "POST", url, headers=headers, data=multi_form)

        if response.status_code == 200:
            return json.loads(response.content)['data']['image_key']
        else:
            return ''

    @staticmethod
    async def send_str(bot: Bot, event: Event, *args):

        for string in args:
            if isinstance(string, str):
                await bot.send(event, string)

    @ staticmethod
    async def send_img(bot: Bot, event: Event, *args):

        imgs_pack: WebUI_API.WebUIApiResult = args[0]

        str_user = "**魔导师**\n%s" % (event.get_user_id())
        str_res = "**导引结果**\n%s" % ('存在' if imgs_pack.images else '炸炉')
        str_magic = "**咒语：**\n%s" % (imgs_pack.info['infotexts'][0])

        await bot.send(event=event, message=Message("画好了，正在从法阵中提取图片喵 ( •̀ ω •́ )y"), at_sender=True)
        await bot.send(event, Message(MessageSegment.interactive(
            {
                "config": {
                    "wide_screen_mode": False
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "法阵记录"
                    }
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": str_user
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "tag": "lark_md",
                                    "content": str_res
                                }
                            },
                            {
                                "is_short": False,
                                "text": {
                                    "tag": "lark_md",
                                    "content": str_magic
                                }
                            }
                        ]
                    }
                ]
            }
        )))

        imgs_path = PILImageOperation.save_imgs(
            imgs_pack.images, imgs_pack.info)

        for img_path in imgs_path:

            await bot.send(
                event,
                Message(
                    MessageSegment.image(
                        image_key=Feishu_Protocol._utils_upload_img(
                            img_path,
                            Feishu_Protocol._utils_get_tenant_access_token(
                                app_id='cli_a4fcd7c6cef8900b',
                                app_secret='bv0Qa11u0JUYq24DnImp0bH8krSXvBnb'
                            )))
                ))
