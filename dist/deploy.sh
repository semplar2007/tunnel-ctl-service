#!/bin/bash

# This script is used to deploy source files to test control server.
# For development and testing purposes.

#LOCAL_SCRIPT_FILES="*.py"
LOCAL_INITD_FILE="init.d/tunnel-ctl"
REMOTE_SERVER_IP="198.58.101.85"
REMOTE_DIR="/tmp/"
# assuming local id_rsa.pub is in '.ssh/authorized_keys' file, allowing passwordless access

echo "Deploying to $REMOTE_SERVER_IP..."
#scp "$LOCAL_SCRIPT_FILE" root@198.58.101.85:$REMOTE_DIR &&
scp "$LOCAL_INITD_FILE" root@198.58.101.85:/etc/init.d/ && echo "SCP successfull" || echo "SCP error, exit code: $?"
