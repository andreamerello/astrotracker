#!/bin/bash

# print a warning if we are flashing a debug build
strings main.elf | grep "DEBUG BUILD"
echo

expect <<EOF

spawn telnet
expect "telnet>"
send "open localhost 4444\n"
expect ">"
send "reset halt\n"
expect ">"
send "flash write_image erase main.elf\n"
expect ">"
send "reset\n"
#spawn ./tool/reset_astro

EOF
