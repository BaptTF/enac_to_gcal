#!/bin/bash

# Open a new terminal tab or window to run the Python script
gnome-terminal --tab --title="Python Script" -e "bash -c 'cd ~/enac_to_gcal/ && python3 ical_to_gcal_sync.py; exec bash'"

# Open another new terminal tab or window to tail the logger file
gnome-terminal --tab --title="Log File" -e "bash -c 'cd ~/enac_to_gcal/ && tail -f ical_to_gcal_sync.log; exec bash'"
