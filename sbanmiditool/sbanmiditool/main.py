import mido
import re
from PIL import Image, ImageDraw
import math
from pathlib import Path
from datetime import datetime
import copy


def _lists_match(l1, l2):
    if len(l1) != len(l2):
        return False
    return all(x == y and type(x) == type(y) for x, y in zip(l1, l2))


class SBANMidi:
    def _clean(self):
        self.track = sorted(self.track, key=lambda x: x["start"])
        self.max_stop = max([msg["stop"] for msg in self.track])

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

            for track in mid.tracks:
                for msg in track:
                    time += msg.time * tpb_rate

                    if msg.type == "note_off" or (
                        msg.type == "note_on" and msg.velocity == 0
                    ):
                        target = None
                        for i, msg2 in enumerate(self.track):
                            if msg2["note"] == msg.note and not ("stop" in msg2):
                                target = i
                        self.track[target]["stop"] = time
                    elif msg.type == "note_on":
                        self.track.append({"start": time, "note": msg.note})
        elif object is None:
            pass

        self._clean()

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

        midi._clean()

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

        midi._clean()

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

        midi._clean()

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

        today = str(datetime.date(datetime.today()))

        directory = Path(path)
        if not directory.is_dir():
            raise ValueError

        if mode == 0:
            for msg in self.track:
                x1 = math.floor(msg["start"] / ticks_per_dot)
                x2 = math.floor(msg["stop"] / ticks_per_dot) - 1
                y = 127 - msg["note"]

                if x2 < x1:
                    x2 = x1

                draw.rectangle(xy=(x1, y, x2, y), fill=(255, 255, 255))
        elif mode == 1 or mode == 2:
            time = 0
            max_stop = max([msg["stop"] for msg in self.track])
            pre_msgs = []

            for time in range(len(max_stop) + 1):
                current_msgs = [
                    msg for msg in self.track if msg["start"] <= time < msg["stop"]
                ]

                if not _lists_match(pre_msgs, current_msgs):
                    pass  # あとでかく

                pre_msgs = copy.deepcopy(current_msgs)

        im.save(str(directory / f"{today}.png"))

    def reverse(self):
        """MIDIを破壊的に反転します"""

        max_stop = max([msg["stop"] for msg in self.track])
        for msg in self.track:
            pre_start = msg["start"]
            pre_stop = msg["stop"]

            msg["start"] = max_stop - pre_stop
            msg["stop"] = max_stop - pre_start

        self._clean()

    def __str__(self):
        return str(self.track)


if __name__ == "__main__":
    mid = SBANMidi("C:\\Users\\shake\\Desktop\\untitled.mid")

    print(mid)

    mid.to_image("", 20, 1)
