thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

rm $thisDirPath/db.sqlite3
rm -rf $thisDirPath/wpsclient/migrations
sh $thisDirPath/setup.sh
