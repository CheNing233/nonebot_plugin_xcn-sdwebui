

class UniversalMessageBuilder:

    @staticmethod
    def server_info(
        qsize: int, gpu: list[tuple], progress: list[tuple]
    ):
        final_str = "待处理数量：%d" % (qsize)
        for i in range(len(gpu)):
            for j in range(len(progress)):
                host1, port1, vram_free, vram_used, vram_total, vram_percent = gpu[i]
                host2, port2, jobcnt, eta, prog, step, steps = progress[j]

                if host1 == host2 and port1 == port2:

                    if jobcnt == 0:
                        work = "🆗"
                    else:
                        work = "🔂"

                    final_str += \
                        "\n[%s%s:%d]\n"\
                        "任务 %.2f s, %d/%d (%.2f%%)\n"\
                        "显存 %.2f/%.2f GB (%.2f%%)"\
                        % (
                            work, str(host1).replace('.', '·'), port2,
                            eta, step, steps, prog,
                            vram_used, vram_total, vram_percent
                        )

        return final_str

    @staticmethod
    def params_show(target: dict, title: str = '', separator: str = ': '):

        final_str = title + '\n'
        for key, value in target.items():
            if key != 'override_settings':
                final_str += (
                    "♥ %s%s%s\n" % (str(key), separator, str(value))
                )

        if 'override_settings' in target:
            for key, value in target['override_settings'].items():
                final_str += (
                    "♥ %s%s%s\n" % (str(key), separator, str(value))
                )

        return final_str.strip()
