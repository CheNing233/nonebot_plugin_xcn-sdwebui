import difflib
import datetime


class TextOptimization:
    @staticmethod
    def find_similar_str(str_list: list[str], sub_str: str):
        max_similar_ratio = 0
        most_similar_str = ""

        for str_single in str_list:
            similarity_ratio = difflib.SequenceMatcher(
                None, str_single.lower(), sub_str.lower()
            ).ratio()

            if similarity_ratio > max_similar_ratio:
                max_similar_ratio = similarity_ratio
                most_similar_str = str_single

        return most_similar_str

    @staticmethod
    def generate_timestamp_file_name() -> str:
        """
        yield function
        """
        # 定义开始日期时间戳
        start_date = datetime.datetime(2023, 3, 12)

        # 获取当前日期时间戳
        now_date = datetime.datetime.now()

        # 计算时间差并转换为秒数
        time_difference = now_date - start_date
        timestamp = int(time_difference.total_seconds())

        while True:
            i = 0
            yield str(timestamp) + str(i)
            i += 1
