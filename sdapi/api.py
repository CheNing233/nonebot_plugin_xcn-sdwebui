import json
import re
import requests
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
    @StdTransfer.StdExceptionHandler
    def _utils_req(
        host: str,
        port: int,
        api: str,
        json: dict,
        use_get: bool = False,
        use_https: bool = False,
        use_WebUIApiResult: bool = False,
        timeout: int = None,
    ) -> dict:
        if not hasattr(SDWebUI_API._utils_req, "session"):
            SDWebUI_API._utils_req.session = requests.Session()

        if not use_https:
            url = f"http://{host}:{port}{api}"
        else:
            url = f"https://{host}:{port}{api}"

        logger.info(f"拉起请求: {url}")

        if use_get:
            response = SDWebUI_API._utils_req.session.get(
                url=url, json=json, timeout=timeout
            )
        else:
            response = SDWebUI_API._utils_req.session.post(
                url=url, json=json, timeout=timeout
            )

        if response.status_code != 200:
            raise RuntimeError(f"{response.status_code}, {response.text}")

        if not use_WebUIApiResult:
            result = response
        else:
            response_json = response.json()

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

            result = SDWebUI_API.ImageResult(images, parameters, info)

        return StdTransfer.ApiResult(result, response.text)

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def ping(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/internal/ping", json=None, use_get=True, timeout=1000
        )

        if result.result is not None:
            logger.debug("PING %s:%d %s" % (host, port, "OK"))
            return StdTransfer.ApiResult(True, result.info)
        else:
            logger.debug("PING %s:%d %s" % (host, port, "UNVALIABLE"))
            return StdTransfer.ApiResult(False, result.info)

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_vram(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/memory", {}, True, False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        if "cuda" not in result_json:
            raise RuntimeError("result_json parse fail")

        vram = result["cuda"]["system"]

        vram_free = round(vram["free"] / pow(1024, 3), 2)
        vram_used = round(vram["used"] / pow(1024, 3), 2)
        vram_total = round(vram["total"] / pow(1024, 3), 2)
        vram_percent = round((vram["used"] / vram["total"]) * 100, 2)

        return StdTransfer.ApiResult(
            result=(vram_free, vram_used, vram_total, vram_percent), info="ok"
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_progress(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/progress", {}, True, False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        return StdTransfer.ApiResult(
            result=(
                result_json["state"]["job_count"],
                result_json["eta_relative"],
                result_json["progress"] * 100,
                result_json["state"]["sampling_step"],
                result_json["state"]["sampling_steps"],
            ),
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_model(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/refresh-checkpoints",
            js={},
            use_get=False,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/sd-models",
            js={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        models = [model["model_name"] for model in result_json]

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=models,
                info="ok",
            )
        else:
            user_model = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(models, user_model),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_vae(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/sd-vae",
            js={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        vaes = ["None", "Automatic"] + [vae["model_name"] for vae in result_json]

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=vaes,
                info="ok",
            )
        else:
            user_vae = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(vaes, user_vae),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_sampler(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/samplers",
            js={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        samplers = [sampler["name"] for sampler in result_json]

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=samplers,
                info="ok",
            )
        else:
            user_sampler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(samplers, user_sampler),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_hires_upscaler(host, port, **kwargs):
        hires_upscaler = list(map(lambda x: x.value, SDWebUI_API.HiResUpscaler))

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=hires_upscaler,
                info="ok",
            )
        else:
            user_hires_upscaler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(
                    hires_upscaler, user_hires_upscaler
                ),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_extra_upscaler(host, port, **kwargs):
        extra_upscaler = list(map(lambda x: x.value, SDWebUI_API.ExtraUpscaler))

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=extra_upscaler,
                info="ok",
            )
        else:
            user_extra_upscaler = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(
                    extra_upscaler, user_extra_upscaler
                ),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_loras(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/refresh-loras", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/loras",
            js={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        loras = [lora["name"] for lora in result_json]

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=loras,
                info="ok",
            )
        else:
            user_lora = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(loras, user_lora),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_match_embeddings(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/embeddings",
            js={},
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        embeddings = [embedding for embedding in result_json["loaded"]]

        if kwargs.get("name", None):
            return StdTransfer.ApiResult(
                result=embeddings,
                info="ok",
            )
        else:
            user_embeddings = kwargs.get("name", None)
            return StdTransfer.ApiResult(
                result=TextOptimization.find_similar_str(embeddings, user_embeddings),
                info="ok",
            )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def get_or_set_options(host, port, **kwargs):
        user_options: dict = kwargs.get("options", {})

        options = {
            "sd_model_checkpoint": user_options.get("sd_model_checkpoint", ""),
            "sd_vae": user_options.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": user_options.get("CLIP_stop_at_last_layers", 2),
            "eta_noise_seed_delta": user_options.get("eta_noise_seed_delta", 0),
        }

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/sdapi/v1/options",
            js=user_options,
            use_get=True,
            use_https=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        options = {
            "sd_model_checkpoint": result_json.get("sd_model_checkpoint", ""),
            "sd_vae": result_json.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": result_json.get("CLIP_stop_at_last_layers", 2),
            "eta_noise_seed_delta": result_json.get("eta_noise_seed_delta", 0),
        }

        return StdTransfer.ApiResult(
            result=options,
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def txt2img(host, port, **kwargs):
        params: dict = kwargs.get("params", {})

        payload = ParameterOperation.txt2img_params_normalization(params)

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/txt2img", payload, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def img2img(host, port, **kwargs):
        params = kwargs.get("params", {})
        images = kwargs.get("images", None)

        payload = ParameterOperation.img2img_params_normalization(params, images)

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/img2img", payload, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def extra_batch_image(host, port, **kwargs):
        params = kwargs.get("params", {})
        images = kwargs.get("images", None)

        payload = ParameterOperation.extra_params_normalization(params, images)

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/extra-batch-images", payload, use_WebUIApiResult=True
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(
            result=result.result,
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def skip(host, port, *args):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/skip", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(result=result.code, info=result.info)

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def reload_checkpoints(host, port, *args):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/unload-checkpoint", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/reload-checkpoint", {}
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        return StdTransfer.ApiResult(result=result.code, info=result.info)

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def png_info(host, port, **kwargs) -> str:
        payload = {"image": kwargs.get("image", None)}

        if payload["image"] is None:
            raise RuntimeError("No image in png_info")

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/sdapi/v1/png-info", payload, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        return StdTransfer.ApiResult(
            result=result_json["info"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def tagger_image(host, port, **kwargs):
        params = kwargs.get("params", {})
        images = kwargs.get("images", None)

        payload = ParameterOperation.tagger_params_normalization(params, images)

        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/tagger/v1/interrogate", payload, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        SDWebUI_API.tagger_unload_models(host, port)

        return StdTransfer.ApiResult(
            result=result_json["caption"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def tagger_get_models(host, port, **kwargs) -> list:
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host,
            port,
            "/tagger/v1/interrogators",
            {},
            use_get=True,
            use_WebUIApiResult=False,
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        result_json = result.result.json()

        return StdTransfer.ApiResult(
            result=result_json["models"],
            info="ok",
        )

    @staticmethod
    @StdTransfer.StdExceptionHandler
    def tagger_unload_models(host, port, **kwargs):
        result: StdTransfer.ApiResult = SDWebUI_API._utils_req(
            host, port, "/tagger/v1/unload-interrogators", {}, use_WebUIApiResult=False
        )

        if result.result is None:
            raise RuntimeError(f"{result.info}")

        count = re.findall(r"\d+", str(result.result.content))

        return StdTransfer.ApiResult(
            result=count,
            info="ok",
        )
