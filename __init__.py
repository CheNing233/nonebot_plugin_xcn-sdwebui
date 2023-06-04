from nonebot.plugin import PluginMetadata

from pathlib import Path

from .route import Protocol_Router
from .config import Plugin_Config, WebUI_Config

from .webui.webui_manager import WebUI_Manager

__plugin_meta__ = PluginMetadata(
    name="XCN-WEBUI-PLUGIN",
    description="调用SDWebUIApi进行涩涩",
    usage=f"使用 井号help 获取帮助",
)
__all__ = ["XCN-WEBUI-PLUGIN", "__plugin_meta__"]

# 载入配置项
config_path = Path(__file__).parent.resolve() / "config"
plugin_cfg = Plugin_Config.parse_file(
    path=str(config_path / "config.json")
)
webui_cfg = WebUI_Config.parse_file(
    path=str(config_path / "config_webui.json")
)

# 创建webui控制器
webui_manager = WebUI_Manager(webui_cfg)

# 创建协议路由器
router = Protocol_Router(webui_manager)
