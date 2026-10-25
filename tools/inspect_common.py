import struct

with open('c:/Users/SlouMa/Desktop/tlou1/extracted/text2/eng.common', 'rb') as f:
    data = f.read()

count = struct.unpack('<I', data[:4])[0]
base = 4 + count * 16
records = [struct.unpack('<QQ', data[4+i*16 : 20+i*16]) for i in range(count)]
by_offset = sorted(records, key=lambda r: r[1])

print('Total records:', count)
print('First 10 records by offset in string block:')
for sid, off in by_offset[:10]:
    end = data.find(b'\x00', base + off)
    s = data[base+off:end].decode('utf-8', errors='replace')
    print(f'  off={off}: SID=0x{sid:x} text="{s}"')
