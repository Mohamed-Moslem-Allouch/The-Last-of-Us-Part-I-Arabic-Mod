import struct

for name in ['eng.subtitles', 'eng.subtitles-systemic']:
    path = f'c:/Users/SlouMa/Desktop/tlou1/extracted/text2/{name}'
    with open(path, 'rb') as f:
        data = f.read()
    count = struct.unpack('<I', data[:4])[0]
    base = 4 + count * 16
    print(f'{name}: count={count}, base=0x{base:x}, size={len(data)}')
    print('  first 20 bytes of string block:', data[base:base+20])
