#!/bin/bash

# usage: deploy.sh [--all]

MODEL=`adb shell getprop ro.product.model`

case $MODEL in
    "SM-A405FN") echo "Device: Galaxy A40"; TARGET="/storage/emulated/0/kivy/cellware/";;
    *) echo "Unknown device"; TARGET="/sdcard/kivy/astro";;
esac

TMPDIR=/tmp/adbpush/astro
FILES=(android.txt
       main.py
       astro
       libs
       data
       *.png
       *.jpg
      )

rm -rf $TMPDIR
mkdir -p $TMPDIR

if [ x$1 = "x--all" ]
then
    # deploy everything -- slowish
    adb shell rm -rf $TARGET
    cp -L -r "${FILES[@]}" $TMPDIR
    cd $TMPDIR
    py.cleanup
    cd -
    adb push $TMPDIR $TARGET
else
    # deploy only astro -- faster
    cp -L -r astro $TMPDIR
    cd $TMPDIR
    py.cleanup
    cd -
    adb shell rm -rf $TARGET/astro
    adb push $TMPDIR/astro $TARGET
fi

adb logcat -c
adb logcat -s python
