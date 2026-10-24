import struct,zlib
from pathlib import Path
for size in (192,512):
    rows=[]
    for y in range(size):
        row=bytearray()
        for x in range(size):
            u,v=x/size,y/size
            color=(20,46,53,255)
            if .25<u<.75 and .18<v<.8: color=(234,218,152,255)
            if .32<u<.72 and .32<v<.5: color=(24,62,75,255)
            if .55<u<.66 and .35<v<.43: color=(180,255,242,255)
            if .42<u<.58 and .72<v<.82: color=(20,46,53,255)
            row.extend(color)
        rows.append(b'\x00'+row)
    def chunk(kind,data): return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
    Path(f'public/pwa-{size}.png').write_bytes(png)
