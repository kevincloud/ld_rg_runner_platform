# LaunchDarkly Release Guardian Populator
This is a demo data population tool created for the SE Platform demo. It does the following:
- Persistently loops to check if RG is running
    - If no: it waits 5 seconds then checks again
    - If yes: It will fire off 500 evaluations of the flag, and track metrics for it

## To use:
1. In your terminal: `pip install -r requirements.txt`
1. Rename `.env.example` to `.env`
1. Modify the `SDK_KEY` variable to the SDK key of your environment.
1. In your terminal: `python main.py`