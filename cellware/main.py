#!/usr/bin/env python

import sys
import os

# https://github.com/kivy/kivy/issues/1600
# we force-enabled KIVY_GLES_LIMITS
# so that on linux the behavior is the same as on Android.
print 'Enabling KIVY_GLES_LIMITS'
os.environ['KIVY_GLES_LIMITS'] = '1'

# remove extra args from sys.argv, else kivy complains
extra_argv = []
for opt in ('--rotation', '--polar',):
    if opt in sys.argv:
        extra_argv.append(opt)
        sys.argv.remove(opt)

sys.path.append('libs')
from astro.app import main

if __name__ == '__main__':
    main(extra_argv)
