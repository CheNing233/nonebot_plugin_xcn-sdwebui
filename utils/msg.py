class UniversalMessageBuilder:
    @staticmethod
    def server_info(
        qsize: int,
        ret_list: list[dict],
        ingnore: list[dict],
        vram_retname: str,
        prog_retname: str,
    ):
        final_str = "⏭ 待处理数量：%d" % (qsize)

        for server in ret_list:
            name = server["info"]["name"]
            host = str(server["info"]["host"]).replace(".", "·")
            port = server["info"]["port"]
            avalible = server["info"]["avalible"]
            select = server["info"]["select"].is_set()
            vram_free, vram_used, vram_total, vram_percent = server[vram_retname]
            jobcnt, eta, prog, step, steps = server[prog_retname]

            if select:
                selct = "🔵"
            else:
                selct = "⚪"

            if avalible:
                access = "🆗"
            else:
                access = "🆖"

            if jobcnt == 0:
                work = "🔁"
            else:
                work = "🔂"

            final_str += (
                f"\n{selct} {name}\n"
                f"{access} {host}:{port}\n"
                "%s %.2f s, %d/%d (%.2f%%)\n"
                "🎦 %.2f/%.2f GB (%.2f%%)"
                % (
                    work,
                    eta,
                    step,
                    steps,
                    prog,
                    vram_used,
                    vram_total,
                    vram_percent,
                )
            )

        for unvalible_server in ingnore:
            name = unvalible_server["name"]
            host = str(unvalible_server["host"]).replace(".", "·")
            port = unvalible_server["port"]
            avalible = unvalible_server["avalible"]
            select = unvalible_server["select"].is_set()

            if select:
                selct = "🔵"
            else:
                selct = "⚪"

            if avalible:
                access = "🆗"
            else:
                access = "🆖"

            final_str += f"\n{selct} {name}\n" f"{access} {host}:{port}"

        return final_str

    @staticmethod
    def tagger_info(target: dict) -> str:
        general: float = round(target["general"] * 100.0000, 2)
        sensitive: float = round(target["sensitive"] * 100.0000, 2)
        questionable: float = round(target["questionable"] * 100.0000, 2)
        explicit: float = round(target["explicit"] * 100.0000, 2)

        del target["general"]
        del target["sensitive"]
        del target["questionable"]
        del target["explicit"]

        curse = [word for word in target.keys()]

        final_str = (
            "❤ 涩涩鉴定：\n"
            "无害(general)：%.2f%%\n"
            "H(sensitive)：%.2f%%\n"
            "涩(questionable)：%.2f%%\n"
            "大咩(explicit)：%.2f%%\n"
        ) % (general, sensitive, questionable, explicit)

        final_str += ("🔠 求导结果为：\n%s") % (", ".join(curse))

        return final_str

    @staticmethod
    def key_value_show(target: dict, title: str = "", separator: str = ": "):
        final_str = title + "\n"
        for key, value in target.items():
            if key != "override_settings":
                final_str += "➡ %s%s%s\n" % (str(key), separator, str(value))

        if "override_settings" in target:
            for key, value in target["override_settings"].items():
                final_str += "➡ %s%s%s\n" % (str(key), separator, str(value))

        return final_str.strip()

    @staticmethod
    def value_show(target: list, title: str = ""):
        final_str = title + "\n"

        for value in target:
            try:
                final_str += "➡ %s\n" % (str(value))
            except:
                continue

        return final_str.strip()

    @staticmethod
    def value_show_withserver(
        target: list[dict], target_name: list[str], title: str = ""
    ):
        final_str = title + "\n"

        for server in target:
            name = server["info"]["name"]
            host = str(server["info"]["host"]).replace(".", "·")
            port = server["info"]["port"]
            select = server["info"]["select"].is_set()
            avalible = server["info"]["avalible"]

            if select:
                selct = "🔵"
            else:
                selct = "⚪"

            if avalible:
                access = "🆗"
            else:
                access = "🆖"

            final_str += f"{selct} {name}\n" + f"{access} {host}:{port}\n"

            for server in target:
                for items_todisplay in target_name:
                    for value in server[items_todisplay]:
                        try:
                            final_str += "➡ %s\n" % (str(value))
                        except:
                            continue

        return final_str.strip()
