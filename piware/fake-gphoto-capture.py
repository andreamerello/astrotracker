import sys
import time
from gphotocam import iter_mjpg

FPS = 25.0

def main():
    if len(sys.argv) != 2:
        print('Usage: fake-gphoto-capture.py VIDEOFILE')
        sys.exit(1)
    filename = sys.argv[1]
    fout = sys.stdout.buffer
    with open(filename, 'rb') as f:
        for frame in iter_mjpg(f):
            fout.write(frame)
            fout.flush()
            time.sleep(1/FPS)

if __name__ == '__main__':
    main()
