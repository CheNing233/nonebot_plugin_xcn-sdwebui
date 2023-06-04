import asyncio

from typing import Type

from nonebot.adapters import Bot, Event, Message, MessageSegment

from nonebot.rule import to_me
from nonebot.permission import SUPERUSER

from nonebot.params import CommandArg

from nonebot.log import logger
from nonebot.exception import MatcherException

from nonebot.matcher import Matcher

from ..utils.img import PILImageOperation
from ..utils.cqcode import CQCodeProcess

from ..webui.webui_api import WebUI_API


class Default_Protocol:

    @staticmethod
    async def send_str(bot: Bot, event: Event, *args):
        for string in args:
            if isinstance(string, str):
                await bot.send(event, string)

    @staticmethod
    async def send_img(bot: Bot, event: Event, *args):
        
        ...
        