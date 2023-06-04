import pynvml

from ._api import WebUI_Api, WebUI_ApiResult
from ..utils.text import ParameterOperation, PILImageOperation, TextOptimization


class WebUI():

    def __init__(self) -> None:

        self.api = WebUI_Api()
        self.queue_count = 0

    def get_queue(self) -> str:

        # 初始化pynvml
        pynvml.nvmlInit()

        mainGpuHandle = pynvml.nvmlDeviceGetHandleByIndex(0)

        # 获取当前显存使用情况
        mainGpuinfo = pynvml.nvmlDeviceGetMemoryInfo(mainGpuHandle)
        mainGpuUsage = mainGpuinfo.used / mainGpuinfo.total * 100

        # 获取GPU温度
        mainGpuTemp = pynvml.nvmlDeviceGetTemperature(
            mainGpuHandle, pynvml.NVML_TEMPERATURE_GPU)

        # 清理pynvml环境
        pynvml.nvmlShutdown()

        progress = self.api.get_progress()

        if progress['state']['job_count'] != 0:
            workstr = "Working"
        else:
            self.queue_count = 0
            workstr = "Idle"

        return (
            "队列：%s, %d task(s)\n"
            "显卡：%.2f%%, %.1f°C\n"
            "任务剩时：%.2f s\n"
            "任务进度：%.2f%%, %d/%d"
            % (
                workstr, self.queue_count,
                mainGpuUsage, mainGpuTemp,
                progress['eta_relative'],
                progress['progress'] * 100,
                progress['state']['sampling_step'],
                progress['state']['sampling_steps'],
            )
        )

    def magic_to_img(self, curse: str = '', imgs: list = []):

        params = {}
        params = ParameterOperation.magic_trans_to_params(curse)

        if bool(imgs):
            base_file = 'sd_img2img.json'
        else:
            base_file = 'sd_txt2img.json'

        base_params = {}
        base_params = self.actions.open_json_file_as_base(base_file, params)

        res: WebUI_ApiResult = None
        if bool(imgs):
            base_params['images'] = imgs
            res = self.api.img2img(base_params)
        else:
            res = self.api.txt2img(base_params)

        return self.actions.save_pil_imgs(res.images, res.info)

    def curse_to_file(self, curse: str = '', file_name: str = ''):

        params = self.actions.curse_trans_to_params(curse)

        base_params = {}
        base_params = self.actions.open_json_file_as_base(file_name, params)

        self.actions.write_json_file_with_base(file_name, base_params)
        if ('override_settings' in params) and bool(params['override_settings']):
            self.opr_options(params['override_settings'])

        res_params = []
        res_params = list(base_params.items())+list(self.opr_options().items())

        return [str(i) for i in res_params]

    def curse_to_file_for_extra(self, curse: str = ''):

        params = self.actions.curse_trans_to_params_for_extra(curse)

        base_params = {}
        base_params = self.actions.open_json_file_as_base(
            'sd_extra.json', params)

        self.actions.write_json_file_with_base('sd_extra.json', base_params)

        res_params = []
        res_params = list(base_params.items())

        return [str(i) for i in res_params]

    def imgs_to_extra(self, curse: str = '', img: list = []):

        params = {}
        params = self.actions.curse_trans_to_params_for_extra(curse)
        params["image"] = img[0]

        base_file = 'sd_extra.json'
        base_params = self.actions.open_json_file_as_base(base_file, params)

        res = self.api.extra_single_image(base_params)

        img_add_params = {
            'infotexts': [
                base_params
            ]
        }

        return self.actions.save_pil_imgs(res.images, img_add_params)

    def get_pnginfo(self, img):

        if 'parameters' in img.info:
            return img.info['parameters']
        else:
            return 'None'

    def get_tagger(self, img):

        params = {
            "image": img
        }

        base_file = 'sd_tagger.json'
        base_params = self.actions.open_json_file_as_base(base_file, params)

        res_dict: dict = self.api.tagger_image(base_params)

        general: float = round(res_dict['general']*100.0000, 2)
        sensitive: float = round(res_dict['sensitive']*100.0000, 2)
        questionable: float = round(res_dict['questionable']*100.0000, 2)
        explicit: float = round(res_dict['explicit']*100.0000, 2)

        del res_dict['general']
        del res_dict['sensitive']
        del res_dict['questionable']
        del res_dict['explicit']

        curse = [word for word in res_dict.keys()]

        return general, sensitive, questionable, explicit, curse

    def unload_tagger_model(self):
        self.api.unload_tagger_models()

    def opr_options(self, settings: dict = None):
        if settings:
            self.api.set_options(settings)
            return None

        else:
            base_options = {
                "sd_model_checkpoint": "",
                "sd_vae": "",
                "CLIP_stop_at_last_layers": "",
                "eta_noise_seed_delta": ""
            }

            options = self.api.get_options()

            for key in base_options:
                base_options[key] = options[key]

            return base_options

    def reload_model(self):
        self.unload_tagger_model()
        self.api.unload_checkpoint()
        self.api.reload_checkpoint()

    def r_tagger_models(self):
        return self.api.get_tagger_models()

    def w_tagger_settings(self, modelname: str = None, threshold: float = None):
        models_name_list = self.api.get_tagger_models()

        base_params: dict = {}
        if bool(modelname):
            base_params['model'] = self.api.util_find_similar_str(
                models_name_list, modelname)

        if bool(threshold):
            base_params['threshold'] = threshold

        base_params = self.actions.open_json_file_as_base(
            'sd_extra.json', base_params)

        self.actions.write_json_file_with_base(
            'sd_extra.json', base_params)

        return base_params

    def r_sampler(self):
        return self.api.util_get_sampler_names()

    def w_sampler(self, dest_file: str, sampler_name: str) -> str:

        samplers_name_list = self.api.util_get_sampler_names()

        dest_sampler = self.api.util_find_similar_str(
            samplers_name_list, sampler_name)

        base_params = self.actions.open_json_file_as_base(
            dest_file, {'sampler_name': dest_sampler})

        self.actions.write_json_file_with_base(
            dest_file, base_params)

        return dest_sampler

    def r_upscaler(self):
        return self.api.util_get_upscaler_names()

    def w_upscaler(self, is_upscaler2: bool = False, upscaler_name: str = 'None'):

        upcalers_name_list = self.api.util_get_upscaler_names()

        dest_upscaler = self.api.util_find_similar_str(
            upcalers_name_list, upscaler_name)

        base_params = {}

        if not is_upscaler2:
            base_params = self.actions.open_json_file_as_base(
                'sd_extra.json', {'upscaler_1': dest_upscaler})
        else:
            base_params = self.actions.open_json_file_as_base(
                'sd_extra.json', {'upscaler_2': dest_upscaler})

        if not bool(base_params):
            return None

        self.actions.write_json_file_with_base(
            'sd_extra.json', base_params)

        return dest_upscaler

    def r_hiresupscaler(self):
        return self.api.uitl_get_hires_upscaler_names()

    def w_hiresupsacler(self, dest_file: str, upscaler_name: str):

        upcalers_name_list = self.api.uitl_get_hires_upscaler_names()

        dest_upscaler = self.api.util_find_similar_str(
            upcalers_name_list, upscaler_name)

        base_params = self.actions.open_json_file_as_base(
            dest_file, {'hr_upscaler': dest_upscaler})

        self.actions.write_json_file_with_base(
            dest_file, base_params)

        return dest_upscaler

    def r_models(self) -> list:
        self.api.refresh_checkpoints()
        return self.api.util_get_model_names()

    def w_models(self, modelname: str) -> str:
        return self.api.util_set_model(modelname)

    def r_vae(self):
        try:
            return self.api.util_get_vae_names()
        except:
            return []

    def w_vae(self, vaename: str):

        return self.api.util_set_vae(vaename)
