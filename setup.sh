# Created by matveyev at 07.04.2021

BASEDIR=`dirname $0`
cd $BASEDIR || exit

export VIEWERPATH=$PWD/
export PYTHONPATH=$PYTHONPATH:$VIEWERPATH

python3 ./build.py

chmod +x start_online_editor.sh

python3 ./make_alias.py