import time
from flask import Flask, Response
from star_camera import StarCamera
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


def gen_frames_from_jpgs():
    print('Reading jpgs...')
    for i in range(1, 6529):
        with open('/home/pi/frames/out%d.jpg' % i, 'rb') as f:
            frame = f.read()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'Content-Length: %d\r\n'
               b'\r\n'
               b'%s\r\n') % (len(frame), frame)
        time.sleep(0.3)


@app.route('/camera/<speed>/')
def camera(speed):
    speed = float(speed)
    def gen_frames():
        try:
            print('Starting camera...')
            cam = StarCamera(speed)
            for frame in cam.read_frames():
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: %d\r\n'
                       b'\r\n'
                       b'%s\r\n') % (len(frame), frame)
        finally:
            print('Closing camera...')

    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    app.run(host='0.0.0.0', debug=True)
