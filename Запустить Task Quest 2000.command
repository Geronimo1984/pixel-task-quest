#!/bin/zsh
cd "$(dirname "$0")"
nohup python3 task_quest_2000.py >/dev/null 2>&1 &
osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 &
exit 0
