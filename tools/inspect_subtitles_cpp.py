with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    f.seek(0x2e35600)
    print(f.read(1000))
