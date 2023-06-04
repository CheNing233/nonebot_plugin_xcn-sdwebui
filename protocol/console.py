from typing import Type

from nonebot.adapters.console import Bot, Event, Message

from nonebot.rule import to_me
from nonebot.permission import SUPERUSER

from nonebot.params import CommandArg

from nonebot.log import logger
from nonebot.exception import MatcherException

from nonebot.matcher import Matcher

from ..utils.param import ParameterOperation
from ..utils.msg import UniversalMessageBuilder

from ..webui.webui_api import WebUI_API

from .default import Default_Protocol


class Console_Protocol(Default_Protocol):

    @staticmethod
    async def send_img(bot: Bot, event: Event, *args):
        res: WebUI_API.WebUIApiResult = args[0]
        await bot.send(event, "画好喵 ( •̀ ω •́ )y")
        await bot.send(event, str(res.images))
