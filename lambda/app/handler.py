import ldclient
from ldclient.config import Config
from ldclient.context import Context
import boto3
import requests
import json
import os
import random
import time
from utils.create_context import create_multi_context

"""
Get environment variables
"""

SDK_KEY = None
LD_API_KEY = os.environ.get("LD_API_KEY")
# NUMERIC_METRIC_1 = os.environ.get("NUMERIC_METRIC_1")
# BINARY_METRIC_1 = os.environ.get("BINARY_METRIC_1")
NUMERIC_METRIC_1_FALSE_RANGE = json.loads(
    os.environ.get("NUMERIC_METRIC_1_FALSE_RANGE")
)
NUMERIC_METRIC_1_TRUE_RANGE = json.loads(os.environ.get("NUMERIC_METRIC_1_TRUE_RANGE"))
BINARY_METRIC_1_FALSE_CONVERTED = os.environ.get("BINARY_METRIC_1_FALSE_CONVERTED")
BINARY_METRIC_1_TRUE_CONVERTED = os.environ.get("BINARY_METRIC_1_TRUE_CONVERTED")

logs = boto3.client("logs")

"""
It's just fun :) A tribute to Tom Totenberg -- even though it only shows up in the logs! :) 
"""


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


"""
Get the project, environment, and flag keys from the resource string
"""


def get_resource_names(resource):
    resource_items = resource.split(":")
    for item in resource_items:
        res = item.split("/")
        match res[0]:
            case "proj":
                tp_key = res[1].split(";")
                project_key = tp_key[0]
            case "env":
                te_key = res[1].split(";")
                env_key = te_key[0]
            case "flag":
                tf_key = res[1].split(";")
                flag_key = tf_key[0]
    return project_key, env_key, flag_key


"""
Get the SDK key from the LaunchDarkly API
"""


def get_sdk_key(project_key, env_key):
    global LD_API_KEY

    url = (
        "https://app.launchdarkly.com/api/v2/projects/"
        + project_key
        + "/environments/"
        + env_key
    )

    headers = {"Content-Type": "application/json", "Authorization": LD_API_KEY}

    response = requests.get(
        url,
        headers=headers,
    )
    data = json.loads(response.text)

    return data["apiKey"]


def get_metrics(project_key, env_key, flag_key):
    global LD_API_KEY
    retval = []

    url = (
        "https://app.launchdarkly.com/api/v2/projects/"
        + project_key
        + "/flags/"
        + flag_key
        + "/measured-rollouts?filter=environmentKey:"
        + env_key
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": LD_API_KEY,
        "LD-API-Version": "beta",
    }

    response = requests.get(
        url,
        headers=headers,
    )

    data = json.loads(response.text)
    total = len(data["items"])
    if total > 0:
        item = data["items"][total - 1]
        metrics = item["design"]["metrics"]
        for metric in metrics:
            retval.append(
                {
                    "key": metric["key"],
                    "name": metric["name"],
                    "isNumeric": metric["isNumeric"],
                }
            )

    return retval


"""
Error true or false calculator. Returns True if the random number is less than or equal to the chance_number.
"""


def error_chance(chance_number):
    chance_calc = random.randint(1, 100)
    if chance_calc <= chance_number:
        return True
    else:
        return False


def lambda_handler(event, context):
    global LD_API_KEY
    global logs
    count = 0

    data = json.loads(event["body"])
    print(event["body"])
    for action in data["accesses"]:
        current_action = action["action"]
        current_resource = action["resource"]
        project_key, env_key, flag_key = get_resource_names(current_resource)

        print("Action: " + current_action)
        print("Resource: " + current_resource)
        print("Project Key: " + project_key)
        print("Environment Key: " + env_key)
        print("Flag Key: " + flag_key)

        # actionable = [
        #     "updateFallthroughWithMeasuredRollout",
        #     "updateRulesWithMeasuredRollout",
        #     "updateRules",
        # ]

        # if current_action not in actionable:
        #     print("Not actionable...exiting.")
        #     return {
        #         "statusCode": 200,
        #         "body": '{"message": "Not actionable...exiting."}',
        #     }

        sdk_key = get_sdk_key(project_key, env_key)

        ldclient.set_config(Config(sdk_key))

        if current_action == "updateRules":
            x_context = create_multi_context()
            x_flag_detail = ldclient.get().variation_detail(
                flag_key, x_context, {"no_data_found": True}
            )

            in_experiment = x_flag_detail.reason.get("inExperiment")
            if in_experiment is None:
                print("Not actionable...exiting.")
                return {
                    "statusCode": 200,
                    "body": '{"message": "Not actionable...exiting."}',
                }

        show_banner()
        metrics = get_metrics(project_key, env_key, flag_key)

        time.sleep(10)

        for i in range(500):
            flag_context = create_multi_context()
            flag_detail = ldclient.get().variation_detail(
                flag_key,
                flag_context,
                {"no_data_found": True},
            )
            index = flag_detail.variation_index
            flag_variation = flag_detail.value

            if index == 0:
                print("Serving control")
                if error_chance(int(BINARY_METRIC_1_FALSE_CONVERTED)):
                    for metric in metrics:
                        if not metric["isNumeric"]:
                            ldclient.get().track(metric["key"], flag_context)
                            print(
                                "Tracking "
                                + metric["name"]
                                + " ("
                                + metric["key"]
                                + ")"
                            )
                else:
                    for metric in metrics:
                        if metric["isNumeric"]:
                            numeric_metric_value = random.randint(
                                int(NUMERIC_METRIC_1_FALSE_RANGE[0]),
                                int(NUMERIC_METRIC_1_FALSE_RANGE[1]),
                            )
                            ldclient.get().track(
                                metric["key"],
                                flag_context,
                                metric_value=numeric_metric_value,
                            )
                            print(
                                "Tracking "
                                + metric["name"]
                                + " ("
                                + metric["key"]
                                + ") with value "
                                + str(numeric_metric_value)
                            )

            else:
                print("Serving treatment")
                if error_chance(int(BINARY_METRIC_1_TRUE_CONVERTED)):
                    for metric in metrics:
                        if not metric["isNumeric"]:
                            ldclient.get().track(metric["key"], flag_context)
                            print(
                                "Tracking "
                                + metric["name"]
                                + " ("
                                + metric["key"]
                                + ")"
                            )
                else:
                    for metric in metrics:
                        if metric["isNumeric"]:
                            numeric_metric_value = random.randint(
                                int(NUMERIC_METRIC_1_TRUE_RANGE[0]),
                                int(NUMERIC_METRIC_1_TRUE_RANGE[1]),
                            )
                            ldclient.get().track(
                                metric["key"],
                                flag_context,
                                metric_value=numeric_metric_value,
                            )
                            print(
                                "Tracking "
                                + metric["name"]
                                + " ("
                                + metric["key"]
                                + ") with value "
                                + str(numeric_metric_value)
                            )
            if i % 20 == 0:
                ldclient.get().flush()
            time.sleep(0.05)

        ldclient.get().flush()
        time.sleep(1)
        ldclient.get().close()

    return {"statusCode": 200, "body": '{"message": "Success"}'}
