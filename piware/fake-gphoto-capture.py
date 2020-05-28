import time
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print('Usage: fake-gphoto-capture.py DIRECTORY')
        sys.exit(1)

    FPS = 35.0
    delay = 1/FPS
    d = Path(sys.argv[1])
    n = len(list(d.glob('frame*.jpg')))
    fout = sys.stdout.buffer
    for i in range(n):
        fname = d / ('frame%d.jpg' % i)
        data = fname.read_bytes()
        fout.write(data)
        fout.flush()
        time.sleep(delay)


if __name__ == '__main__':
    main()
