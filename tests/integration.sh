# -e stands for error: stops the script if there are errors
# -x prints  contents of the script as it runs it
set -ex
curl -sfS http://127.0.0.1:8080 > /dev/null
curl -sfS http://127.0.0.1:8080/login > /dev/null 
