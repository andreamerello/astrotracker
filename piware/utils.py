import subprocess
import datetime

def terminate(p, timeout=1):
    """
    Terminate gracefully the given process, or kill
    """
    print('Sending SIGTERM...')
    try:
        p.terminate()
        p.wait(timeout)
    except subprocess.TimeoutExpired:
        print('Timeout :(, killing the process')
        p.kill()
    else:
        print('Process successully terminated')

def now():
    return datetime.datetime.now().time()
