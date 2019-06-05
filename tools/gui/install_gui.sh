thisScriptPath=`realpath $0`
thisDirPath=`dirname $thisScriptPath`

npm install --prefix ~/.node-red node-red-dashboard
npm install --prefix ~/.node-red $thisDirPath
