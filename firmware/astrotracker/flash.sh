#!/usr/bin/expect

spawn telnet
expect "telnet>"
send "open localhost 4444\n"
expect ">"
send "reset halt\n"
expect ">"
send "flash write_image erase astrotracker/astrotracker.elf\n"
expect ">"
send "reset\n"
