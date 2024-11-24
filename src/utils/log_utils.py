#!/usr/bin/env python3
# encoding: utf-8


# File logger
import logging

# Date check
import requests 
from datetime import datetime


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


DEFAULT_LOG_LEVEL = "ALL"
DEFAULT_TOPIC = None

# Stores possible log level with its tag to be sent through ntfy server
LOG_LEVEL = {
             "NOTSET": {"id": 0, "tag": "", "priority": "default", "format":bcolors.ENDC},
             "ALL": {"id": 5, "tag": "white_check_mark", "priority": "default", "format":bcolors.ENDC},
             "DEBUG": {"id": 10, "tag": "white_check_mark", "priority": "default", "format":bcolors.ENDC},
             "INFO": {"id": 20, "tag": "white_check_mark", "priority": "default", "format":bcolors.BOLD},
             "WARNING": {"id": 30, "tag": "warning", "priority": "high", "format":bcolors.WARNING},
             "ERROR": {"id": 40, "tag": "no_entry", "priority": "urgent", "format":bcolors.ERROR}
            }


def setLogDefaults(topic = None, log_level = "INFO", logging_path = "/tmp/twitter2bluesky"):
    global DEFAULT_TOPIC, DEFAULT_LOG_LEVEL

    DEFAULT_TOPIC = topic
    DEFAULT_LOG_LEVEL = log_level

    # Logger to store data in a file
    logging.basicConfig(
        format = '[%(asctime)s][%(levelname)s] - %(message)s',
        level  = logging.INFO,      # Nivel de los eventos que se registran en el logger
        filename = logging_path, # Fichero en el que se escriben los logs
        filemode = "a",             # a ("append"), en cada escritura, si el archivo de logs ya existe,
                                    # se abre y añaden nuevas lineas.
        force=True
    )

def loggingShutdown():
    logging.shutdown()
    
#####################
# LOGGING FUNCTIONS #
#####################



"""
    Logging function to print information on screen and save it to file.

    :param msg: str with the message to post.
    :param level: logging level based on LOG_LEVEL.
    :param notify: if set to True a notification is sent to the ntfy topic configured.

    TBD: Check that logging level provided is in line with the expected.
"""
def log_screen(msg, level = "INFO", notify = False, text_format=""):
    global DEFAULT_TOPIC
    global DEFAULT_LOG_LEVEL

    timestamp = datetime.now().strftime("%Y-%m-%d|%H:%M:%S")
    
    log_level = LOG_LEVEL[level]
    print(f"{log_level['format']}{text_format}[{timestamp}] [{level}] {msg}{bcolors.ENDC}")
    
    # Access logging level by attribute
    getattr(logging, level.lower())(msg)

    # Notification setup    
    if notify:
        if DEFAULT_TOPIC is None:
            log_screen("No topic was configured to send notifications", level = "WARNING", notify = False)
            return False
        
        log_level = LOG_LEVEL[level]
        # If message log level is lower than configured, no loging is made as notification
        if log_level["id"] < LOG_LEVEL[DEFAULT_LOG_LEVEL]["id"]:
            log_screen("No notification is sent as logging level is below configured", level = "INFO", notify = False)
            return False

        requests.post("https://ntfy.sh/"+str(DEFAULT_TOPIC),
            data=str(msg).encode(encoding='utf-8'),
            headers={
            "Title": "UMH - Time check in",
            "Priority": log_level["priority"],
            "Tags": log_level["tag"]
        })
