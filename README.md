# Forecast Assistant

The forecast assistant is a customizable application template for building AI-powered forecasts. In addition to creating a hosted and shareable user interface, the forecast assistant provides: 

* Best-in-class predictive model training and deployment using DataRobot Forecasting.
* An intelligent explanation of factors driving the forecast that are uniquely derived for any series at any time.

> [!WARNING]
> Application Templates are intended to be starting points that provide guidance on how to develop, serve, and maintain AI applications.
> They require a developer or data scientist to adapt, and modify them to business requirements before being put into production.

![Using Forecastic](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/launch_gifs/forecast-assistant-smallest.gif)

## Setup

1. If `pulumi` is not already installed, install the CLI following instructions [here](https://www.pulumi.com/docs/iac/download-install/). 
   After installing for the first time, restart your terminal and run:
   ```
   pulumi login --local  # omit --local to use Pulumi Cloud (requires separate account)
   ```

2. Clone the template repository.

   ```
   git clone https://github.com/datarobot-community/forecast-assistant.git
   cd forecast-assistant
   ```

3. Rename the file `.env.template` to `.env` in the root directory of the repo and populate your credentials.

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
   
4. In a terminal run:
   ```
   python quickstart.py YOUR_PROJECT_NAME  # Windows users may have to use `py` instead of `python`
   ```

Advanced users desiring control over virtual environment creation, dependency installation, environment variable setup
and `pulumi` invocation see [here](#setup-for-advanced-users).


## Architecture Overview
![Forecast Assistant](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/forecasting_architecture.svg)

## Why build AI Apps with DataRobot App Templates?

App Templates transform your AI projects from notebooks to production-ready applications. Too often, getting models into production means rewriting code, juggling credentials, and coordinating with multiple tools & teams just to make simple changes. DataRobot's composable AI apps framework eliminates these bottlenecks, letting you spend more time experimenting with your ML and app logic and less time wrestling with plumbing and deployment.
- Start Building in Minutes: Deploy complete AI applications instantly, then customize AI logic or frontend independently - no architectural rewrites needed.
- Keep Working Your Way: Data scientists keep working in notebooks, developers in IDEs, and configs stay isolated - update any piece without breaking others.
- Iterate With Confidence: Make changes locally and deploy with confidence - spend less time writing and troubleshooting plumbing, more time improving your app.

Each template provides an end-to-end AI architecture, from raw inputs to deployed application, while remaining highly customizable for specific business requirements.

## Make changes

### Change the data and how the model is trained
1. Edit the following two notebooks:
   - `notebooks/train_model.ipynb`: Handles training data ingest and preparation and model training settings.
   - `notebooks/prep_scoring_data.ipynb`: Handles scoring data preparation (the data used to show forecasts in the front-end).
   
   The last cell of each notebook is required, as it writes outputs needed for the rest of the pipeline.
2. Run the revised notebooks.
3. Run `pulumi up` to update your stack with these changes.
```
source set_env.sh  # On windows use `set_env.bat`
pulumi up
```  
4. For a forecasting app that is continuously updated, consider running `prep_scoring_data.ipynb` on a schedule.

### Change the front-end
1. Ensure you have already run `pulumi up` at least once (to provision the time series deployment).
2. Streamlit assets are in `frontend/` and can be edited. After provisioning the stack
   at least once, you can also test the frontend locally using `streamlit run app.py` from the
   `frontend/` directory (don't forget to initialize your environment using `source set_env.sh`).
```
source set_env.sh  # On windows use `set_env.bat`
cd frontend
streamlit run app.py
```
3. Run `pulumi up` again to update your stack with the changes.
```
source set_env.sh  # On windows use `set_env.bat`
pulumi up
```

#### Change the language in the frontend
Optionally, you can set the application locale here as well. e.g. `MAIN_APP_LOCALE=ja_JP`. Supported locales include Japanese (ja_JP) in addition to the default language (en_US).

#### Change the language in the frontend
Optionally, you can set the application locale here as well. e.g. `MAIN_APP_LOCALE=ja_JP`. Supported locales include Japanese (ja_JP) in addition to the default language (en_US).

## Share results
1. Log into the DataRobot application.
2. Navigate to **Registry > Applications**.
3. Navigate to the application you want to share, open the actions menu, and select **Share** from the dropdown.

## Delete all provisioned resources
```
pulumi down
```
Then run the jupyter notebook `notebooks/delete_non_pulumi_assets.ipynb`

## Setup for advanced users
For manual control over the setup process adapt the following steps for MacOS/Linux to your environent:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
source set_env.sh
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
e.g. for Windows/conda/cmd.exe this would be:
```
conda create --prefix .venv pip
conda activate .\.venv
pip install -r requirements.txt
set_env.bat
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
For projects that will be maintained, DataRobot recommends forking the repo so upstream fixes and improvements can be merged in the future.
