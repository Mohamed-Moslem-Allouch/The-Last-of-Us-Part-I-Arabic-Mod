with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    exe = f.read()

pos = 0
while True:
    p = exe.find(b'text2-style', pos)
    if p == -1: break
    print('text2-style at', hex(p), exe[p-10:p+50])
    pos = p + 11
    if pos > 0x3000000: break
