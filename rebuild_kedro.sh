# Rebuild a kedro project without resetting the data directory or credenentials.yaml
# Usage: `bash rebuild_kedro.sh <project_name>` where project_name is the name of the existing kedro project

set -e
cwd=$(pwd)
cd ".."
project_name=$1
# Convert project name to snake case
package_name=${project_name//-/_}

mv "$project_name" "$project_name-old"
kedro new -n $project_name -s $cwd --verbose

cp "$project_name-old/conf/local/credentials.yml" "$project_name/conf/local/credentials.yml"
cp "$project_name-old/conf/base/parameters_load_datasets.yml" "$project_name/conf/base/parameters_load_datasets.yml"
cp "$project_name-old/conf/base/parameters_deploy_forecast.yml" "$project_name/conf/base/parameters_deploy_forecast.yml"
cp "$project_name-old/conf/base/parameters_deploy_application.yml" "$project_name/conf/base/parameters_deploy_application.yml"
cp "$project_name-old/conf/base/parameters_configure_deployment.yml" "$project_name/conf/base/parameters_configure_deployment.yml"


if test -d "$project_name-old/data"; then
  cp -R "$project_name-old/data" "$1/data"
fi

rm -Rf "$project_name-old"