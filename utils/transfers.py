from dataclasses import dataclass, field
from typing import Any

from nonebot.log import logger


class StdTransfer:
    @dataclass
    class StdParams:
        command: str = None
        params: dict = field(default_factory=dict)
        code: str = None

    @dataclass
    class ApiImageResult:
        images: list
        parameters: dict
        info: dict

        @property
        def image(self):
            if self.images:
                return self.images[0]
            else:
                return []

    @dataclass
    class ApiResult:
        result: Any
        info: str = None

    @dataclass
    class NodeResult:
        result: Any
        nodeinfo: dict

    @staticmethod
    def StdExceptionHandler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{str(func)} {e}")
                return StdTransfer.ApiResult(None, info=f"{str(func)} {e}")

        return wrapper

    @classmethod
    def AsyncExceptionHandler(cls, func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{str(func)} {e}")
                return StdTransfer.ApiResult(None, info=f"{str(func)} {e}")

        return wrapper

    class StdStopEvent(Exception):
        pass
