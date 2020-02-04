#!/usr/bin/env python

import sys
import os

# https://github.com/kivy/kivy/issues/1600
# we force-enabled KIVY_GLES_LIMITS
# so that on linux the behavior is the same as on Android.
print 'Enabling KIVY_GLES_LIMITS'
os.environ['KIVY_GLES_LIMITS'] = '1'

sys.path.append('libs')
from astro.app import main

if __name__ == '__main__':
    main()
