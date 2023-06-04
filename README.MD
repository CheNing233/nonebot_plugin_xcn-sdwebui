# nonebot_plugin_xcn-sdwebui

![banner](/cache/download/example.png)

本插件基于nonebot2，支持QQ、飞书等平台的画图机器人，支持多SDWebUI的简单负载均衡

## Feature

### FullPlatform

第一期工程：

- [x] 使用简单FIFO队列进行负载均衡
- [x] `#sd`，查看当前所有服务器状态
- [x] `#sddraw`，接魔法进行画图
- [x] `#sdtxt`，修改文生图配置
- [x] `#sdimg`，修改图生图配置

第二期工程：

- [ ] `#sdext`，修改图片放大配置
- [ ] `#sdinf`，获取图片参数，`#sdinf -tagger`，调用tagger插件
- [ ] `#sdskip`或`#sdskip -all`，跳过
- [ ] `#sdfrev`，重载模型进行显存释放
- [ ] `#sdlora` ，获取Lora列表
- [ ] `#sdmodel` ，获取Models列表
- [ ] `#sdvae` ，获取VAE列表
- [ ] `#sdhrupscaler` ，获取Hires Upscaler列表
- [ ] `#sdexupscaler` ，获取Extra Upscaler列表

### only-QQ

- [x] `#sddraw`，回复图片可以进行图生图

### only-Feishu

- [x] `#sddraw`，完成画图有卡片显示参数

### Command Params

`#sddraw`、`sdtxt`、`#sdimg`、`#sdext`命令可接的参数，用于修改文生图或图生图等操作的参数

#### Example

支持“-”系列参数

```
#sddraw 1girl -cnt 6 -size 1024x768
```

上述指令将生成6张1024x768大小的二次元妹妹

支持“快速参数”

```
1girl,solo,line up,retro art,medium breasts,cleavage,x hair ornaments,bare thighs,thighs gap,miniskirt,T-shirt,
Negative prompt: mutated hands,too many fingers,fused fingers,bad anatomy,malformed limbs,extra limbs,missing legs,deformed legs,extra legs,more than 2 knee,missing toes,bad proportions,deformed,mutation,morbid,duplicate,mutilated,(worst quality:1.4), (low quality:1.4), (monochrome:1.1), easynegative, bad-artist-anime, bad-image-v2-39000, bad_prompt_version2, bad_quality, ng_deepnegative_v1_75t, verybadimagenegative_v1.1-6400, vile_prompt3, bad-hands-5,
Steps: 30, Sampler: Euler a, CFG scale: 7.0, Seed: 1097555186, Size: 1024x768, Model hash: 5df765eff2, Model: donutholemix_v10, Denoising strength: 0.58, Clip skip: 2, Hires upscale: 2.0, Hires upscaler: Latent, Version: v1.3.0
```

当然也可以混合使用

#### Achieve

基于`utils/param.py.ParameterOperation.txtimg_matcher`

你可以找到并修改它使其按照你的意愿进行参数的匹配

```python
patterns_dict = {
    "prompt": [r"(.*?)($|\n)"],
    "negative_prompt": [
        r"Negative prompt:(.*?)($|\n)", 
        r"-ngt(.*?)($|\n)"
    ],

    "steps": [
        r"Steps:(.*?)(,|$|\n)", 
        r"-steps(.*?)(,|$|\n)"
    ],
    "sampler_name": [
        r"Sampler:(.*?)(,|$|\n)", 
        r"-sampler(.*?)(,|$|\n)"
    ],
    "cfg_scale": [
        r"CFG scale:(.*?)(,|$|\n)", 
        r"-cfg(.*?)(,|$|\n)"
    ],
    "seed": [
        r"Seed:(.*?)(,|$|\n)", 
        r"-seed(.*?)(,|$|\n)"
    ],
    "width": [
        r"Size:(.*?)(,|$|\n)", 
        r"-size(.*?)(,|$|\n)"
    ],
    "height": [
        r"Size:(.*?)(,|$|\n)", 
        r"-size(.*?)(,|$|\n)"
    ],

    "n_iter": [r"-cnt(.*?)(,|$|\n)"],

    "enable_hr": [r"-hr(.*?)(,|$|\n)"],
    "denoising_strength": [
        r"Denoising strength:(.*?)(,|$|\n)",
        r"-ds(.*?)(,|$|\n)",
    ],
    "hr_scale": [
        r"Hires upscale:(.*?)(,|$|\n)", 
        r"-upscale(.*?)(,|$|\n)"
    ],
    "hr_upscaler": [
        r"Hires upscaler:(.*?)(,|$|\n)", 
        r"-upscaler(.*?)(,|$|\n)"
    ],
    "hr_second_pass_steps": [
        r"Hires steps:(.*?)(,|$|\n)",
        r"-hrsteps(.*?)(,|$|\n)",
    ],

    "sd_model_checkpoint": [
        r"Model:(.*?)(,|$|\n)", 
        r"-model(.*?)(,|$|\n)"
    ],
    "sd_vae": [r"-vae(.*?)(,|$|\n)"],
    "CLIP_stop_at_last_layers": [
        r"Clip skip:(.*?)(,|$|\n)",
        r"-clip(.*?)(,|$|\n)",
    ],
    "eta_noise_seed_delta": [
        r"ENSD:(.*?)(,|$|\n)", 
        r"-ensd(.*?)(,|$|\n)"
    ],
}
```

## Usage

1. 使用`git clone`克隆当前项目，并放到你的nonebot2机器人的`src/plugins`处
2. 在`pyproject.toml`或其他地方配置加载该插件
3. 修改`config/config_webui.json`中的`servers`字段，将你的SDWebUI填进去
4. 启动后使用`#sd`测试是否正常连接到所有SDWebUI