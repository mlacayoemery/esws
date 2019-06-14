thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

npm install --prefix ~/.node-red $thisDirPath
