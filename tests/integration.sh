# set ex:
# -e stands for "error" stop the script if there is an error
# -x print the contents of the script as it is executed
set -ex
curl -sfS http://127.0.0.1:8000/ > /dev/null
curl -sfS http://127.0.0.1:8000/login > /dev/null 
