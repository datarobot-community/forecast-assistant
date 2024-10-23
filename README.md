# Forecast Assistant
Forecast Assistant is a customizable app template for building AI powered forecasts. In addition to 
creating a hosted, shareable user interface, Forecast Assistant provides: 

* Best in class predictive model training and deployment using DataRobot AutoTS
* An intelligent explanation of factors driving the forecast, uniquely derived for any series at any time

![Using Forecastic](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/launch_gifs/forecast-assistant-smallest.gif)


## Getting started
1. ```
   git clone https://github.com/datarobot/recipe-forecastic-reactic.git
   ```

2. Create the file `.env` in the root directory of the repo and populate your credentials.
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
   
3. Set environment variables using your `.env` file. We have provided a helper script:
   ```
   source set_env.sh
   # on Windows: set_env.bat or Set-Env.ps1
   ```
   This script will export environment variables from `.env` and activate the virtual 
   environment in `.venv/` (if present).

4. [For first time users] Install the pulumi CLI following the instructions [here](#details).


5. Create a new stack for your project (update the placeholder YOUR_PROJECT_NAME).
   ```
   pulumi stack init YOUR_PROJECT_NAME
   ```

6. Provision all resources, install dependencies in a new virtual environment located in `.venv/`
   ```
   pulumi up
   ```

### Details
Instructions for installing pulumi are [here][pulumi-install]. In many cases this can be done
with:
```
curl -fsSL https://get.pulumi.com | sh
pulumi login --local
```

Python must be installed for this project to run. By default, pulumi will use the python binary
aliased to `python3` to create a new virtual environment. If you wish to self-manage your virtual
environment, delete the `virtualenv` and `toolchain` keys from `Pulumi.yaml` before running `pulumi up`.


For projects that will be maintained we recommend forking the repo so upstream fixes and
improvements can be merged in the future.

[pulumi-install]: https://www.pulumi.com/docs/iac/download-install/

### Feature Flags
This app template requires certain feature flags to be enabled or disabled in your DataRobot account.
The required feature flags can be found in [infra/feature_flag_requirements.yaml](infra/feature_flag_requirements.yaml). Contact your DataRobot representative for more information.

## Architecture Overview
![Forecast Assistant](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/forecasting_architecture.svg)

## Make changes
### Change the data and how the model is trained
1. Edit the following two notebooks:
   - `notebooks/train_model.ipynb`: training data ingest, preparation, model training settings
   - `notebooks/prep_scoring_data.ipynb`: scoring data preparation (data is used to show forecast in frontend)
   
   The last cell of each notebook writes outputs needed for the rest of the pipeline and must remain.
2. Run the revised notebooks.
3. Run `pulumi up` to update your stack with the changes.
4. For a forecasting app that is continuously updated, consider running `prep_scoring_data.ipynb` on a schedule.

### Change the frontend
1. Ensure you have already run `pulumi up` at least once (to provision the time series deployment)
2. Streamlit assets are in `frontend/` and can be directly edited. After provisioning the stack 
   at least once, you can also test the frontend locally using `streamlit run app.py` from the
   `frontend/` directory (don't forget to initialize your environment using `source set_env.sh`)
3. Run `pulumi up` again to update your stack with the changes.

## Share results
1. Log into app.datarobot.com
2. Navigate to Registry > Application.
3. Navigate to the Application row you want to share and click on the three dots on the right and select Share from the dropdown. 

## Delete all provisioned resources
```
pulumi down
```
