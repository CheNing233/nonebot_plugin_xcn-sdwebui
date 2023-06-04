import json
import re
import copy

from pathlib import Path

from .img import PILImageOperation
from .text import TextOptimization


class ParameterOperation:

    @staticmethod
    def get_cfg_path(filename: str = None):
        if filename:
            return str(Path(__file__).parent.parent.resolve() / 'config' / filename)
        else:
            return str(Path(__file__).parent.parent.resolve() / 'config')

    class txtimg_matcher:
        patterns_dict = {
            "prompt": [r"(.*?)($|\n)"],
            "negative_prompt": [r"Negative prompt:(.*?)($|\n)", r"-ngt(.*?)($|\n)"],

            "steps": [r"Steps:(.*?)(,|$|\n)", r"-steps(.*?)(,|$|\n)"],
            "sampler_name": [r"Sampler:(.*?)(,|$|\n)", r"-sampler(.*?)(,|$|\n)"],
            "cfg_scale": [r"CFG scale:(.*?)(,|$|\n)", r"-cfg(.*?)(,|$|\n)"],
            "seed": [r"Seed:(.*?)(,|$|\n)", r"-seed(.*?)(,|$|\n)"],
            "width": [r"Size:(.*?)(,|$|\n)", r"-size(.*?)(,|$|\n)"],
            "height": [r"Size:(.*?)(,|$|\n)", r"-size(.*?)(,|$|\n)"],

            "n_iter": [r"-cnt(.*?)(,|$|\n)"],

            "enable_hr": [r"-hr(.*?)(,|$|\n)"],
            "denoising_strength": [
                r"Denoising strength:(.*?)(,|$|\n)",
                r"-ds(.*?)(,|$|\n)",
            ],
            "hr_scale": [r"Hires upscale:(.*?)(,|$|\n)", r"-upscale(.*?)(,|$|\n)"],
            "hr_upscaler": [r"Hires upscaler:(.*?)(,|$|\n)", r"-upscaler(.*?)(,|$|\n)"],
            "hr_second_pass_steps": [
                r"Hires steps:(.*?)(,|$|\n)",
                r"-hrsteps(.*?)(,|$|\n)",
            ],

            "sd_model_checkpoint": [r"Model:(.*?)(,|$|\n)", r"-model(.*?)(,|$|\n)"],
            "sd_vae": [r"-vae(.*?)(,|$|\n)"],
            "CLIP_stop_at_last_layers": [
                r"Clip skip:(.*?)(,|$|\n)",
                r"-clip(.*?)(,|$|\n)",
            ],
            "eta_noise_seed_delta": [r"ENSD:(.*?)(,|$|\n)", r"-ensd(.*?)(,|$|\n)"],
        }

        base_params = {"override_settings": {}}

        # 匹配

        bool_group = ["enable_hr"]

        int_group = [
            "steps",
            "seed",
            "hr_second_pass_steps",
            "eta_noise_seed_delta",
            "CLIP_stop_at_last_layers",
            "n_iter",
        ]

        float_group = ["cfg_scale", "denoising_strength", "hr_scale"]

        override_settings_group = [
            "sd_model_checkpoint",
            "sd_vae",
            "CLIP_stop_at_last_layers",
            "eta_noise_seed_delta",
        ]

    class extra_matcher:
        patterns_dict = {
            "gfpgan_visibility": [r"-gfp(.*?)(,|$|\n)"],
            "codeformer_visibility": [r"-codeformer(.*?)(,|$|\n)"],
            "codeformer_weight": [r"-codeformerw(.*?)(,|$|\n)"],
            "upscaling_resize": [r"-resize(.*?)(,|$|\n)"],
            "upscaling_crop": [r"-crop(.*?)(,|$|\n)"],
            "upscaling_resize_w": [r"-tosize(.*?)(,|$|\n)"],
            "upscaling_resize_h": [r"-tosize(.*?)(,|$|\n)"],
            "upscaler_1": [r"-upscaler1(.*?)(,|$|\n)"],
            "upscaler_2": [r"-upscaler2(.*?)(,|$|\n)"],
            "extras_upscaler_2_visibility": [r"-upscaler2w(.*?)(,|$|\n)"],
        }

        params = {}

        # 匹配

        bool_group = ["upscaling_crop"]

        float_group = [
            "gfpgan_visibility",
            "codeformer_visibility",
            "codeformer_weight",
            "upscaling_resize",
            "extras_upscaler_2_visibility",
        ]

    @staticmethod
    def magic_trans_to_params(
        text_o: str,
        patterns_dict_o: dict = {},
        base_params_o: dict = {},
        int_group_o: list = [],
        float_group_o: list = [],
        bool_group_o: list = [],
        override_settings_group_o: list = []
    ) -> dict:
        # 深复制
        text: str = copy.deepcopy(text_o)
        patterns_dict: dict = copy.deepcopy(patterns_dict_o)
        base_params: dict = copy.deepcopy(base_params_o)
        int_group: list = copy.deepcopy(int_group_o)
        float_group: list = copy.deepcopy(float_group_o)
        bool_group: list = copy.deepcopy(bool_group_o)
        override_settings_group: list = copy.deepcopy(
            override_settings_group_o)

        # 预处理
        text = text.replace("\n", "")

        for patterns_name, patterns in patterns_dict.items():
            if patterns_name == "prompt":
                pass
            else:
                for pattern in patterns:
                    try:
                        item_proc1 = re.search(
                            pattern=pattern, string=text).group()
                        text = text.replace(item_proc1, "\n" + item_proc1)
                    except:
                        continue

        for patterns_name, patterns in patterns_dict.items():
            for pattern in patterns:
                try:
                    item_proc1 = (
                        re.search(pattern=pattern, string=text).group(
                            1).strip()
                    )
                    if not bool(item_proc1):
                        continue
                except:
                    continue

                # 数据类型转换
                try:
                    if patterns_name in int_group:
                        item_proc2 = int(item_proc1)

                    elif patterns_name in float_group:
                        item_proc2 = round(float(item_proc1), 2)

                    elif patterns_name in bool_group:
                        item_proc2 = bool(int(item_proc1))

                    elif patterns_name == "width":
                        item_proc2 = int(item_proc1.strip().split("x")[0])

                    elif patterns_name == "height":
                        item_proc2 = int(item_proc1.strip().split("x")[1])

                    elif patterns_name == "upscaling_resize_w":
                        item_proc2 = int(item_proc1.strip().split("x")[0])

                    elif patterns_name == "upscaling_resize_h":
                        item_proc2 = int(item_proc1.strip().split("x")[1])

                    else:
                        item_proc2 = item_proc1

                except:
                    continue

                # 分组
                if patterns_name in override_settings_group:
                    base_params["override_settings"][patterns_name] = item_proc2

                else:
                    base_params[patterns_name] = item_proc2

        return base_params

    @staticmethod
    def txt2img_params_process(user_params: dict):

        with open(ParameterOperation.get_cfg_path('param_txt2img.json'), "r") as file:
            preset_params: dict = json.load(file)

        final_params = {
            "enable_hr": preset_params.get('enable_hr', False),
            "hr_scale": preset_params.get('hr_scale', 2),
            "hr_upscaler": preset_params.get('hr_upscaler', 'Latent'),
            "hr_second_pass_steps": preset_params.get('hr_second_pass_steps', 0),
            "hr_resize_x": preset_params.get('hr_resize_x', 0),
            "hr_resize_y": preset_params.get('hr_resize_y', 0),
            "denoising_strength": preset_params.get('denoising_strength', 0.7),
            "firstphase_width": preset_params.get('firstphase_width', 0),
            "firstphase_height": preset_params.get('firstphase_height', 0),
            "prompt": preset_params.get('prompt', ''),
            "styles": preset_params.get('styles', []),
            "seed": preset_params.get('seed', -1),
            "subseed": preset_params.get('subseed', -1),
            "subseed_strength": preset_params.get('subseed_strength', 0.0),
            "seed_resize_from_h": preset_params.get('seed_resize_from_h', 0),
            "seed_resize_from_w": preset_params.get('seed_resize_from_w', 0),
            "batch_size": preset_params.get('batch_size', 1),
            "n_iter": preset_params.get('n_iter', 1),
            "steps": preset_params.get('steps', 20),
            "cfg_scale": preset_params.get('cfg_scale', 7.0),
            "width": preset_params.get('width', 512),
            "height": preset_params.get('height', 512),
            "restore_faces": preset_params.get('restore_faces', False),
            "tiling": preset_params.get('tiling', False),
            "do_not_save_samples": preset_params.get('do_not_save_samples', False),
            "do_not_save_grid": preset_params.get('do_not_save_grid', True),
            "negative_prompt": preset_params.get('negative_prompt', ''),
            "eta": preset_params.get('eta', 1.0),
            "s_churn": preset_params.get('s_churn', 0),
            "s_tmax": preset_params.get('s_tmax', 0),
            "s_tmin": preset_params.get('s_tmin', 0),
            "s_noise": preset_params.get('s_noise', 1),
            "override_settings": preset_params.get('override_settings', {}),
            "override_settings_restore_afterwards": preset_params.get(
                'override_settings_restore_afterwards', True),
            "sampler_name": preset_params.get('sampler_name', 'Euler a'),
            "sampler_index": preset_params.get('sampler_index', 'Euler a'),
            "script_name": preset_params.get('script_name'),
            "script_args": preset_params.get('script_args', []),
            "send_images": preset_params.get('send_images', True),
            "save_images": preset_params.get('save_images', True),
            "alwayson_scripts": preset_params.get('alwayson_scripts', {}),
        }

        for param in final_params:
            final_params[param] = user_params.get(param, final_params[param])

        final_params['override_settings'] = preset_params.get(
            'override_settings', {})

        return final_params

    @staticmethod
    def img2img_params_process(user_params: dict, user_images: list = None):

        with open(ParameterOperation.get_cfg_path('param_img2img.json'), "r") as file:
            preset_params: dict = json.load(file)

        final_params = {
            "init_images": [PILImageOperation.b64_img(x) for x in preset_params.get('images', [])],
            "resize_mode": preset_params.get('resize_mode', 0),
            "denoising_strength": preset_params.get('denoising_strength', 0.75),
            "mask_image": PILImageOperation.b64_img(preset_params.get('mask_image')) if preset_params.get('mask_image') is not None else '',
            "mask_blur": preset_params.get('mask_blur', 4),
            "inpainting_fill": preset_params.get('inpainting_fill', 0),
            "inpaint_full_res": preset_params.get('inpaint_full_res', True),
            "inpaint_full_res_padding": preset_params.get('inpaint_full_res_padding', 0),
            "inpainting_mask_invert": preset_params.get('inpainting_mask_invert', 0),
            "initial_noise_multiplier": preset_params.get('initial_noise_multiplier', 1),
            "prompt": preset_params.get('prompt', ""),
            "styles": preset_params.get('styles', []),
            "seed": preset_params.get('seed', -1),
            "subseed": preset_params.get('subseed', -1),
            "subseed_strength": preset_params.get('subseed_strength', 0),
            "seed_resize_from_h": preset_params.get('seed_resize_from_h', 0),
            "seed_resize_from_w": preset_params.get('seed_resize_from_w', 0),
            "batch_size": preset_params.get('batch_size', 1),
            "n_iter": preset_params.get('n_iter', 1),
            "steps": preset_params.get('steps', 20),
            "cfg_scale": preset_params.get('cfg_scale', 7.0),
            "image_cfg_scale": preset_params.get('image_cfg_scale', 1.5),
            "width": preset_params.get('width', 512),
            "height": preset_params.get('height', 512),
            "restore_faces": preset_params.get('restore_faces', False),
            "tiling": preset_params.get('tiling', False),
            "do_not_save_samples": preset_params.get('do_not_save_samples', True),
            "do_not_save_grid": preset_params.get('do_not_save_grid', True),
            "negative_prompt": preset_params.get('negative_prompt', ""),
            "eta": preset_params.get('eta', 1.0),
            "s_churn": preset_params.get('s_churn', 0),
            "s_tmax": preset_params.get('s_tmax', 0),
            "s_tmin": preset_params.get('s_tmin', 0),
            "s_noise": preset_params.get('s_noise', 1),
            "override_settings": preset_params.get('override_settings', {}),
            "override_settings_restore_afterwards": preset_params.get('override_settings_restore_afterwards', True),
            "sampler_name": preset_params.get('sampler_name', 'Euler a'),
            "sampler_index": preset_params.get('sampler_index', 'Euler a'),
            "include_init_images": preset_params.get('include_init_images', False),
            "script_name": preset_params.get('script_name', ''),
            "script_args": preset_params.get('script_args', []),
            "send_images": preset_params.get('send_images', True),
            "save_images": preset_params.get('save_images', False),
            "alwayson_scripts": preset_params.get('alwayson_scripts', {}),
        }

        for param in final_params:
            final_params[param] = user_params.get(param, final_params[param])

        final_params['override_settings'] = preset_params.get(
            'override_settings', {})

        if user_images:
            final_params['init_images'] = [
                PILImageOperation.b64_img(image) for image in user_images
            ]

        return final_params

    @staticmethod
    def params_to_file(user_params: dict, file_name: str):

        with open(ParameterOperation.get_cfg_path(file_name), 'r') as file:
            preset_params = json.load(file)

        for param in preset_params:
            """基于preset_params将user_params叠入最终结果"""
            if param in user_params and param != 'override_settings':
                preset_params[param] = user_params[param]

        if 'override_settings' in user_params:
            for ovr_s in preset_params['override_settings']:
                """基于preset_params将user_params叠入最终结果"""
                if ovr_s in user_params['override_settings']:
                    preset_params['override_settings'][ovr_s] =\
                        user_params['override_settings'][ovr_s]

        with open(ParameterOperation.get_cfg_path(file_name), 'w') as file:
            json.dump(preset_params, file)

        return preset_params

    @staticmethod
    def fix_string_params(
            user_params: dict, target_key: str, std_list: list,
            is_overridesettings: bool = False
    ):

        if is_overridesettings:

            if target_key in user_params['override_settings']:

                user_params['override_settings'][target_key] =\
                    TextOptimization.find_similar_str(
                        std_list,
                        user_params['override_settings'][target_key])

        else:

            if target_key in user_params:

                user_params[target_key] =\
                    TextOptimization.find_similar_str(
                        std_list,
                        user_params[target_key])

        return user_params
