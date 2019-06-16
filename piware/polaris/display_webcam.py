import cv2
from mycamera import MyCamera

def main():
    with MyCamera(1) as cam:
        while(True):
            frame = cam.read()
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Display the resulting frame
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

main()
