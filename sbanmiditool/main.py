import mido
import re


class SBANMidi:
    def __init__(self, object=None):
        self.track = []
        if type(object) == str:
            mid = mido.MidiFile(object)

            time = 0
            for track in mid.tracks:
                for msg in track:
                    time += msg.time
                    if msg.type == "note_on":
                        self.track.append({"start": time, "note": msg.note})
                    if msg.type == "note_off":
                        target = 0
                        for i, msg2 in enumerate(self.track):
                            if (
                                msg2["note"] == msg.note
                                and self.track[target]["start"] < msg2["start"]
                            ):
                                target = i
                        self.track[target]["stop"] = msg.time
        elif object is None:
            pass

    def _mido(self) -> mido.MidiFile:
        mid = mido.MidiFile()
        track = mido.MidiTrack()

        on = []
        time = 0
        for i, msg in enumerate(self.track):
            on = sorted(on, key=lambda x: x["stop"])
            new_on = on.copy()

            for x in new_on:
                print(x["stop"] - time)
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
        print(on)

        mid.tracks.append(track)

        return mid

    def save(self, path):
        self._mido().save(path)

    @staticmethod
    def from_number(numbers: str, time: int = 120):
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

        return midi

    @staticmethod
    def from_morse(
        morse: str,
        time: int = 120,
        dit: tuple = (".", "・"),
        dah: tuple = ("-", "_", "ー"),
        space: tuple = (" ", "　"),
    ):
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

        return midi

    @staticmethod
    def from_tenji(tenji: str, time: int = 120):
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

        return midi

    def __str__(self):
        return str(self.track)


if __name__ == "__main__":
    mid = SBANMidi.from_tenji(
        "⠧⠞⠓⠁⠙⠣⠳⠹⠐⠣⠟⠳⠵⠝⠕⠜⠉⠐⠕⠄⠕⠳⠐⠡⠃⠩⠑⠮⠴⠞⠉⠎⠺⠞⠖⠃⠟⠟⠾⠾⠉⠐⠗⠛⠾⠳⠶⠐⠳⠟⠹⠛⠇⠃⠎⠐⠗⠚⠉⠱⠚⠶⠐⠻"
    )._mido()

    mid.save("export.mid")
