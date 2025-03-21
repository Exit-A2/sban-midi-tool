import mido

mid = mido.MidiFile("C:\\Users\\shake\\Desktop\\untitled.mid")
for track in mid.tracks:
    print(track)
