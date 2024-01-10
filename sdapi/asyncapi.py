import json
import re
import requests
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum

from nonebot.log import logger

from .param import ParameterOperation
from ..utils.text import TextOptimization
from ..utils.transfers import StdTransfer


class SDWebUI_API:
    class ExtraUpscaler(str, Enum):
        none = "None"
        Lanczos = "Lanczos"
        Nearest = "Nearest"
        LDSR = "LDSR"
        BSRGAN = "BSRGAN"
        ESRGAN_4x = "ESRGAN_4x"
        R_ESRGAN_General_4xV3 = "R-ESRGAN General 4xV3"
        ScuNET_GAN = "ScuNET GAN"
        ScuNET_PSNR = "ScuNET PSNR"
        SwinIR_4x = "SwinIR 4x"

    class HiResUpscaler(str, Enum):
        none = "None"
        Latent = "Latent"
        LatentAntialiased = "Latent (antialiased)"
        LatentBicubic = "Latent (bicubic)"
        LatentBicubicAntialiased = "Latent (bicubic antialiased)"
        LatentNearest = "Latent (nearist)"
        LatentNearestExact = "Latent (nearist-exact)"
        Lanczos = "Lanczos"
        Nearest = "Nearest"
        ESRGAN_4x = "ESRGAN_4x"
        LDSR = "LDSR"
        ScuNET_GAN = "ScuNET GAN"
        ScuNET_PSNR = "ScuNET PSNR"
        SwinIR_4x = "SwinIR 4x"

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def _utils_req(
        host: str,
        port: int,
        api: str,
        json: dict,
        use_get: bool = False,
        use_https: bool = False,
        use_WebUIApiResult: bool = False,
        timeout: int = None,
        allow_null_response: bool = False,
    ) -> dict | str:
        if not use_https:
            url = f"http://{host}:{port}{api}"
        else:
            url = f"https://{host}:{port}{api}"

        async with aiohttp.ClientSession() as session:
            if use_get:
                response = await session.get(url=url, json=json, timeout=timeout)
            else:
                response = await session.post(url=url, json=json, timeout=timeout)

            logger.info(f"请求 {url} {response.status}")

            if response.status != 200:
                response_text = await response.text()
                raise RuntimeError(f"{response.status}, {response_text}")

            if response.content is None or allow_null_response:
                code = response.status
                response.release()
                return StdTransfer.ApiResult(f"{code} but content is none", f"{url}")

            try:
                response_json = await response.json()
            except:
                response_text = await response.text()
                response.release()
                return response_text

            response.release()

        if not use_WebUIApiResult:
            result = response_json
        else:
            images = []
            if "images" in response_json.keys():
                images = response_json["images"]
            elif "image" in response_json.keys():
                images = response_json["image"]

            info = ""
            if "info" in response_json.keys():
                try:
                    info = json.loads(response_json["info"])
                except:
                    info = response_json["info"]

            elif "html_info" in response_json.keys():
                info = response_json["html_info"]

            elif "caption" in response_json.keys():
                info = response_json["caption"]

            parameters = "No parameters MIAO~"
            if "parameters" in response_json.keys():
                parameters = response_json["parameters"]

            result = StdTransfer.ApiImageResult(images, parameters, info)

        return StdTransfer.ApiResult(result, f"{url}")

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def ping(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/internal/ping", json=None, use_get=True, timeout=1000
        )

        if result.result is not None:
            logger.debug("PING %s:%d %s" % (host, port, "OK"))
            return StdTransfer.ApiResult(True, result.info)
        else:
            logger.debug("PING %s:%d %s" % (host, port, "UNVALIABLE"))
            return StdTransfer.ApiResult(False, result.info)

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_vram(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/memory", {}, True, False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        if "cuda" not in result.result:
            raise RuntimeError("result.result parse fail")

        vram = result.result["cuda"]["system"]

        vram_free = round(vram["free"] / pow(1024, 3), 2)
        vram_used = round(vram["used"] / pow(1024, 3), 2)
        vram_total = round(vram["total"] / pow(1024, 3), 2)
        vram_percent = round((vram["used"] / vram["total"]) * 100, 2)

        return StdTransfer.ApiResult(
            result=(vram_free, vram_used, vram_total, vram_percent), info="ok"
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_progress(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/progress", {}, True, False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=(
                result.result["state"]["job_count"],
                result.result["eta_relative"],
                result.result["progress"] * 100,
                result.result["state"]["sampling_step"],
                result.result["state"]["sampling_steps"],
            ),
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_model(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/refresh-checkpoints",
            json={},
            use_get=False,
            use_https=False,
            allow_null_response=True,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/sd-models",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        models = [model["model_name"] for model in result.result]

        if kwargs.get("name", None):
            user_model = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(models, user_model),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=models,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_vae(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/refresh-vae",
            json={},
            use_get=False,
            use_https=False,
            allow_null_response=True,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/sd-vae",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        vaes = ["None", "Automatic"] + [vae["model_name"] for vae in result.result]

        if kwargs.get("name", None):
            user_vae = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(vaes, user_vae),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=vaes,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_sampler(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/samplers",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        samplers = [sampler["name"] for sampler in result.result]

        if kwargs.get("name", None):
            user_sampler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(samplers, user_sampler),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=samplers,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_hires_upscaler(host, port, **kwargs):
        # hires_upscaler = list(map(lambda x: x.value, SDWebUI_API.HiResUpscaler))
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/latent-upscale-modes",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        hires_upscaler = [item["name"] for item in result.result]

        if kwargs.get("name", None):
            user_hires_upscaler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(
                    hires_upscaler, user_hires_upscaler
                ),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=hires_upscaler,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_extra_upscaler(host, port, **kwargs):
        # extra_upscaler = list(map(lambda x: x.value, SDWebUI_API.ExtraUpscaler))
        add_pth_detailed = kwargs.get("add_pth_detailed", False)

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/upscalers",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        if add_pth_detailed:
            extra_upscaler = [
                item["name"]
                + (
                    " (需下载)"
                    if (item["model_path"] is not None)
                    and (
                        (item["model_path"].startswith("http://"))
                        or (item["model_path"].startswith("https://"))
                    )
                    else " (可用)"
                )
                for item in result.result
            ]
        else:
            extra_upscaler = [item["name"] for item in result.result]

        if kwargs.get("name", None):
            user_extra_upscaler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(
                    extra_upscaler, user_extra_upscaler
                ),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=extra_upscaler,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_loras(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/refresh-loras", {}, allow_null_response=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/loras",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        loras = [lora["name"] for lora in result.result]

        if kwargs.get("name", None):
            user_lora = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(loras, user_lora),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=loras,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_match_embeddings(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/embeddings",
            json={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        embeddings = [embedding for embedding in result.result["loaded"]]

        if kwargs.get("name", None):
            user_embeddings = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(embeddings, user_embeddings),
                info="ok",
            )
        else:
            return StdTransfer.ApiResult(
                result=embeddings,
                info="ok",
            )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def get_or_set_options(host, port, **kwargs):
        user_options: dict = kwargs.get("options", {})

        options = {
            "sd_model_checkpoint": user_options.get("sd_model_checkpoint", ""),
            "sd_vae": user_options.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": user_options.get("CLIP_stop_at_last_layers", 2),
            "eta_noise_seed_delta": user_options.get("eta_noise_seed_delta", 0),
        }

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/options",
            json=user_options,
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        options = {
            "sd_model_checkpoint": result.result.get("sd_model_checkpoint", ""),
            "sd_vae": result.result.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": result.result.get(
                "CLIP_stop_at_last_layers", 2
            ),
            "eta_noise_seed_delta": result.result.get("eta_noise_seed_delta", 0),
        }

        return StdTransfer.ApiResult(
            result=options,
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def txt2img(host, port, **kwargs):
        payload: dict = kwargs.get("params", {})

        # payload = ParameterOperation.txt2img_params_normalization(params)

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/txt2img", payload, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def img2img(host, port, **kwargs):
        params = kwargs.get("params", {})
        # images = kwargs.get("images", None)

        # payload = ParameterOperation.img2img_params_normalization(params, images)

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/img2img", params, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def extra_batch_image(host, port, **kwargs):
        params = kwargs.get("params", {})
        # images = kwargs.get("images", None)

        # payload = ParameterOperation.extra_params_normalization(params, images)

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/extra-batch-images", params, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def skip(host, port, *args):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/skip", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(result=result.result, info="ok")

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def stop(host, port, *args):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/interrupt", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(result=result.result, info="ok")

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def reload_checkpoints(host, port, *args):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/unload-checkpoint", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/reload-checkpoint", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(result=result.result, info="ok")

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def png_info(host, port, **kwargs) -> str:
        payload = {"image": kwargs.get("image", None)}

        if payload["image"] is None:
            raise RuntimeError("No image in png_info")

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/png-info", payload, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result["info"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def tagger_image(host, port, **kwargs):
        params = kwargs.get("params", {})
        images = kwargs.get("image", None)

        payload = ParameterOperation.tagger_params_normalization(params, images)

        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/tagger/v1/interrogate", payload, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        await SDWebUI_API.tagger_unload_models(host, port)

        return StdTransfer.ApiResult(
            result=result.result["caption"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def tagger_get_models(host, port, **kwargs) -> list:
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host,
            port,
            "/tagger/v1/interrogators",
            {},
            use_get=True,
            use_WebUIApiResult=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result["models"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.AsyncExceptionHandler
    async def tagger_unload_models(host, port, **kwargs):
        result: StdTransfer.ApiResult = await SDWebUI_API._utils_req(
            host, port, "/tagger/v1/unload-interrogators", {}, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        count = re.findall(r"\d+", str(result.result.content))

        return StdTransfer.ApiResult(
            result=count,
            info="ok",
        )
