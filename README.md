# Forecast Assistant

The forecast assistant is a customizable application template for building AI-powered forecasts. In addition to creating a hosted and shareable user interface, the forecast assistant provides: 

* Best-in-class predictive model training and deployment using DataRobot AutoTS.
* An intelligent explanation of factors driving the forecast that are uniquely derived for any series at any time.

![Using Forecastic](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/launch_gifs/forecast-assistant-smallest.gif)


## Setup


1. Clone the template's repository.
   ```
   git clone https://github.com/datarobot-community/forecast-assistant.git
   ```

2. Create the file `.env` in the root directory of the repository and populate your credentials.
   ```
   DATAROBOT_API_TOKEN=...
   DATAROBOT_ENDPOINT=...  # e.g. https://app.datarobot.com/api/v2
   # [Optional]: Provide an ID of a dedicated prediction environment - otherwise we create a new serverless prediction environment
   # DATAROBOT_PREDICTION_ENVIRONMENT_ID=...  # dedicated prediction server id from https://app.datarobot.com/console-nextgen/prediction-environments
   OPENAI_API_KEY=...
   OPENAI_API_VERSION=...  # e.g. 2024-02-01
   OPENAI_API_BASE=...  # e.g. https://your_org.openai.azure.com/
   OPENAI_API_DEPLOYMENT_ID=...  # e.g. gpt-4
   PULUMI_CONFIG_PASSPHRASE=...  # required, choose an alphanumeric passphrase to be used for encrypting pulumi config
   ```
   
3. Set environment variables using your `.env` file. Use the helper script provided below:
   ```
   source set_env.sh
   # on Windows: set_env.bat or Set-Env.ps1
   ```
   This script exports environment variables from `.env` and activate the virtual 
   environment in `.venv/` (if present).

4. If you're a first-time user, install the Pulumi CLI by following the instructions [here](#details) before proceeding with this workflow.

5. Create a new stack for your project (update the placeholder `YOUR_PROJECT_NAME`).
   ```
   pulumi stack init YOUR_PROJECT_NAME
   ```

6. Provision all resources and install dependencies in a new virtual environment located in `.venv/`.
   ```
   pulumi up
   ```

### Details
Instructions for installing Pulumi are [here](https://www.pulumi.com/docs/iac/download-install/). In many cases this can be done with the code below:
```
curl -fsSL https://get.pulumi.com | sh
pulumi login --local
```

Restart your terminal.
```
source set_env.sh
# on Windows: set_env.bat or Set-Env.ps1
```

Python must be installed for this project to run. By default, pulumi will use the Python binary aliased to `python3` to create a new virtual environment. If you wish to self-manage your virtual environment, delete the `virtualenv` and `toolchain` keys from `Pulumi.yaml` before running `pulumi up`. For projects that will be maintained, DataRobot recommends forking the repo so upstream fixes and improvements can be merged in the future.

### Feature flags

This app template requires certain feature flags to be enabled or disabled in your DataRobot account. The required feature flags can be found in [infra/feature_flag_requirements.yaml](infra/feature_flag_requirements.yaml). Contact your DataRobot representative or administrator for information on enabling the feature.

## Architecture Overview
![Forecast Assistant](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/forecasting_architecture.svg)

## Make changes

### Change the data and how the model is trained
1. Edit the following two notebooks:
   - `notebooks/train_model.ipynb`: Handles training data ingest and preparation and model training settings.
   - `notebooks/prep_scoring_data.ipynb`: Handles scoring data preparation (the data used to show forecasts in the front-end).
   
   The last cell of each notebook is required, as it writes outputs needed for the rest of the pipeline.
2. Run the revised notebooks.
3. Run `pulumi up` to update your stack with these changes.
4. For a forecasting app that is continuously updated, consider running `prep_scoring_data.ipynb` on a schedule.

### Change the front-end
1. Ensure you have already run `pulumi up` at least once (to provision the time series deployment).
2. Streamlit assets are in `frontend/` and can be edited. After provisioning the stack
   at least once, you can also test the frontend locally using `streamlit run app.py` from the
   `frontend/` directory (don't forget to initialize your environment using `source set_env.sh`).
3. Run `pulumi up` again to update your stack with the changes.

#### Change the language in the frontend
Optionally, you can set the application locale here as well. e.g. `MAIN_APP_LOCALE=es_LA`. Supported locales include Spanish (es_LA) and Japanese (ja_JP) in addition to the default language (en_US).

## Share results
1. Log into the DataRobot application.
2. Navigate to **Registry > Applications**.
3. Navigate to the application you want to share, open the actions menu, and select **Share** from the dropdown.

## Delete all provisioned resources
```
pulumi down
```
