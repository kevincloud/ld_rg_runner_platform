# LaunchDarkly Release Guardian Populator
This is a demo data population tool created for a very specific setup. It's probably not worth it for you to copy this. It does the following:
- Persistently loops to check if RG is running
    - If no: it waits 5 seconds then checks again
    - If yes: It will fire off 500 evaluations of the flag, and track metrics for it

## To use:
1. `pip install -r /path/to/requirements.txt`
2. `python main.py`