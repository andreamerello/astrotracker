import sys
import time
import subprocess
import collections
from gphotocam import iter_mjpg
from utils import terminate

def main():
    cmd = ['gphoto2',
           #'--port', 'ptpip:192.168.1.180',
           '--set-config', 'output=TFT + PC',
           '--capture-movie',
           '--stdout'
    ]
    p = subprocess.Popen(cmd, bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out0 = p.stdout.read(1024)
    out1 = p.stdout.read(1024)
    if out1 == b'':
        # gphoto is not streaming anything, so it must be an error
        stderr = p.stderr.read()
        p.wait()
        print('ERROR')
        print(out0)
        print(stderr)
        return
    
    frame_times = collections.deque([time.time()], maxlen=25)
    try:
        for i, frame in enumerate(iter_mjpg(p.stdout, out0+out1)):
            frame_times.append(time.time())
            fps = len(frame_times) / (frame_times[-1] - frame_times[0])
            if i % 10 == 0:
                print('%.2f fps' % fps)
    finally:
        terminate(p)

if __name__ == '__main__':
    main()
