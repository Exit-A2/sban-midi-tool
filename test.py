import mido

mid = mido.MidiFile()
track = mido.MidiTrack()
for i in range(127):
    track.append(mido.Message("note_on", note=i, time=0))
    track.append(mido.Message("note_off", note=i, time=120))

mid.tracks.append(track)
mid.save("test.mid")
