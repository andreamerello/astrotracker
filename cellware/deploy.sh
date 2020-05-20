#!/bin/bash

# usage: deploy.sh [--all]

TMPDIR=/tmp/adbpush/astro
FILES=(android.txt
       main.py
       astro
       libs
       data
       *.png
      )

rm -rf $TMPDIR
mkdir -p $TMPDIR

if [ x$1 = "x--all" ]
then
    # deploy everything -- slowish
    adb shell rm -rf /sdcard/kivy/astro
    cp -L -r "${FILES[@]}" $TMPDIR
    cd $TMPDIR
    py.cleanup
    cd -
    adb push $TMPDIR /sdcard/kivy/astro
else
    # deploy only astro -- faster
    cp -L -r astro $TMPDIR
    cd $TMPDIR
    py.cleanup
    cd -
    adb shell rm -rf /sdcard/kivy/astro/astro
    adb push $TMPDIR/astro /sdcard/kivy/astro
fi

adb logcat -c
adb logcat -s python
