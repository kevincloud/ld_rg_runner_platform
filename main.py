from dotenv import load_dotenv #pip install python-dotenv
import ldclient
from ldclient.config import Config
from ldclient.context import Context
import json
import os
import random
import time
from utils.create_context import create_multi_context

'''
Get environment variables
'''
load_dotenv()

SDK_KEY = os.environ.get('SDK_KEY')
FLAG_KEY = os.environ.get('RG_FLAG_KEY')
NUMERIC_METRIC_1 = os.environ.get('NUMERIC_METRIC_1')
BINARY_METRIC_1 = os.environ.get('BINARY_METRIC_1')
NUMERIC_METRIC_1_FALSE_RANGE = json.loads(os.environ.get('NUMERIC_METRIC_1_FALSE_RANGE'))
NUMERIC_METRIC_1_TRUE_RANGE = json.loads(os.environ.get('NUMERIC_METRIC_1_TRUE_RANGE'))
BINARY_METRIC_1_FALSE_CONVERTED = os.environ.get('BINARY_METRIC_1_FALSE_CONVERTED')
BINARY_METRIC_1_TRUE_CONVERTED = os.environ.get('BINARY_METRIC_1_TRUE_CONVERTED')


'''
Initialize the LaunchDarkly SDK
'''
ldclient.set_config(Config(SDK_KEY))

'''
It's just fun :)
'''
def show_banner():
    print()
    print("        ██       ")
    print("          ██     ")
    print("      ████████   ")
    print("         ███████ ")
    print("██ LAUNCHDARKLY █")
    print("         ███████ ")
    print("      ████████   ")
    print("          ██     ")
    print("        ██       ")
    print()

'''
Error true or false calculator. Returns True if the random number is less than or equal to the chance_number.
'''
def error_chance(chance_number):
    chance_calc = random.randint(1, 100)
    if chance_calc <= chance_number:
        return True
    else:
        return False


'''
Evaluate the flag for randomly generated users, and make the track() calls to LaunchDarkly
'''
def callLD():

    # Detect whether Release Guardian is running (may take a few iterations to detect)
    context = create_multi_context()
    flag_detail = ldclient.get().variation_detail(
        FLAG_KEY, 
        context, 
        {
            "max_tokens": 4096,
            "modelId": "gpt-4o",
            "temperature": 1
        }
    )

    in_experiment = flag_detail.reason.get('inExperiment')
    if in_experiment is None:
        print("Release Guardian is not running. Retrying in 5 seconds.") 
    
    if in_experiment:
        for i in range(500):
            context = create_multi_context()
            flag_detail = ldclient.get().variation_detail(
                FLAG_KEY, 
                context, 
                {
                    "max_tokens": 4096,
                    "modelId": "gpt-4o",
                    "temperature": 1
                }
            )
            index = flag_detail.variation_index
            flag_variation = flag_detail.value

            if index == 0:
                print("Serving control")
                if error_chance(int(BINARY_METRIC_1_FALSE_CONVERTED)):
                    ldclient.get().track(BINARY_METRIC_1, context)
                    print("Tracking " + BINARY_METRIC_1)
                else:
                    numeric_metric_value = random.randint(int(NUMERIC_METRIC_1_FALSE_RANGE[0]), int(NUMERIC_METRIC_1_FALSE_RANGE[1]))
                    ldclient.get().track(NUMERIC_METRIC_1, context, metric_value=numeric_metric_value)
                    print(f"Tracking {NUMERIC_METRIC_1} with value {numeric_metric_value}")

            else:
                print("Serving treatment")
                if error_chance(int(BINARY_METRIC_1_TRUE_CONVERTED)):
                    ldclient.get().track(BINARY_METRIC_1, context)
                    print("Tracking " + BINARY_METRIC_1)
                else:
                    numeric_metric_value = random.randint(int(NUMERIC_METRIC_1_TRUE_RANGE[0]), int(NUMERIC_METRIC_1_TRUE_RANGE[1]))
                    ldclient.get().track(NUMERIC_METRIC_1, context, metric_value=numeric_metric_value)
                    print(f"Tracking {NUMERIC_METRIC_1} with value {numeric_metric_value}")
            
            ldclient.get().flush()
            time.sleep(.05)
    else:
        time.sleep(5)


'''
Execute! Push Ctrl+C to stop the loop.
'''
show_banner()
while True:
    callLD()

'''
Responsibly close the LD Client
'''
ldclient.get().flush()
time.sleep(1)
ldclient.get().close()