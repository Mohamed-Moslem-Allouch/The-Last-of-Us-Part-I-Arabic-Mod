with open('c:/Users/SlouMa/Desktop/tlou1/backup/tlou-i.exe', 'rb') as f:
    exe = f.read()

# Search for subtitle style, outline, shadow
for term in [b'subtitle', b'outline', b'stroke', b'shadow']:
    pos = 0
    while True:
        p = exe.find(term, pos)
        if p == -1: break
        # Check context
        ctx = exe[p-10:p+40]
        if any(b in ctx.lower() for b in [b'text', b'style', b'font', b'render', b'gui', b'color']):
            print(f'{term.decode()} at {hex(p)}: {ctx}')
        pos = p + len(term)
        if pos > 0x3000000: break
