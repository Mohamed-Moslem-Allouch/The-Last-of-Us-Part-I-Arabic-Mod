from fontTools.ttLib import TTFont

f = TTFont('c:/Users/SlouMa/Desktop/tlou1/extracted/fonts/DINPro-Regular.otf')
cs = f['CFF '].cff.topDictIndex[0].CharStrings

for name in ['V', 'v', 'W', 'w', 'y', 'z', 'j', 'comma', 'parenright', 'two', 'six']:
    if name in cs:
        cs[name].decompile()
        print(f'{name}: {cs[name].program}')
