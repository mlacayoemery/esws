thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

sh $thisDirPath/makemigrations.sh wpsclient
python3 $thisDirPath/manage.py migrate
