import asyncio


from .asyncapi import SDWebUI_API

from ..utils.text import TextOptimization
from ..utils.transfers import StdTransfer
from ..utils.config import ConfigLoader


class SDWebUI_Node:
    def __init__(self, nodeConfig: dict, logger) -> None:
        self.logger = logger

        self._config = nodeConfig

        self.name = nodeConfig["name"]
        self.host = nodeConfig["host"]
        self.port = nodeConfig["port"]
        self.priority = nodeConfig["priority"]
        self.is_available = False
        self.is_ban = False
        self.sem_working = asyncio.Event()

        self.api_mapping = {
            "get_vram": SDWebUI_API.get_vram,
            "get_progress": SDWebUI_API.get_progress,
            "txt2img": SDWebUI_API.txt2img,
            "img2img": SDWebUI_API.img2img,
            "extra": SDWebUI_API.extra_batch_image,
            "get_or_match_sampler": SDWebUI_API.get_or_match_sampler,
            "get_or_match_hires_upscaler": SDWebUI_API.get_or_match_hires_upscaler,
            "get_or_match_extra_upscaler": SDWebUI_API.get_or_match_extra_upscaler,
            "get_or_match_vae": SDWebUI_API.get_or_match_vae,
            "get_or_match_model": SDWebUI_API.get_or_match_model,
            "get_or_match_loras": SDWebUI_API.get_or_match_loras,
            "get_or_match_embeddings": SDWebUI_API.get_or_match_embeddings,
            "tagger_get_models": SDWebUI_API.tagger_get_models,
            "skip": SDWebUI_API.skip,
            "stop": SDWebUI_API.stop,
            "png_info": SDWebUI_API.png_info,
            "tagger_image": SDWebUI_API.tagger_image,
        }

    def get_config(self):
        """
        返回本节点配置
        """
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "priority": self.priority,
            "is_available": self.is_available,
            "is_ban": self.is_ban,
            "sem_working": self.sem_working,
        }

    async def get_status(
        self, api_result: StdTransfer.ApiResult = None
    ) -> StdTransfer.NodeResult:
        if api_result is None:
            api_result: StdTransfer.ApiResult = await SDWebUI_API.get_progress(
                self.host, self.port, **{}
            )

        if api_result.result is None:
            self.is_available = False
            self.sem_working.clear()

            self.logger.info(f"节点自检 {self.host}:{self.port} {self.is_available}")

            return StdTransfer.NodeResult(
                result=self.is_available,
                nodeinfo=self.get_config(),
            )
        else:
            self.is_available = True
            self.logger.info(f"节点自检 {self.host}:{self.port} {self.is_available}")

        (
            job_count,
            eta_relative,
            progress,
            sampling_step,
            sampling_steps,
        ) = api_result.result

        if job_count > 0:
            self.sem_working.clear()
        else:
            self.sem_working.set()

        return StdTransfer.NodeResult(
            result=self.is_available,
            nodeinfo=self.get_config(),
        )

    async def call_api(self, params: StdTransfer.StdParams) -> StdTransfer.NodeResult:
        api_result = None

        self.logger.info(f"{self.host}:{self.port} 接取 {params.command}")

        if params.command in self.api_mapping:
            api_result = await self.api_mapping[params.command](
                self.host, self.port, **(params.params)
            )

            if params.command == "get_progress":
                await self.get_status(api_result)
        else:
            self.logger.error("No matching function")

        return StdTransfer.NodeResult(result=api_result, nodeinfo=self.get_config())
