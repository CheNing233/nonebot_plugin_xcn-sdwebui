import json
import requests
import io
import base64
from PIL import Image
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

import json


class Upscaler(str, Enum):
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


@dataclass
class WebUI_ApiResult:
    images: list
    parameters: dict
    info: dict

    @property
    def image(self):
        if self.images:
            return self.images[0]
        else:
            return []


def b64_img(image: Image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")

    img_base64 = 'data:image/png;base64,' + \
        str(base64.b64encode(buffered.getvalue()), 'utf-8')
    return img_base64


def b64_bytes(image: bytes):
    b64str = base64.b64encode(io.BytesIO(image).getvalue()).decode('utf-8')
    return b64str


def raw_b64_img(image: Image):
    # XXX controlnet only accepts RAW base64 without headers
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = str(base64.b64encode(buffered.getvalue()), 'utf-8')
    return img_base64


class WebUI_Api:

    fn_dict = {}

    def __init__(self,
                 host='127.0.0.1',
                 port=7860,
                 baseurl=None,
                 sampler='Euler a',
                 steps=20,
                 use_https=False):
        """
        gradio_cli = Client(src="http://127.0.0.1:7860/api/predict/")

        self.fn_dict = gradio_cli.view_api(
            print_info=False, return_format="dict")
        """

        self.fn_dict = self.get_fn_info()

        if baseurl is None:
            if use_https:
                baseurl = f'https://{host}:{port}/sdapi/v1'
            else:
                baseurl = f'http://{host}:{port}/sdapi/v1'

        self.baseurl = baseurl
        self.default_sampler = sampler
        self.default_steps = steps

        self.fn_unload_tagger_model, _ = self.search_unname_fn_returns(
            match_min=3,
            labelname='Remove duplicated tag',
            type_python='bool',
            component='Checkbox'
        )
        self.fn_unload_tagger_model += 2

        self.fn_vae, _ = self.search_unname_fn_returns(
            match_min=1, labelname="SD VAE")

        self.session = requests.Session()

    def _to_api_result(self, response):

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

        return WebUI_ApiResult(images, parameters, info)

    def run_predict(self, fn_index: int, data: list = []):
        payload = {
            "data": data,
            "fn_index": fn_index
        }
        response = self.session.post(
            url='http://127.0.0.1:7860/run/predict/', json=payload)
        return response.json()

    def get_fn_info(self):

        response = requests.get(url=r'http://127.0.0.1:7860/info')

        return response.json()

    def get_unname_endpoint_dict(self):
        return self.fn_dict['unnamed_endpoints']

    def search_unname_fn_returns(
            self,
            match_min: int,
            labelname: str = None,
            type_python: str = None,
            type_description: str = None,
            component: str = None
    ):
        match_cnt: int = 0

        for fn_name, fn_dict in self.fn_dict['unnamed_endpoints'].items():
            for ret_dict in fn_dict['returns']:
                match_cnt = 0

                if bool(labelname) and 'label' in ret_dict and ret_dict['label'] == labelname:
                    match_cnt += 1
                if bool(type_python) and 'python_type' in ret_dict and ret_dict['python_type']['type'] == type_python:
                    match_cnt += 1
                if bool(type_description) and 'python_type' in ret_dict and ret_dict['python_type']['description'] == type_description:
                    match_cnt += 1
                if bool(component) and 'component' in ret_dict and ret_dict['component'] == component:
                    match_cnt += 1

                if match_cnt >= match_min:
                    return int(fn_name), ret_dict

    def search_unname_fn_params(
            self,
            match_min: int,
            labelname: str = None,
            type_python: str = None,
            type_description: str = None,
            component: str = None,
            example: str = None
    ):
        match_cnt: int = 0
        for fn_name, fn_dict in self.fn_dict['unnamed_endpoints'].items():
            for ret_dict in fn_dict['parameters']:

                match_cnt = 0

                if bool(labelname) and 'label' in ret_dict and ret_dict['label'] == labelname:
                    match_cnt += 1
                if bool(type_python) and 'python_type' in ret_dict and ret_dict['python_type']['type'] == type_python:
                    match_cnt += 1
                if bool(type_description) and 'python_type' in ret_dict and ret_dict['python_type']['description'] == type_description:
                    match_cnt += 1
                if bool(component) and 'component' in ret_dict and ret_dict['component'] == component:
                    match_cnt += 1
                if bool(example) and 'example_input' in ret_dict and ret_dict['example_input'] == example:
                    match_cnt += 1

                if match_cnt >= match_min:
                    return int(fn_name), ret_dict

    def txt2img(self, params: dict):

        # deprecated: use sampler_name
        use_deprecated_controlnet = params.get(
            'use_deprecated_controlnet', False)

        payload = {
            "enable_hr": params.get('enable_hr', False),
            "hr_scale": params.get('hr_scale', 2),
            "hr_upscaler": params.get('hr_upscaler', HiResUpscaler.Latent),
            "hr_second_pass_steps": params.get('hr_second_pass_steps', 0),
            "hr_resize_x": params.get('hr_resize_x', 0),
            "hr_resize_y": params.get('hr_resize_y', 0),
            "denoising_strength": params.get('denoising_strength', 0.7),
            "firstphase_width": params.get('firstphase_width', 0),
            "firstphase_height": params.get('firstphase_height', 0),
            "prompt": params.get('prompt', ''),
            "styles": params.get('styles', []),
            "seed": params.get('seed', -1),
            "subseed": params.get('subseed', -1),
            "subseed_strength": params.get('subseed_strength', 0.0),
            "seed_resize_from_h": params.get('seed_resize_from_h', 0),
            "seed_resize_from_w": params.get('seed_resize_from_w', 0),
            "batch_size": params.get('batch_size', 1),
            "n_iter": params.get('n_iter', 1),
            "steps": params.get('steps', self.default_steps),
            "cfg_scale": params.get('cfg_scale', 7.0),
            "width": params.get('width', 512),
            "height": params.get('height', 512),
            "restore_faces": params.get('restore_faces', False),
            "tiling": params.get('tiling', False),
            "do_not_save_samples": params.get('do_not_save_samples', False),
            "do_not_save_grid": params.get('do_not_save_grid', True),
            "negative_prompt": params.get('negative_prompt', ''),
            "eta": params.get('eta', 1.0),
            "s_churn": params.get('s_churn', 0),
            "s_tmax": params.get('s_tmax', 0),
            "s_tmin": params.get('s_tmin', 0),
            "s_noise": params.get('s_noise', 1),
            "override_settings": params.get('override_settings', {}),
            "override_settings_restore_afterwards": params.get(
                'override_settings_restore_afterwards', True),
            "sampler_name": params.get('sampler_name', self.default_sampler),
            "sampler_index": params.get('sampler_index', self.default_sampler),
            "script_name": params.get('script_name'),
            "script_args": params.get('script_args', []),
            "send_images": params.get('send_images', True),
            "save_images": params.get('save_images', True),
            "alwayson_scripts": params.get('alwayson_scripts', {}),
        }
        controlnet_units = params.get('controlnet_units', [])

        if use_deprecated_controlnet and controlnet_units and len(controlnet_units) > 0:
            payload["controlnet_units"] = [x.to_dict()
                                           for x in controlnet_units]
            return self.custom_post('controlnet/txt2img', payload=payload)

        if controlnet_units and len(controlnet_units) > 0:
            payload["alwayson_scripts"]["ControlNet"] = {
                "args": [x.to_dict() for x in controlnet_units]
            }

        response = self.session.post(
            url=f'{self.baseurl}/txt2img', json=payload)
        return self._to_api_result(response)

    def img2img(self, params: dict):

        controlnet_units = params.get('controlnet_units', [])
        use_deprecated_controlnet = params.get(
            'use_deprecated_controlnet', False)
        mask_image = params.get('mask_image', None)  # PIL Image mask

        if params.get('sampler_name') is None:
            params['sampler_name'] = self.default_sampler
        if params.get('sampler_index') is None:
            params['sampler_index'] = self.default_sampler
        if params.get('steps') is None:
            params['steps'] = self.default_steps
        if params.get('script_args') is None:
            params['script_args'] = []

        payload = {
            "init_images": [b64_img(x) for x in params.get('images', [])],
            "resize_mode": params.get('resize_mode', 0),
            "denoising_strength": params.get('denoising_strength', 0.75),
            "mask_image": b64_img(params.get('mask_image')) if params.get('mask_image') is not None else None,
            "mask_blur": params.get('mask_blur', 4),
            "inpainting_fill": params.get('inpainting_fill', 0),
            "inpaint_full_res": params.get('inpaint_full_res', True),
            "inpaint_full_res_padding": params.get('inpaint_full_res_padding', 0),
            "inpainting_mask_invert": params.get('inpainting_mask_invert', 0),
            "initial_noise_multiplier": params.get('initial_noise_multiplier', 1),
            "prompt": params.get('prompt', ""),
            "styles": params.get('styles', []),
            "seed": params.get('seed', -1),
            "subseed": params.get('subseed', -1),
            "subseed_strength": params.get('subseed_strength', 0),
            "seed_resize_from_h": params.get('seed_resize_from_h', 0),
            "seed_resize_from_w": params.get('seed_resize_from_w', 0),
            "batch_size": params.get('batch_size', 1),
            "n_iter": params.get('n_iter', 1),
            "steps": params.get('steps'),
            "cfg_scale": params.get('cfg_scale', 7.0),
            "image_cfg_scale": params.get('image_cfg_scale', 1.5),
            "width": params.get('width', 512),
            "height": params.get('height', 512),
            "restore_faces": params.get('restore_faces', False),
            "tiling": params.get('tiling', False),
            "do_not_save_samples": params.get('do_not_save_samples', True),
            "do_not_save_grid": params.get('do_not_save_grid', True),
            "negative_prompt": params.get('negative_prompt', ""),
            "eta": params.get('eta', 1.0),
            "s_churn": params.get('s_churn', 0),
            "s_tmax": params.get('s_tmax', 0),
            "s_tmin": params.get('s_tmin', 0),
            "s_noise": params.get('s_noise', 1),
            "override_settings": params.get('override_settings', {}),
            "override_settings_restore_afterwards": params.get('override_settings_restore_afterwards', True),
            "sampler_name": params.get('sampler_name'),
            "sampler_index": params.get('sampler_index'),
            "include_init_images": params.get('include_init_images', False),
            "script_name": params.get('script_name'),
            "script_args": params.get('script_args'),
            "send_images": params.get('send_images', True),
            "save_images": params.get('save_images', False),
            "alwayson_scripts": params.get('alwayson_scripts', {}),
        }

        if mask_image is not None:
            payload['mask'] = b64_img(mask_image)

        if use_deprecated_controlnet and controlnet_units and len(controlnet_units) > 0:
            payload["controlnet_units"] = [x.to_dict()
                                           for x in controlnet_units]
            return self.custom_post('controlnet/img2img', payload=payload)

        if controlnet_units and len(controlnet_units) > 0:
            payload["alwayson_scripts"]["ControlNet"] = {
                "args": [x.to_dict() for x in controlnet_units]
            }
        response = self.session.post(
            url=f'{self.baseurl}/img2img', json=payload)
        return self._to_api_result(response)

    def extra_single_image(self, params: dict):

        payload = {
            "resize_mode": params.get("resize_mode", 0),
            "show_extras_results": params.get("show_extras_results", True),
            "gfpgan_visibility": params.get("gfpgan_visibility", 0),
            "codeformer_visibility": params.get("codeformer_visibility", 0),
            "codeformer_weight": params.get("codeformer_weight", 0),
            "upscaling_resize": params.get("upscaling_resize", 2),
            "upscaling_resize_w": params.get("upscaling_resize_w", 512),
            "upscaling_resize_h": params.get("upscaling_resize_h", 512),
            "upscaling_crop": params.get("upscaling_crop", True),
            "upscaler_1": params.get("upscaler_1", "None"),
            "upscaler_2": params.get("upscaler_2", "None"),
            "extras_upscaler_2_visibility": params.get("extras_upscaler_2_visibility", 0),
            "upscale_first": params.get("upscale_first", False),
            "image": b64_img(params["image"]),
        }

        response = self.session.post(
            url=f'{self.baseurl}/extra-single-image', json=payload)

        return self._to_api_result(response)

    def extra_batch_images(self,
                           images,  # list of PIL images
                           name_list=None,  # list of image names
                           resize_mode=0,
                           show_extras_results=True,
                           gfpgan_visibility=0,
                           codeformer_visibility=0,
                           codeformer_weight=0,
                           upscaling_resize=2,
                           upscaling_resize_w=512,
                           upscaling_resize_h=512,
                           upscaling_crop=True,
                           upscaler_1="None",
                           upscaler_2="None",
                           extras_upscaler_2_visibility=0,
                           upscale_first=False,
                           ):
        if name_list is not None:
            if len(name_list) != len(images):
                raise RuntimeError('len(images) != len(name_list)')
        else:
            name_list = [f'image{i + 1:05}' for i in range(len(images))]
        images = [b64_img(x) for x in images]

        image_list = []
        for name, image in zip(name_list, images):
            image_list.append({
                "data": image,
                "name": name
            })

        payload = {
            "resize_mode": resize_mode,
            "show_extras_results": show_extras_results,
            "gfpgan_visibility": gfpgan_visibility,
            "codeformer_visibility": codeformer_visibility,
            "codeformer_weight": codeformer_weight,
            "upscaling_resize": upscaling_resize,
            "upscaling_resize_w": upscaling_resize_w,
            "upscaling_resize_h": upscaling_resize_h,
            "upscaling_crop": upscaling_crop,
            "upscaler_1": upscaler_1,
            "upscaler_2": upscaler_2,
            "extras_upscaler_2_visibility": extras_upscaler_2_visibility,
            "upscale_first": upscale_first,
            "imageList": image_list,
        }

        response = self.session.post(
            url=f'{self.baseurl}/extra-batch-images', json=payload)
        return self._to_api_result(response)

    def tagger_image(self, params: dict):
        payload = {
            "image": b64_img(params['image']),
            "model": params.get('model', 'wd14-vit-v2-git'),
            "threshold": params.get('threshold', 0.35)
        }

        response = self.session.post(
            url=f'http://127.0.0.1:7860/tagger/v1/interrogate', json=payload)

        return response.json()['caption']

    def get_tagger_models(self):
        response = self.session.get(
            url=f'http://127.0.0.1:7860/tagger/v1/interrogators')
        return response.json()['models']

    def unload_tagger_models(self):

        return self.run_predict(fn_index=self.fn_unload_tagger_model)

    def get_options(self):
        response = self.session.get(url=f'{self.baseurl}/options')
        return response.json()

    def set_options(self, options):
        response = self.session.post(
            url=f'{self.baseurl}/options', json=options)
        return response.json()

    def get_progress(self):
        response = self.session.get(url=f'{self.baseurl}/progress')
        return response.json()

    def get_cmd_flags(self):
        response = self.session.get(url=f'{self.baseurl}/cmd-flags')
        return response.json()

    def get_samplers(self):
        response = self.session.get(url=f'{self.baseurl}/samplers')
        return response.json()

    def get_upscalers(self):
        response = self.session.get(url=f'{self.baseurl}/upscalers')
        return response.json()

    def get_sd_models(self):
        response = self.session.get(url=f'{self.baseurl}/sd-models')
        return response.json()

    def get_hypernetworks(self):
        response = self.session.get(url=f'{self.baseurl}/hypernetworks')
        return response.json()

    def unload_checkpoint(self):
        response = self.session.post(url=f'{self.baseurl}/unload-checkpoint')
        return response.json()

    def reload_checkpoint(self):
        response = self.session.post(url=f'{self.baseurl}/reload-checkpoint')
        return response.json()

    def refresh_checkpoints(self):
        response = self.session.post(url=f'{self.baseurl}/refresh-checkpoints')
        return response.json()

    def util_get_model_names(self):
        return sorted([x['title'] for x in self.get_sd_models()])

    def util_set_model(self, name, find_closest=True):
        if find_closest:
            name = name.lower()
        models = self.util_get_model_names()
        found_model = None
        if name in models:
            found_model = name
        elif find_closest:
            import difflib

            def str_simularity(a, b):
                return difflib.SequenceMatcher(None, a, b).ratio()
            max_sim = 0.0
            max_model = models[0]
            for model in models:
                sim = str_simularity(name, model)
                if sim >= max_sim:
                    max_sim = sim
                    max_model = model
            found_model = max_model
        if found_model:
            options = {}
            options['sd_model_checkpoint'] = found_model
            self.set_options(options)
            return found_model
        else:
            return ''

    def util_get_vae_names(self):
        return self.run_predict(self.fn_vae)['data'][0]['choices']

    def util_set_vae(self, name):
        vae_list = self.util_get_vae_names()

        vae = self.util_find_similar_str(vae_list, name)

        self.set_options({'sd_vae': vae})
        return vae

    def util_get_sampler_names(self):
        return sorted([x['name'] for x in self.get_samplers()])

    def util_get_upscaler_names(self):
        return sorted([x['name'] for x in self.get_upscalers()])

    def uitl_get_hires_upscaler_names(self):

        _, res_dict = self.search_unname_fn_params(
            match_min=2, example='Latent', component='Dropdown')

        hires_upscaler_str: str = str(
            res_dict['type_description']).replace('Option from:', '')

        hires_upscaler_str = hires_upscaler_str.strip().\
            replace('[', '').replace(']', '').replace('\'', '')

        hires_upscalers_list = hires_upscaler_str.split(',')

        return [key.strip() for key in hires_upscalers_list]

    def util_find_similar_str(self, string_list, sub_str):
        max_similar = 0
        most_similar_str = ""

        import difflib
        for string in string_list:
            similarity_ratio = difflib.SequenceMatcher(
                None, string, sub_str).ratio()
            if similarity_ratio > max_similar:
                max_similar = similarity_ratio
                most_similar_str = string

        return most_similar_str
