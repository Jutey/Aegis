#!/bin/bash
echo "Starting Audio Listener..."
nohup nc -l -p 9000 | ffmpeg -i - -f wav temp_audio.wav > /dev/null 2>&1 &
echo $! > ~/Aegis/listener.pid
echo "Listener started. Use './stop_listener.sh' to stop it."

