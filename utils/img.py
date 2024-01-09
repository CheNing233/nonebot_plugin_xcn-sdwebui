import base64
import io


class ImageOperation:
    @staticmethod
    def bytes_to_base64(image: bytes) -> str:
        """
        BASE64编码BYTES流图像
        """
        img_base64 = base64.b64encode(io.BytesIO(image).getvalue()).decode("utf-8")
        return img_base64

    @staticmethod
    def base64_to_bytes(image: str) -> bytes:
        """
        将 BASE64 编码的图像转换为字节流
        """
        # 将 Base64 字符串解码为字节数据
        image_bytes = base64.b64decode(image)

        # 创建 BytesIO 对象并将字节数据写入其中
        with io.BytesIO() as buffer:
            buffer.write(image_bytes)

            # 获取字节流数据
            bytes_data = buffer.getvalue()

        return bytes_data
