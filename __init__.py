from pathlib import Path

import nonebot
from nonebot.plugin import PluginMetadata

from .process import Message_Processer
from .config import Plugin_Config

from .webui.webui_manager import WebUI_Manager

__plugin_meta__ = PluginMetadata(
    name="XCN-WEBUI-PLUGIN",
    description="调用SDWebUIApi进行涩涩",
    usage=f"使用 井号help 获取帮助",
)
__all__ = ["XCN-WEBUI-PLUGIN", "__plugin_meta__"]

# 载入配置项
global_cfg = nonebot.get_driver().config
plugin_cfg = Plugin_Config.parse_file(
    path=str(Path(__file__).parent.resolve() / "config" / "config.json")
)

# 创建webui控制器
webui_manager = WebUI_Manager(global_cfg, plugin_cfg)

# 创建消息处理器
message_processer = Message_Processer(webui_manager)
