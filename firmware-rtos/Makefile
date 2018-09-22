######################################################################
#  Top Level: STM32F103C8T6 Projects
######################################################################

.PHONY = libopencm3 clobber_libopencm3 clean_libopencm3 libwwg

all:	libopencm3 libwwg
	$(MAKE) -C astro

clean:	clean_libopencm3
	$(MAKE) -C astro clean
	$(MAKE) -$(MAKEFLAGS) -C ./rtos/libwwg clean

clobber: clobber_libopencm3
	$(MAKE) -C astro clobber
	$(MAKE) -$(MAKEFLAGS) -C ./rtos/libwwg clobber

clean_libopencm3: clobber_libopencm3

clobber_libopencm3:
	rm -f libopencm3/lib/libopencm3_stm32f1.a
	-$(MAKE) -$(MAKEFLAGS) -C ./libopencm3 clean

libopencm3: libopencm3/lib/libopencm3_stm32f1.a

libopencm3/lib/libopencm3_stm32f1.a:
	$(MAKE) -C libopencm3

libwwg:
	$(MAKE) -C rtos/libwwg

# Uncomment if necessary:
# MAKE	= gmake

# End
