a = []
for i in range(64):
    a.append(bytes.fromhex(hex(14852224 + i)[2:]).decode("utf-8"))
print("".join(a))
