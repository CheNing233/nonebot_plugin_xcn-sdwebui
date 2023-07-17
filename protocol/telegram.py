from typing import Type

from nonebot.adapters.telegram import Bot, Event, Message, MessageSegment
from nonebot.adapters.telegram.message import File

from nonebot.rule import to_me
from nonebot.permission import SUPERUSER

from nonebot.params import CommandArg

from nonebot.log import logger
from nonebot.exception import MatcherException

from nonebot.matcher import Matcher

from ..utils.img import ImageOperation

from ..webui.webui_api import WebUI_API

from .default import Default_Protocol


class Telegram_Protocol(Default_Protocol):

    pass
