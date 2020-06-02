# Monit

## Install

Install the package:  `sudo apt-get install monit`
Enable monit at boot: `systemctl enable monit`
Set monit to start on boot: `systemctl start monit`
Check monit's status: `monit status`

## Configuration

Guide on how to send out email alerts using mailgun : https://guides.wp-bullet.com/configure-monit-send-email-alerts-mailgun/
After you have configured the monitrc file, reload monit: `monit reload`

