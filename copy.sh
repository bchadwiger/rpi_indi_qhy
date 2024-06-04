# ssh allsky@192.168.178.26 ls /home/allsky/rpi_indi_qhy/images > remote_images.txt

REMOTE_USER="allsky"
REMOTE_HOST="192.168.178.26"
REMOTE_DIR="/home/allsky/rpi_indi_qhy/images/*"
LOCAL_DIR="/home/benny/Documents/SFeu/AllSky_Camera/QHY5III485_images/images"

# rsync -avz --ignore-existing --remove-source-files $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR $LOCAL_DIR
rsync -avz --remove-source-files $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR $LOCAL_DIR
