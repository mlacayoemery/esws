thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

python3 $thisDirPath/manage.py runserver
