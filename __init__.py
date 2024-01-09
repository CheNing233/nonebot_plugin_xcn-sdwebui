from nonebot.plugin import PluginMetadata
from nonebot.log import logger

import nonebot

from .sdapi.node import SDWebUI_Node
from .balance.direct import Direct_Balancer
from .process import Process

__plugin_meta__ = PluginMetadata(
    name="nonebot_plugin_xcn-sdapi",
    description="a sdapi plugin",
    usage="play sd picture",
    type="application",
    config=None,
    extra={},
)

global_cfg = nonebot.get_driver().config

sdapi_balancer = Direct_Balancer(SDWebUI_Node, logger)

main_proc = Process(sdapi_balancer)
