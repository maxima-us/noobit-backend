import os
import subprocess
import logging
import shutil


def startup_monit():

    # Check if we have a file at path: /etc/monit/monitrc
    if not os.path.isfile("/etc/monit/monitrc"):
        logging.warning("File missing at path: /etc/monit/monitrc. Copying template to path")
        shutil.copy("monitrc", "/etc/monit/monitrc")
        logging.warning("Please refer to the following guide for configuration: https://guides.wp-bullet.com/configure-monit-send-email-alerts-mailgun/")

    # Validate syntax from monit control file ==> check again later, this doesnt seem to work
    # as check_output raises an error whenever stdout returns sthg (not empty)
    # out = subprocess.check_output(["monit", "-t"])
    # if out != "Control file syntax OK":
    #     raise Exception("Syntax error in monit control file")

    # Start monit
    # subprocess.call(["sudo", "monit"])