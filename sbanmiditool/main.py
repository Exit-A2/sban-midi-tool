import mido


class SBANMidi:
    def __init__(self, object=None):
        self.track = []
        if type(object) == mido.MidiFile:
            time = 0
            for track in object.tracks:
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
        elif type(object) == SBANMorse:
            pass
        elif object is None:
            pass

    def mido(self):
        mid = mido.MidiFile()

    @classmethod
    def from_morse(morse: "SBANMorse", time):
        midi = SBANMidi()
        for x in list(morse.text):
            x


class SBANMorse:
    def __init__(self, text, dit, dah, space):
        self.text = ""
        for x in list(text):
            if x in dit:
                self.text += "."
            elif x in dah:
                self.text += "-"
            elif x in space:
                self.text += " "


print(SBANMidi(mido.MidiFile("C:\\Users\\shake\\Desktop\\untitled.mid")).track)
