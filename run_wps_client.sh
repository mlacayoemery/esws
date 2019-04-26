thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

python3 $thisDirPath/tools/wpsclient/manage.py runserver
