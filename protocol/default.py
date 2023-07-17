from nonebot.adapters import Bot, Event, Message, MessageSegment


class Default_Protocol:
    @staticmethod
    async def send_str(bot: Bot, event: Event, args: tuple):
        target = "出错喵！"
        preprocess_func = None
        preprocess_params = None
        for i in range(len(args)):
            if i == 0:
                target = args[i]
            elif i == 1:
                preprocess_func = args[i]
            elif i == 2:
                preprocess_params = args[i]

        if preprocess_func:
            if preprocess_params:
                target = preprocess_func(target, preprocess_params)
            else:
                target = preprocess_func(target)

        await bot.send(event, target)

    @staticmethod
    async def send_img(bot: Bot, event: Event, args):
        ...

    @staticmethod
    async def get_img_reply(bot: Bot, event: Event):
        ...
