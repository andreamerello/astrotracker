# special configuration of screen: press CTRL+C to quit the screen
cat > /tmp/myscreenrc <<EOF
bindkey "^C" quit
EOF

sudo screen -c /tmp/myscreenrc /dev/ttyACM0 115200
