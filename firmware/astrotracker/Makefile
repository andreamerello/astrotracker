PROJECT = astrotracker
BUILD_DIR = bin

CFILES = main.c cdcacm.c tinyprintf.c motor.c
DEVICE=stm32f103c8t6


# You shouldn't have to edit anything below here.
#VPATH += $(SHARED_DIR)
#INCLUDES += $(patsubst %,-I%, . $(SHARED_DIR))
OPENCM3_DIR=../libopencm3

include $(OPENCM3_DIR)/mk/genlink-config.mk
include ../rules.mk
include $(OPENCM3_DIR)/mk/genlink-rules.mk
