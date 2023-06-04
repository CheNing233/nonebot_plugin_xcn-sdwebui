from typing import Any, Union
from time import time
import json


class CQCodeProcess():

    @staticmethod
    def strToCqCode(message: str) -> list[str]:
        """
        提取字符串中的 cqCode 字符串
        """
        msg = list(message)
        cq_code = ""
        cq_code_in = False
        cq_code_list = []
        for str in msg:
            if cq_code_in and str != "]":
                cq_code += str
                continue

            if cq_code_in and str == "]":
                cq_code += str
                cq_code_list.append(cq_code)
                cq_code = ""
                cq_code_in = False
                continue

            if str == "[":
                cq_code = ""
                cq_code += str
                continue

            if str == "C":
                cq_code += str
                continue

            if str == "Q":
                cq_code += str
                continue

            if str == ":" and cq_code == "[CQ":
                cq_code += str
                cq_code_in = True

        return cq_code_list

    def strToCqCodeToDict(message: str) -> list[dict[str, Union[str, dict[str, Any]]]]:
        """
        提取字符串中的 cqCode 字符串转换为字典
        """
        CqCodeList = []
        for item in CQCodeProcess.strToCqCode(message):
            CqCodeList.append(CQCodeProcess.get_cq_code(item))

        return CqCodeList

    def set_cq_code(code: dict[str, Any]) -> str:
        """
        转换 pycqBot 的 cqCode 字典为 cqCode 字符串
        """
        data_str = ""
        for key in code["data"].keys():
            data_str += ",%s=%s" % (key, code["data"][key])

        cqCode = "[CQ:%s%s]" % (code["type"], data_str)
        return cqCode

    def get_cq_code(code_str: str) -> dict[str, Union[str, dict[str, Any]]]:
        """
        转换 cqCode 字符串为字典
        """
        code_str = code_str.lstrip("[CQ:").rsplit("]")[0]
        code_list = code_str.split(",")

        cq_code: dict[str, Any] = {
            "type": code_list[0],
            "data": {

            }
        }

        if len(code_list) == 1:
            return cq_code

        for code_data in code_list[1:]:
            key_data = code_data.split("=")
            if len(key_data) != 2:
                key_data[1] = "=".join(key_data[1:])
            cq_code["data"][key_data[0]] = key_data[1]

        if cq_code["type"] == "json":
            cq_code["data"]["data"] = CQCodeProcess.cqJsonStrToDict(
                cq_code["data"]["data"])

        return cq_code

    def cqJsonStrToDict(cq_json_str: str) -> dict[str, Any]:
        """
        转换 cqCode 中的 json 字符串为字典
        """
        cq_json_str = cq_json_str.replace("&#44;", ",")
        cq_json_str = cq_json_str.replace("&amp;", "&")
        cq_json_str = cq_json_str.replace("&#91;", "[")
        cq_json_str = cq_json_str.replace("&#93;", "]")

        return json.loads(cq_json_str)

    def DictTocqJsonStr(dict: dict[str, Any]) -> str:
        """
        转换字典为 cqCode 中的 json 字符串
        """
        cq_json_str = json.dumps(
            dict, separators=(',', ':'), ensure_ascii=False)
        cq_json_str = cq_json_str.replace("&", "&amp;")
        cq_json_str = cq_json_str.replace(",", "&#44;")
        cq_json_str = cq_json_str.replace("[", "&#91;")
        cq_json_str = cq_json_str.replace("]", "&#93;")
        cq_json_str = cq_json_str.replace("'", '"')

        return cq_json_str
