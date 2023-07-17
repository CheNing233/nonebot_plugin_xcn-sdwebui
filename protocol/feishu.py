import requests
import json
from requests_toolbelt import MultipartEncoder


from nonebot.adapters.feishu import (
    Bot,
    Event,
    PrivateMessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
)


# from nonebot.adapters.feishu.adapter import Adapter

# from nonebot.rule import to_me
from nonebot import get_driver
from nonebot.permission import SUPERUSER

# from nonebot.params import CommandArg

from nonebot.log import logger

# from nonebot.exception import MatcherException

# from nonebot.matcher import Matcher


from ..utils.img import ImageOperation

from ..webui.webui_api import WebUI_API

from .default import Default_Protocol


class Feishu_Protocol(Default_Protocol):
    app_config = None

    @staticmethod
    def _utils_get_tenant_access_token(app_id, app_secret):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        json_data = {"app_id": app_id, "app_secret": app_secret}

        return json.loads(
            requests.post(
                url=url,
                json=json_data,
            ).content
        )["tenant_access_token"]

    @staticmethod
    def _utils_rebuild_message_segment(content: dict):
        """
        依据消息体重构消息对象
        """
        if "content" in content.keys():
            real_content = content["content"]

            target = ""

            for msg_group in real_content:
                for same_type_msg in msg_group:
                    if same_type_msg["tag"] == "img":
                        target += MessageSegment.image(same_type_msg["image_key"])
                    if same_type_msg["tag"] == "text":
                        target += MessageSegment.text(same_type_msg["text"])

        elif "image_key" in content.keys():
            target = Message(MessageSegment.image(content["image_key"]))

        else:
            target = ""

        return target

    @staticmethod
    def _utils_upload_img(img_bytes: str, tenant_access_token: str):
        """
        上传图片
        """
        url = "https://open.feishu.cn/open-apis/im/v1/images"

        form = {"image_type": "message", "image": img_bytes}
        multi_form = MultipartEncoder(form)

        # 获取tenant_access_token, 需要替换为实际的token
        headers = {"Authorization": "Bearer " + tenant_access_token}
        headers["Content-Type"] = multi_form.content_type

        response = requests.request("POST", url, headers=headers, data=multi_form)

        if response.status_code == 200:
            return json.loads(response.content)["data"]["image_key"]
        else:
            return ""

    @staticmethod
    def _utils_download_img(
        msg_id: str, img_keys: list[str], tenant_access_token: str
    ) -> list:
        """
        下载图片，返回base64列表
        """
        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{msg_id}/resources"

        # 获取tenant_access_token, 需要替换为实际的token
        headers = {"Authorization": "Bearer " + tenant_access_token}
        params = {"type": "file"}

        session = requests.Session()

        imgs = []

        for img_key in img_keys:
            response = session.get(
                url + "/" + str(img_key), headers=headers, params=params
            )
            imgs.append(ImageOperation.bytes_to_base64(response.content))

        return imgs

    @staticmethod
    def _utils_get_reply_message(
        parent_id: str, tenant_access_token: str
    ) -> dict | None:
        """
        获取被回复的消息体
        """
        if not parent_id:
            return None

        url = "https://open.feishu.cn/open-apis/im/v1/messages"

        # 获取tenant_access_token, 需要替换为实际的token
        headers = {"Authorization": "Bearer " + tenant_access_token}

        response = requests.get(url=url + "/" + parent_id, headers=headers)

        try:
            content_body = json.loads(
                response.json()["data"]["items"][0]["body"]["content"]
            )
        except:
            logger.error("获取 Feishu content_body 失败")
            content_body = None

        return content_body

    @staticmethod
    async def get_img_reply(
        bot: Bot, event: Event | PrivateMessageEvent | GroupMessageEvent
    ):
        if Feishu_Protocol.app_config:
            tenant_access_token = Feishu_Protocol._utils_get_tenant_access_token(
                app_id=Feishu_Protocol.app_config[0]["app_id"],
                app_secret=Feishu_Protocol.app_config[0]["app_secret"],
            )

        messages_content = Feishu_Protocol._utils_get_reply_message(
            event.event.message.parent_id, tenant_access_token
        )

        if messages_content:
            msg_id = event.event.message.parent_id
            messages = Feishu_Protocol._utils_rebuild_message_segment(messages_content)
        else:
            msg_id = event.event.message.message_id
            messages = event.get_message()

        img_keys = []

        if messages:
            for msg in messages:
                if msg.type == "image":
                    img_keys.append(msg.data["image_key"])

        if img_keys:
            return Feishu_Protocol._utils_download_img(
                msg_id, img_keys, tenant_access_token
            )

        else:
            return None

    @staticmethod
    async def send_img(
        bot: Bot, event: Event | PrivateMessageEvent | GroupMessageEvent, ret_img
    ):
        imgs_pack: WebUI_API.WebUIApiResult = ret_img

        str_user = "**魔导师**\n%s" % (event.get_user_id())
        str_res = "**导引结果**\n%s" % ("存在" if imgs_pack.images else "炸炉")
        str_magic = "**咒语：**\nemm，没有捏"
        if isinstance(imgs_pack.info, dict):
            if "infotexts" in imgs_pack.info.keys():
                if isinstance(imgs_pack.info["infotexts"], list):
                    str_magic = "**咒语：**\n%s" % (imgs_pack.info["infotexts"][0])

        await bot.send(
            event=event, message=Message("画好了，正在从法阵中提取图片喵 ( •̀ ω •́ )y"), at_sender=True
        )
        await bot.send(
            event,
            Message(
                MessageSegment.interactive(
                    {
                        "config": {"wide_screen_mode": False},
                        "header": {"title": {"tag": "plain_text", "content": "法阵记录"}},
                        "elements": [
                            {
                                "tag": "div",
                                "fields": [
                                    {
                                        "is_short": True,
                                        "text": {"tag": "lark_md", "content": str_user},
                                    },
                                    {
                                        "is_short": True,
                                        "text": {"tag": "lark_md", "content": str_res},
                                    },
                                    {
                                        "is_short": False,
                                        "text": {
                                            "tag": "lark_md",
                                            "content": str_magic,
                                        },
                                    },
                                ],
                            }
                        ],
                    }
                )
            ),
        )

        imgs_bytes_pack: list = []
        for img in imgs_pack.images:
            imgs_bytes_pack.append(ImageOperation.base64_to_bytes(img))

        if Feishu_Protocol.app_config:
            tenant_access_token = Feishu_Protocol._utils_get_tenant_access_token(
                app_id=Feishu_Protocol.app_config[0]["app_id"],
                app_secret=Feishu_Protocol.app_config[0]["app_secret"],
            )

        for imgs_bytes in imgs_bytes_pack:
            await bot.send(
                event,
                Message(
                    MessageSegment.image(
                        image_key=Feishu_Protocol._utils_upload_img(
                            imgs_bytes,
                            tenant_access_token,
                        )
                    )
                ),
            )
