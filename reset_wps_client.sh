thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

rm $thisDirPath/tools/wpsclient/db.sqlite3
rm -rf $thisDirPath/tools/wpsclient/wpsclient/migrations
sh $thisDirPath/tools/wpsclient/setup.sh
