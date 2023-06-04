import difflib


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
