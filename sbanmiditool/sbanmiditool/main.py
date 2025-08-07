import mido
import re
from PIL import Image, ImageDraw
import math
from pathlib import Path
from datetime import datetime
import copy


class SBANMidi:
    def _clean(self):
        self.track = sorted(self.track, key=lambda x: x["start"])
        if self.track:
            self.max_stop = max([msg["stop"] for msg in self.track])
        else:
            self.max_stop = 0

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

    def _draw_messages(self, messages: list[dict], width, ticks_per_dot):
        im = Image.new("RGBA", (width, 128), (0, 0, 0, 100))
        draw = ImageDraw.Draw(im)
        for msg in messages:
            x1 = math.floor(msg["start"] / ticks_per_dot)
            x2 = math.floor(msg["stop"] / ticks_per_dot) - 1
            y = 127 - msg["note"]

            if x2 < x1:
                x2 = x1

            draw.rectangle(xy=(x1, y, x2, y), fill=(255, 255, 255))

        return im

    def save(self, path: str):
        """MIDIファイルとして保存する。

        Args:
            path (str): 出力するMIDIファイルのパス
        """
        self._mido().save(path)

    def to_morse(self, time: int = 120) -> str:
        """SBANMidiをモールス信号に変換(つまり解読)

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

    def to_image(self, path: str, ticks_per_dot: int = 80, progress: str = "none"):
        """SBANMidiを画像に変換して出力する。

        ファイル名は日付になる。

        Args:
            path (str): 出力するフォルダのパス
            ticks_per_dot (int): 1ドットあたりのティック数
            progress (str): noneの場合結果の画像のみ、lineの場合経過画像、pointの場合ヤツメ式の経過画像
        """

        im_length = int(max([x["stop"] for x in self.track]) / ticks_per_dot)
        im = Image.new("RGBA", (im_length, 128))
        draw = ImageDraw.Draw(im)

        today = str(datetime.date(datetime.today()))

        directory = Path(path)
        if not directory.is_dir():  # pathがディレクトリでは無かった場合
            raise ValueError

        if progress == "none":
            for msg in self.track:
                x1 = math.floor(msg["start"] / ticks_per_dot)
                x2 = math.floor(msg["stop"] / ticks_per_dot) - 1
                y = 127 - msg["note"]

                if x2 < x1:
                    x2 = x1

                draw.rectangle(xy=(x1, y, x2, y), fill=(255, 255, 255))

            im.save(str(directory / f"{today}.png"))

        elif progress == "line" or progress == "point":
            time = 0
            pre_msgs = {}
            file_num = 0

            for time in range(self.max_stop + 1):
                current_msgs = [
                    msg for msg in self.track if msg["start"] <= time < msg["stop"]
                ]
                current_notes = {msg["note"] for msg in current_msgs}
                current_starts = {msg["start"] for msg in current_msgs}
                current_stops = {msg["stop"] for msg in current_msgs}
                pre_notes = {msg["note"] for msg in pre_msgs}
                pre_starts = {msg["start"] for msg in pre_msgs}
                pre_stops = {msg["stop"] for msg in pre_msgs}

                if (
                    not (
                        current_notes == pre_notes
                        and current_starts == pre_starts
                        and current_stops == pre_stops
                    )
                    and current_notes
                ):  # なっている音が前と違い、かつ1つ以上音が鳴っている
                    if progress == "line":
                        target_msgs = [
                            msg for msg in self.track if msg["start"] <= time
                        ]
                    elif progress == "point":
                        target_msgs = copy.deepcopy(current_msgs)
                    now_im = self._draw_messages(target_msgs, im_length, ticks_per_dot)
                    now_im.save(str(directory / f"{today}-{file_num}.png"))
                    file_num += 1

                pre_msgs = copy.deepcopy(current_msgs)

    def to_gif(self, path: str, ticks_per_dot: int = 80, progress: str = "point"):
        """SBAMidiをGIFに変換して出力する。

        100BPM固定。

        Args:
            path(str):出力するGIFのパス
            progress(str):lineの場合経過画像、pointの場合ヤツメ式の経過画像
        """

        im_length = int(max([x["stop"] for x in self.track]) / ticks_per_dot)
        time = 0
        images = []

        while time < self.max_stop:
            if progress == "point":
                target_msgs = [
                    msg for msg in self.track if msg["start"] <= time < msg["stop"]
                ]
            elif progress == "line":
                target_msgs = [msg for msg in self.track if msg["start"] <= time]

            images.append(self._draw_messages(target_msgs, im_length, ticks_per_dot))

            time += ticks_per_dot

        if 2 <= len(images):
            SECOND_PER_BEAT = 600  # 100BPMのとき1拍あたりのミリ秒数
            duration = SECOND_PER_BEAT / (480 / ticks_per_dot)

            images[0].save(
                path, duration=duration, save_all=True, append_images=images[1:]
            )

    def reverse(self):
        """MIDIを破壊的に反転する。"""

        max_stop = max([msg["stop"] for msg in self.track])
        for msg in self.track:
            pre_start = msg["start"]
            pre_stop = msg["stop"]

            msg["start"] = max_stop - pre_stop
            msg["stop"] = max_stop - pre_start

        self._clean()

    def __str__(self):
        return str(self.track)


def from_number(numbers: str, time: int = 120) -> SBANMidi:
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


def from_morse(
    morse: str,
    time: int = 120,
    dit: tuple = (".", "・"),
    dah: tuple = ("-", "_", "ー"),
    space: tuple = (" ", "　"),
) -> SBANMidi:
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
            midi.track.append({"start": current, "stop": current + time, "note": 60})
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


def from_tenji(tenji: str, time: int = 120) -> "SBANMidi":
    """点字テキストをSBANMidiに変換する。

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
            midi.track.append({"start": current, "stop": current + time, "note": 62})
        if x[4] == "1":
            midi.track.append({"start": current, "stop": current + time, "note": 61})
        if x[3] == "1":
            midi.track.append({"start": current, "stop": current + time, "note": 60})
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
