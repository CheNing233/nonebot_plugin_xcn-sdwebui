import datetime
import base64
import io

from pathlib import Path
from PIL import Image, PngImagePlugin


class PILImageOperation:

    @staticmethod
    def base_path(use_Path: bool = False):
        if use_Path:
            return Path(__file__).parent.parent.resolve() / "cache" / "download"
        else:
            return str(Path(__file__).parent.parent.resolve() / "cache" / "download")

    @staticmethod
    def save_imgs(imgs: list, info: dict):
        path = list()

        for i in range(len(imgs)):

            # 加入图片参数
            pnginfo = PngImagePlugin.PngInfo()
            pnginfo.add_text("parameters", str(info['infotexts'][i]))

            # 定义开始日期时间戳
            start_date = datetime.datetime(2023, 3, 12)

            # 获取当前日期时间戳
            now_date = datetime.datetime.now()

            # 计算时间差并转换为秒数
            time_difference = now_date - start_date
            timestamp = int(time_difference.total_seconds())

            imgs[i].save(
                str(PILImageOperation.base_path(use_Path=True) /
                    (str(timestamp) + str(i) + '.png')
                    ),
                pnginfo=pnginfo
            )

            path.append(
                str(PILImageOperation.base_path(use_Path=True) /
                    (str(timestamp) + str(i) + '.png')
                    )
            )

        return path

    @staticmethod
    def b64_img(image: Image, head: str = 'data:image/png;base64,'):
        """
        BASE64编码PIL图像（data:image/png;base64,）
        """
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")

        img_base64 = head + \
            str(base64.b64encode(buffered.getvalue()), 'utf-8')
        return img_base64

    @staticmethod
    def b64_bytes(image: bytes):
        """
        BASE64编码BYTES流图像
        """
        img_base64 = base64.b64encode(
            io.BytesIO(image).getvalue()).decode('utf-8')
        return img_base64
