#!/bin/bash
if [ -f ~/Aegis/listener.pid ]; then
    kill $(cat ~/Aegis/listener.pid)
    rm ~/Aegis/listener.pid
    echo "Listener stopped."
else
    echo "No active listener found."
fi

