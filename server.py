from dotenv import load_dotenv  # pip install python-dotenv
import ldclient
from ldclient.config import Config
import logging
import json
import time
import boto3
import os
import random
import signal
from boto3.dynamodb.conditions import Attr
from utils.create_context import create_multi_context
from multiprocessing import Process


noophandler = logging.NullHandler()
nolog = logging.getLogger("")
nolog.setLevel(logging.INFO)
nolog.addHandler(noophandler)

app_path = os.path.dirname(os.path.realpath(__file__))
loghandler = logging.FileHandler(app_path + "/rg_runner.log", mode="a")
loghandler.setFormatter(
    logging.Formatter(
        "{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M:%S"
    )
)
logger = logging.getLogger("app_log")
logger.setLevel(logging.INFO)
logger.addHandler(loghandler)

print("Logging to " + app_path + "/rg_runner.log")


load_dotenv()


DDB_TABLE = "coastdemo-demo-tracker"
FLAG_KEY = os.environ.get("RG_FLAG_KEY")
NUMERIC_METRIC_1 = os.environ.get("NUMERIC_METRIC_1")
BINARY_METRIC_1 = os.environ.get("BINARY_METRIC_1")
NUMERIC_METRIC_1_FALSE_RANGE = json.loads(
    os.environ.get("NUMERIC_METRIC_1_FALSE_RANGE")
)
NUMERIC_METRIC_1_TRUE_RANGE = json.loads(os.environ.get("NUMERIC_METRIC_1_TRUE_RANGE"))
BINARY_METRIC_1_FALSE_CONVERTED = os.environ.get("BINARY_METRIC_1_FALSE_CONVERTED")
BINARY_METRIC_1_TRUE_CONVERTED = os.environ.get("BINARY_METRIC_1_TRUE_CONVERTED")


shut_me_down = False


def shutdown(signum, frame):
    global shut_me_down
    logger.info("Received signal " + signal.Signals(signum).name)
    logger.info("Shutting down Release Guardian Runner")
    shut_me_down = True


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def error_chance(chance_number):
    chance_calc = random.randint(1, 100)
    if chance_calc <= chance_number:
        return True
    else:
        return False


def rg_runner(
    project_key,
    sdk_key,
    flag_key,
    binary_metric_1,
    numeric_metric_1,
    binary_metric_1_false_converted,
    binary_metric_1_true_converted,
    numeric_metric_1_false_range,
    numeric_metric_1_true_range,
):
    local_client = ldclient.client.LDClient(Config(sdk_key=sdk_key, stream=False))
    ddb_table = boto3.resource("dynamodb").Table(DDB_TABLE)
    response = ddb_table.update_item(
        Key={"ProjectKey": project_key},
        UpdateExpression="set RGRunning = :r",
        ExpressionAttributeValues={":r": True},
        ReturnValues="UPDATED_NEW",
    )
    for i in range(500):
        context = create_multi_context()
        flag_detail = local_client.variation_detail(
            flag_key,
            context,
            {"max_tokens": 4096, "modelId": "gpt-4o", "temperature": 1},
        )
        index = flag_detail.variation_index
        flag_variation = flag_detail.value

        if index == 0:
            logger.debug("Serving control")
            if error_chance(int(binary_metric_1_false_converted)):
                local_client.track(binary_metric_1, context)
                logger.debug("Tracking " + binary_metric_1)
            else:
                numeric_metric_value = random.randint(
                    int(numeric_metric_1_false_range[0]),
                    int(numeric_metric_1_false_range[1]),
                )
                local_client.track(
                    numeric_metric_1, context, metric_value=numeric_metric_value
                )
                logger.debug(
                    f"Tracking {numeric_metric_1} with value {numeric_metric_value}"
                )

        else:
            logger.debug("Serving treatment")
            if error_chance(int(binary_metric_1_true_converted)):
                local_client.track(binary_metric_1, context)
                logger.debug("Tracking " + binary_metric_1)
            else:
                numeric_metric_value = random.randint(
                    int(numeric_metric_1_true_range[0]),
                    int(numeric_metric_1_true_range[1]),
                )
                local_client.track(
                    numeric_metric_1, context, metric_value=numeric_metric_value
                )
                logger.debug(
                    f"Tracking {numeric_metric_1} with value {numeric_metric_value}"
                )
    response = ddb_table.update_item(
        Key={"ProjectKey": project_key},
        UpdateExpression="set RGRunning = :r",
        ExpressionAttributeValues={":r": False},
        ReturnValues="UPDATED_NEW",
    )
    logger.debug(context)
    local_client.flush()
    time.sleep(1)
    local_client.close()


def detect_release_guardian():
    global shut_me_down
    while not shut_me_down:
        logger.info("Scanning all projects...")
        ddb_table = boto3.resource("dynamodb").Table(DDB_TABLE)
        response = ddb_table.scan(FilterExpression=Attr("UserId").ne("TDB"))
        context = create_multi_context()
        itemcount = len(response["Items"])
        for item in response["Items"]:
            rg_is_running = False
            client = ldclient.client.LDClient(
                Config(sdk_key=item["SdkKey"], stream=False)
            )
            flag_detail = client.variation_detail(
                FLAG_KEY,
                context,
                {"max_tokens": 4096, "modelId": "gpt-4o", "temperature": 1},
            )
            in_experiment = flag_detail.reason.get("inExperiment")
            if "RGRunning" in item:
                rg_is_running = bool(item["RGRunning"])

            if in_experiment is None:
                logger.debug(
                    "Release Guardian is not running for " + item["ProjectName"]
                )
            if in_experiment and not rg_is_running:
                logger.info("Running Release Guardian for " + item["ProjectName"])
                p = Process(
                    target=rg_runner,
                    args=(
                        item["ProjectKey"],
                        item["SdkKey"],
                        FLAG_KEY,
                        BINARY_METRIC_1,
                        NUMERIC_METRIC_1,
                        BINARY_METRIC_1_FALSE_CONVERTED,
                        BINARY_METRIC_1_TRUE_CONVERTED,
                        NUMERIC_METRIC_1_FALSE_RANGE,
                        NUMERIC_METRIC_1_TRUE_RANGE,
                    ),
                )
                p.daemon = True
                p.start()
            client.close()

        logger.info("Scanned " + str(itemcount) + " projects")
        logger.info("Sleeping for 5 seconds")
        time.sleep(5)


if __name__ == "__main__":
    logger.info("Starting Release Guardian Runner")
    detect_release_guardian()
