with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    exe = f.read()

# Search for font names in subtitle code
pos = 0
while True:
    p = exe.find(b'Subtitles::', pos)
    if p == -1: break
    print('Found Subtitles:: at', hex(p), exe[p:p+60])
    pos = p + 11
