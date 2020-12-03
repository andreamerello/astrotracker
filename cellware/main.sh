#!/bin/bash

LG_LEON="--size=854x480 --dpi=220"
BIG="--size=1708x960 --dpi=220"
HUAWEI_P9="--size=1920x1080 --dpi=480"

#SCREEN=${BIG}
SCREEN=${HUAWEI_P9}
export KIVY_METRICS_DENSITY=3 # for HUAWEI_P9

python main.py ${SCREEN} "$@"

