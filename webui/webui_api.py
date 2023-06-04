import json
import io
import base64
import requests

from PIL import Image
from pathlib import Path

from dataclasses import dataclass
from enum import Enum

from ..utils.param import ParameterOperation
from ..utils.text import TextOptimization


class WebUI_API():

    @dataclass
    class WebUIApiResult:
        images: list
        parameters: dict
        info: dict

        @property
        def image(self):
            if self.images:
                return self.images[0]
            else:
                return []

    class ExtraUpscaler(str, Enum):
        none = 'None'
        Lanczos = 'Lanczos'
        Nearest = 'Nearest'
        LDSR = 'LDSR'
        BSRGAN = 'BSRGAN'
        ESRGAN_4x = 'ESRGAN_4x'
        R_ESRGAN_General_4xV3 = 'R-ESRGAN General 4xV3'
        ScuNET_GAN = 'ScuNET GAN'
        ScuNET_PSNR = 'ScuNET PSNR'
        SwinIR_4x = 'SwinIR 4x'

    class HiResUpscaler(str, Enum):
        none = 'None'
        Latent = 'Latent'
        LatentAntialiased = 'Latent (antialiased)'
        LatentBicubic = 'Latent (bicubic)'
        LatentBicubicAntialiased = 'Latent (bicubic antialiased)'
        LatentNearest = 'Latent (nearist)'
        LatentNearestExact = 'Latent (nearist-exact)'
        Lanczos = 'Lanczos'
        Nearest = 'Nearest'
        ESRGAN_4x = 'ESRGAN_4x'
        LDSR = 'LDSR'
        ScuNET_GAN = 'ScuNET GAN'
        ScuNET_PSNR = 'ScuNET PSNR'
        SwinIR_4x = 'SwinIR 4x'

    @staticmethod
    def _utils_to_api_result(response):

        if response.status_code != 200:
            raise RuntimeError(response.status_code, response.text)

        r = response.json()
        images = []
        if 'images' in r.keys():
            images = [Image.open(io.BytesIO(base64.b64decode(i)))
                      for i in r['images']]
        elif 'image' in r.keys():
            images = [Image.open(io.BytesIO(base64.b64decode(r['image'])))]

        info = ''
        if 'info' in r.keys():
            try:
                info = json.loads(r['info'])
            except:
                info = r['info']
        elif 'html_info' in r.keys():
            info = r['html_info']
        elif 'caption' in r.keys():
            info = r['caption']

        parameters = ''
        if 'parameters' in r.keys():
            parameters = r['parameters']

        for i in range(len(images)):
            # 加入图片参数
            images[i].info["parameters"] = str(info['infotexts'][i])

        return WebUI_API.WebUIApiResult(images, parameters, info)

    @staticmethod
    def _utils_requests(
        host: str, port: int, api: str, js: dict,
        use_get: bool = False, use_https: bool = False, use_unprocess: bool = False
    ):
        if not hasattr(WebUI_API._utils_requests, 'session'):
            WebUI_API._utils_requests.session = requests.Session()

        if not use_https:
            url = 'http://' + host + ':' + str(port) + api
        else:
            url = 'https://' + host + ':' + str(port) + api

        if use_get:
            res = WebUI_API._utils_requests.session.get(url=url, json=js)
        else:
            res = WebUI_API._utils_requests.session.post(url=url, json=js)

        if res.status_code != 200:
            return None

        if use_unprocess:
            return res
        else:
            return res.json()

    @staticmethod
    def get_vram(host, port, *args):

        res = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/memory", {}, True, False)

        if 'cuda' not in res:
            return None

        vram = res['cuda']['system']

        vram_free = round(vram['free'] / pow(1024, 3), 2)
        vram_used = round(vram['used'] / pow(1024, 3), 2)
        vram_total = round(vram['total'] / pow(1024, 3), 2)
        vram_percent = round((vram['used'] / vram['total']) * 100, 2)

        return host, port, vram_free, vram_used, vram_total, vram_percent

    @staticmethod
    def get_progress(host, port, *args):

        res = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/progress", {}, True, False)

        return host, port,\
            res['state']['job_count'],\
            res['eta_relative'],\
            res['progress'] * 100,\
            res['state']['sampling_step'],\
            res['state']['sampling_steps']

    @staticmethod
    def get_or_match_model(host, port, *args):

        response = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/refresh-checkpoints", js={},
            use_get=False, use_https=False, use_unprocess=True)

        if not response.status_code == 200:
            return None

        response: dict = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/sd-models", js={},
            use_get=True, use_https=False, use_unprocess=False)

        models = [model['model_name'] for model in response]

        if not args:
            return models
        else:
            user_model = args[0]
            return TextOptimization.find_similar_str(models, user_model)

    @staticmethod
    def get_or_match_vae(host, port, *args):
        if args:
            return 'Automatic'
        else:
            return ['None', 'Automatic']

    @staticmethod
    def get_or_match_sampler(host, port, *args):

        response: dict = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/samplers", js={},
            use_get=True, use_https=False, use_unprocess=False)

        samplers = [sampler['name'] for sampler in response]

        if not args:
            return samplers
        else:
            user_sampler = args[0]
            return TextOptimization.find_similar_str(samplers, user_sampler)

    @staticmethod
    def get_or_match_hires_upscaler(host, port, *args):
        pass

    @staticmethod
    def get_or_match_extra_upscaler(host, port, *args):
        pass

    @staticmethod
    def get_or_set_options(host, port, *args):

        if args:
            user_options: dict = args[0]
        else:
            user_options: dict = {}

        options = {
            "sd_model_checkpoint": user_options.get("sd_model_checkpoint", ""),
            "sd_vae": user_options.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": user_options.get("CLIP_stop_at_last_layers", 2),
            "eta_noise_seed_delta": user_options.get("eta_noise_seed_delta", 0)
        }

        response: dict = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/options", js=user_options, use_get=True, use_https=False)

        options = {
            "sd_model_checkpoint": response.get("sd_model_checkpoint", ""),
            "sd_vae": response.get("sd_vae", ""),
            "CLIP_stop_at_last_layers": response.get("CLIP_stop_at_last_layers", 2),
            "eta_noise_seed_delta": response.get("eta_noise_seed_delta", 0)
        }

        return options

    @staticmethod
    def txt2img(host, port, *args):

        params: dict = args[0]

        payload = ParameterOperation.txt2img_params_process(params)

        response = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/txt2img", payload, use_unprocess=True)

        return WebUI_API._utils_to_api_result(response)

    @staticmethod
    def img2img(host, port, *args):

        params, images = args

        payload = ParameterOperation.img2img_params_process(params, images)

        response = WebUI_API._utils_requests(
            host, port, "/sdapi/v1/img2img", payload, use_unprocess=True)

        return WebUI_API._utils_to_api_result(response)
