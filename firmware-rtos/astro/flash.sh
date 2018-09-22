#!/usr/bin/expect

spawn telnet
expect "telnet>"
send "open localhost 4444\n"
expect ">"
send "reset halt\n"
expect ">"
send "flash write_image erase main.elf\n"
expect ">"
send "reset\n"
spawn ./tool/reset_astro
