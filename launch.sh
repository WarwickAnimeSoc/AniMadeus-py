#!/bin/bash

# Kill running instance of the bot
echo "Killing old bot instance."
kill -9 `cat pid.txt`
rm pid.txt

# Run bot and store pid
nohup .venv/bin/python ./animadeus.py &
echo $! > pid.txt
echo "Launched new instance."
