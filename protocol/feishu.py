import requests
import json
from requests_toolbelt import MultipartEncoder

from pydantic import parse_obj_as

from nonebot.adapters.feishu import (
    Bot,
    Event,
    PrivateMessageEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
)

from nonebot.adapters.feishu.adapter import Adapter
from nonebot.adapters.feishu.models import BaseResponse

from nonebot.drivers import Request

from nonebot.log import logger

from ..utils.img import ImageOperation

from .default import Default_Protocol


class Feishu_Utils:
    @staticmethod
    async def upload_image(bot: Bot, img_bytes: str) -> str:
        """
        上传图片 返回一个image_key
        """
        tenant_access_token = await bot.adapter.get_tenant_access_token(bot.bot_config)

        url = bot.adapter.get_api_url(bot.bot_config, "im/v1/images")

        data = {"image_type": "message", "image": img_bytes}
        multi_form = MultipartEncoder(data)

        headers = {
            "Authorization": f"Bearer {tenant_access_token}",
            "Content-Type": multi_form.content_type,
        }

        response = requests.request(
            method="POST",
            url=url,
            headers=headers,
            data=multi_form,
        )

        logger.info(f"请求 {url} {response.status_code}")

        if response.status_code == 200:
            return json.loads(response.content)["data"]["image_key"]
        else:
            return ""

    @staticmethod
    async def download_images(bot: Bot, msg_id: str, img_keys: list[str]) -> list:
        """
        下载图片 返回base64列表
        """
        tenant_access_token = await bot.adapter.get_tenant_access_token(bot.bot_config)

        url = bot.adapter.get_api_url(
            bot.bot_config, f"im/v1/messages/{msg_id}/resources"
        )

        # 获取tenant_access_token, 需要替换为实际的token
        headers = {"Authorization": f"Bearer {tenant_access_token}"}
        params = {"type": "file"}

        session = requests.Session()

        imgs = []
        for img_key in img_keys:
            payload_url = f"{url}/{img_key}"
            response = session.get(payload_url, headers=headers, params=params)

            logger.info(f"请求 {payload_url} {response.status_code}")

            imgs.append(ImageOperation.bytes_to_base64(response.content))

        return imgs

    @staticmethod
    def build_message_segment(content: dict):
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


class Feishu_Protocol(Default_Protocol):
    @staticmethod
    async def msg_image(bot: Bot, event: Event, images: list):
        """
        构造图片 message seg 列表
        """
        images_bytes: list = []

        for image in images:
            images_bytes.append(ImageOperation.base64_to_bytes(image))

        msgseg_images = list()

        for image_bytes in images_bytes:
            msgseg_images.append(
                MessageSegment.image(
                    image_key=await Feishu_Utils.upload_image(bot, image_bytes)
                )
            )

        return msgseg_images

    @staticmethod
    async def get_image_from_reply(bot: Bot, event: Event) -> list:
        """
        获取用户回复的那条消息中的图片 返回b64列表
        """
        if event.event.message.parent_id is None:
            return []

        # 获取原始响应数据
        parent_msg = await bot.get_msg(event.event.message.parent_id)
        response: BaseResponse = parse_obj_as(BaseResponse, parent_msg)

        logger.info(
            "请求 {} code={} msg={}".format(
                bot.adapter.get_api_url(
                    bot.bot_config, f"im/v1/messages/{event.event.message.parent_id}"
                ),
                response.code,
                response.msg,
            )
        )

        if response.msg != "success":
            return []

        # 解析数据
        parent_msg = Feishu_Utils.build_message_segment(
            json.loads(parent_msg["data"]["items"][0]["body"]["content"])
        )

        # 获取 image_key
        image_keys: list = []
        if parent_msg:
            for parent_msg_seg in parent_msg:
                if parent_msg_seg.type == "image":
                    image_keys.append(parent_msg_seg.data["image_key"])

        # 利用 image_key 下载所有图片
        if image_keys:
            return await Feishu_Utils.download_images(
                bot, event.event.message.parent_id, image_keys
            )

        else:
            return []
