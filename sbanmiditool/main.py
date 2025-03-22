import mido
import re
from PIL import Image, ImageDraw
import math
from pathlib import Path
from datetime import datetime


def _sorted_by_start(track: list[dict]):
    return sorted(track, key=lambda x: x["start"])


class SBANMidi:
    def __init__(self, path: str | None = None):
        """このパッケージ用のMIDIオブジェクト。

        通常のMIDIでは「ノートの始まり」や「ノートの終わり」を1メッセージとするが、
        このオブジェクトではノートを1メッセージとする。
        また、テンポやトラック名などの細かい機能を廃止している。

        Attributes:
            path (str or None):MIDIファイルのパス
        """

        self.track = []
        if type(path) == str:
            mid = mido.MidiFile(path)

            time = 0
            tpb_rate = int(
                480 / mid.ticks_per_beat
            )  # ticks_per_beatが480以外だった時の倍率
            print(tpb_rate)

            for track in mid.tracks:
                for msg in track:
                    time += msg.time * tpb_rate

                    if msg.type == "note_off" or (
                        msg.type == "note_on" and msg.velocity == 0
                    ):
                        target = 0
                        for i, msg2 in enumerate(self.track):
                            if (
                                msg2["note"] == msg.note
                                and self.track[target]["start"] < msg2["start"]
                            ):
                                target = i
                        self.track[target]["stop"] = time
                    elif msg.type == "note_on":
                        self.track.append({"start": time, "note": msg.note})
        elif object is None:
            pass

        self.track = _sorted_by_start(self.track)

    def _mido(self) -> mido.MidiFile:
        mid = mido.MidiFile()
        track = mido.MidiTrack()

        on = []
        time = 0
        for i, msg in enumerate(self.track):
            on = sorted(on, key=lambda x: x["stop"])
            new_on = on.copy()

            for x in new_on:
                if time <= x["stop"] <= msg["start"]:
                    track.append(
                        mido.Message("note_off", note=x["note"], time=x["stop"] - time)
                    )
                    time = x["stop"]
                    on.remove(x)

            track.append(
                mido.Message("note_on", note=msg["note"], time=msg["start"] - time)
            )
            on.append(msg)
            time = msg["start"]

        new_on = on.copy()
        for x in new_on:
            track.append(
                mido.Message("note_off", note=x["note"], time=x["stop"] - time)
            )
            time = x["stop"]
            on.remove(x)

        mid.tracks.append(track)

        return mid

    def save(self, path: str):
        """MIDIファイルとして保存する。

        Args:
            path (str): 出力するMIDIファイルのパス
        """
        self._mido().save(path)

    @staticmethod
    def from_number(numbers: str, time: int = 120) -> "SBANMidi":
        """数字をSBANMidiに変換する。

        Args:
            numbers (str): 36進数までの数字
            time (int): 1音の長さ

        Returns:
            SBANMidi
        """

        midi = SBANMidi()
        current = 0
        print(list(numbers))

        for x in list(numbers):
            if x.isdecimal():
                midi.track.append(
                    {"start": current, "stop": current + time, "note": int(x)}
                )
                current += time
            elif x.isascii() and x.isalpha():
                midi.track.append(
                    {
                        "start": current,
                        "stop": current + time,
                        "note": ord(x.upper()) - 55 + 60,
                    }
                )
                current += time

        midi.track = _sorted_by_start(midi.track)

        return midi

    @staticmethod
    def from_morse(
        morse: str,
        time: int = 120,
        dit: tuple = (".", "・"),
        dah: tuple = ("-", "_", "ー"),
        space: tuple = (" ", "　"),
    ) -> "SBANMidi":
        """モールス文をSBANMidiに変換する。

        Args:
            morse (str): モールス信号のテキスト
            time (int): 点あたりのノートの長さ
            dit (tuple): 点にあたる文字のタプル
            dah (tuple): 線にあたる文字のタプル
            space (tuple): スペースにあたる文字のタプル

        Returns:
            SBANMidi
        """

        midi = SBANMidi()
        current = 0
        for x in list(morse):
            if x in dit:
                midi.track.append(
                    {"start": current, "stop": current + time, "note": 60}
                )
                current += time
            elif x in dah:
                midi.track.append(
                    {"start": current, "stop": current + time * 2, "note": 60}
                )
                current += time * 2
            elif x in space:
                current += time

        midi.track = _sorted_by_start(midi.track)

        return midi

    @staticmethod
    def from_tenji(tenji: str, time: int = 120) -> "SBANMidi":
        """点字テキストをSBANMidiに変換

        Args:
            tenji (str): 点字のテキスト(漢点字には未対応)
            time (int): 1音の長さ

        Returns:
            SBANMidi
        """

        midi = SBANMidi()

        pattern = re.compile(r"[⠀-⠿]")
        valid_tenji = [x for x in list(tenji) if pattern.match(x)]

        tenji_num = [int(x.encode("utf-8").hex(), 16) - 14852224 for x in valid_tenji]

        bin_tenji = [bin(x)[2:].zfill(6) for x in tenji_num]

        current = 0
        for x in bin_tenji:
            if x[5] == "1":
                midi.track.append(
                    {"start": current, "stop": current + time, "note": 62}
                )
            if x[4] == "1":
                midi.track.append(
                    {"start": current, "stop": current + time, "note": 61}
                )
            if x[3] == "1":
                midi.track.append(
                    {"start": current, "stop": current + time, "note": 60}
                )
            if x[2] == "1":
                midi.track.append(
                    {"start": current + time, "stop": current + time * 2, "note": 62}
                )
            if x[1] == "1":
                midi.track.append(
                    {"start": current + time, "stop": current + time * 2, "note": 61}
                )
            if x[0] == "1":
                midi.track.append(
                    {"start": current + time, "stop": current + time * 2, "note": 60}
                )

            current += time * 2

        midi.track = _sorted_by_start(midi.track)

        return midi

    def to_morse(self, time: int = 120) -> str:
        """SBANMidiをモールス信号に変換

        Args:
            time (int): 基準になる長さ(これより長いノートは線、そうでないノートは点、これより長い空白はスペースになる)

        Returns:
            str: "."、"-"、" "で表されたモールス文
        """

        result = ""

        pre_stop = 0
        for msg in self.track:
            if (msg["start"] - pre_stop) >= time:
                result += " "

            if (msg["stop"] - msg["start"]) > time:
                result += "-"
            else:
                result += "."
            pre_stop = msg["stop"]

        return result

    def to_image(self, path: str, ticks_per_dot: int = 80, mode: int = 0):
        """SBANMidiを画像に変換して出力する。

        ファイル名は日付になる。

        Args:
            path (str): 出力するフォルダのパス
            ticks_per_dot (int): 1ドットあたりのティック数
            mode (int): 0の場合結果の画像のみ、1の場合経過画像、2の場合ヤツメ式の経過画像
        """

        im_length = int(max([x["stop"] for x in self.track]) / ticks_per_dot)
        im = Image.new("RGBA", (im_length, 128))
        draw = ImageDraw.Draw(im)

        today = datetime.today()

        directory = Path(path)
        if not directory.is_dir():
            raise ValueError

        index = 0
        for msg in self.track:
            if mode == 2:
                im2 = Image.new("RGBA", (im_length, 128))
                draw2 = ImageDraw.Draw(im2)

            x1 = math.floor(msg["start"] / ticks_per_dot)
            x2 = math.floor(msg["stop"] / ticks_per_dot)
            y = 127 - msg["note"]
            draw.rectangle(xy=(x1, y, x2, y), fill=(255, 255, 255))

            if mode == 1:
                im.save(str(directory / f"{today}-{index}.png"))
            elif mode == 2:
                draw2.rectangle(xy=(x1, y, x2, y), fill=(255, 255, 255))
                im2.save(str(directory / f"{today}-{index}.png"))
            index += 1

        im.save(str(directory / f"{today}.png"))

    def __str__(self):
        return str(self.track)


if __name__ == "__main__":
    mid = SBANMidi("C:\\Users\\shake\\Desktop\\untitled.mid")

    print(mid)
    print(mid.to_morse(120))
