# Created by matveyev at 07.04.2021

BASEDIR=`dirname $0`
cd $BASEDIR || exit

export VIEWERPATH=$PWD/
export PYTHONPATH=$PYTHONPATH:$VIEWERPATH

python3 ./build.py
python3 -m venv --system-site-packages ./venv

chmod +x start_online_editor.sh