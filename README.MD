# nonebot_plugin_xcn-sdwebui

![banner](example.png)

本插件基于nonebot2，支持QQ、飞书等平台的画图机器人，支持多SDWebUI的简单负载均衡

## Feature

### 已实现功能

- [x] 简单的优先级任务队列和负载均衡（不稳定）

- [x] `#sd`，查看当前所有服务器状态
- [x] `#sd -h`，其他子命令可以使用`-h`查看提示

- [x] `#sddraw`，接提示词进行`txt2img`，回复图片可以进行`img2img`
- [x] `#sdextra`，图片放大

- [x] `#sdtxt`，修改`txt2img`配置
- [x] `#sdimg`，修改`img2img`配置
- [x] `#sdext`，修改图片放大配置
- [x] `#sdtagger`，修改tagger反推插件配置

- [x] `#sdinf`，获取图片参数，`#sdinf -tagger`，额外调用tagger插件反推（自动卸载反推模型）

- [x] `#sdskip`，选中的服务器全部跳过一张，`#sdskip -all`，停止并清空所有任务
- [x] `#sdfrev`，重载模型进行显存释放，`#sdfrev -all`，全部进行重载模型

- [x] `#sdlst -model -vae -hires ...`，获取可用的列表（比如获取可用的model和sampler等）
- [x] `#sdlst -h`，更多选项可以使用`-h`查看提示


### 待实现功能

- [ ] 适配Telegram
- [ ] 改善稳定性
- [ ] 改善多服务器操作

### 关于魔法

`#sddraw`、`#sdtxt`、`#sdimg`、`#sdext`等命令可接的参数，用于修改文生图或图生图等操作的参数

#### 例子

支持“-”系列参数

```
#sddraw 1girl -cnt 6 -size 1024x768
```

上述指令将生成6张1024x768大小的二次元妹妹

支持“快速参数”（通常都是复制粘贴过来，非常方便）

```
1girl,solo,line up,retro art,medium breasts,cleavage,x hair ornaments,bare thighs,thighs gap,miniskirt,T-shirt,
Negative prompt: mutated hands,too many fingers,fused fingers,bad anatomy,malformed limbs,extra limbs,missing legs,deformed legs,extra legs,more than 2 knee,missing toes,bad proportions,deformed,mutation,morbid,duplicate,mutilated,(worst quality:1.4), (low quality:1.4), (monochrome:1.1), easynegative, bad-artist-anime, bad-image-v2-39000, bad_prompt_version2, bad_quality, ng_deepnegative_v1_75t, verybadimagenegative_v1.1-6400, vile_prompt3, bad-hands-5,
Steps: 30, Sampler: Euler a, CFG scale: 7.0, Seed: 1097555186, Size: 1024x768, Model hash: 5df765eff2, Model: donutholemix_v10, Denoising strength: 0.58, Clip skip: 2, Hires upscale: 2.0, Hires upscaler: Latent, Version: v1.3.0
```

当然也可以混合使用

#### 实现

基于`utils/param.py.ParameterOperation.txtimg_matcher`

你可以找到并修改它使其按照你的意愿进行参数的匹配

单击[此处跳转到匹配模式表](#magic-matcher-rules)

## Usage

### 配置插件

- 使用`git clone`克隆当前项目，并放到你的nonebot2机器人的`src/plugins`处
- 配置好`pyproject.toml`和`env.*`，配置好飞书账号

### 安装依赖

```bash
# 可能你需要启动你机器人的虚拟环境才能安装
. ./venv/bin/activate

# 使用环境内pip安装依赖
pip install requests requests_toolbelt tabulate aiohttp
```

如果你的飞书适配器插件过旧，可能还需要进行更新

### 启动、测试及修改服务器

- 启动成功后，输入`#sd -h`查看帮助，若有输出则插件启动成功
- 使用`#sd add -name 名字 -host xxx.xxx.xxx.xxx`添加第一个服务器
- 使用`#sd -delete 名字`删除对应名字的服务器
- 使用`#sd`查看所有服务器状态
- 可以开心画画了

## Problems and Defects

1. 仅适配了QQ与飞书，Telegram以后再行适配
2. 飞书需要自己注册并开放各种东西，有可能还要内网穿透，详见飞书文档以及nonebot2的飞书适配器文档
3. 文生图时建议在Webui网页里把`表格`相关的选项全部关了，否则上传网格图片可能因图片过大上传失败

## Magic matcher rules

以下是所有魔法的匹配规则，使用正则表达式，例如调整迭代步数：

`#sddraw -steps 28`，`#sdtxt -steps 28`，`#sdimg -steps 28`等等

你都可以在下面找到相应的匹配方法

```python
txt_or_img = {
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

extra = {
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

tagger = {
    "model": [r"-model(.*?)(,|$|\n)"],
    "threshold": [r"-threshold(.*?)(,|$|\n)"],
}
```