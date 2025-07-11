# Forecast assistant

The forecast assistant is a customizable application template for building AI-powered forecasts. In addition to creating a hosted and shareable user interface, the forecast assistant provides: 

* Best-in-class predictive model training and deployment using DataRobot forecasting.
* An intelligent explanation of factors driving the forecast that are uniquely derived for any series at any time.

> [!WARNING]
> Application templates are intended to be starting points that provide guidance on how to develop, serve, and maintain AI applications.
> They require a developer or data scientist to adapt and modify them to meet business requirements before being put into production.

![Using forecastic](https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/launch_gifs/forecast-assistant-smallest.gif)

## Table of contents
1. [Setup](#setup)
2. [Architecture overview](#architecture-overview)
3. [Why build AI Apps with DataRobot app templates?](#why-build-ai-apps-with-datarobot-app-templates)
4. [Make changes](#make-changes)
   - [Change the data and how the model is trained](#change-the-data-and-how-the-model-is-trained)
   - [Disable the LLM](#disable-the-llm)
   - [Change the LLM](#change-the-llm)
   - [Change the front-end](#change-the-front-end)
   - [Change the language in the front-end](#change-the-language-in-the-front-end)
5. [Share results](#share-results)
6. [Delete all resources](#delete-all-provisioned-resources)
7. [Setup for advanced users](#setup-for-advanced-users)
8. [Data privacy](#data-privacy)

## Setup

> [!IMPORTANT]  
> If you are running this template in a DataRobot codespace, `pulumi` is already configured and the repository is automatically cloned.
> Skip to **Step 3**.

1. If `pulumi` is not already installed, install the CLI following instructions [here](https://www.pulumi.com/docs/iac/download-install/). 
   After installing `pulumi` for the first time, restart your terminal and run:
   ```bash
   pulumi login --local  # omit --local to use Pulumi Cloud (requires separate account)
   ```

2. Clone the template repository.

   ```bash
   git clone https://github.com/datarobot-community/forecast-assistant.git
   cd forecast-assistant
   ```

3. Rename the file `.env.template` to `.env` in the root directory of the repo and populate your credentials.
   
   [Optional] If you want to use the GenAI functionality of the app, follow the instructions in `.env` to supply LLM credentials.
   
4. In a terminal, run the following command:
   
   ```bash
   python quickstart.py YOUR_PROJECT_NAME  # Windows users may have to use `py` instead of `python`
   ```
   Python 3.9+ is required.

Advanced users who want to control virtual environment creation, dependency installation, environment variable setup,
and `pulumi` invocation, see [the advanced setup instructions](#setup-for-advanced-users).


## Architecture overview
![Forecast assistant](https://s3.us-east-1.amazonaws.com/datarobot_public/drx/recipe_gifs/forecast-assistant-diagram.svg)

App Templates contain three families of complementary logic. For this template, you can [opt-in](#make-changes) to fully 
custom AI logic and a fully custom front-end or utilize DataRobot's off-the-shelf offerings:

- **AI logic**: Necessary to service AI requests, generate predictions, and manage predictive models.
  ```
  notebooks/  # Model training logic, scoring data prep logic
  ```
- **App logic**: Necessary for user consumption, whether via a hosted front-end or integrating into an external consumption layer.
  ```
  frontend/  # Streamlit frontend
  forecastic/  # App biz logic & runtime helpers
  ```
- **Operational logic**: Necessary to turn on all DataRobot assets.
  ```
  infra/  # Settings for resources and assets to be created in DataRobot
  infra/__main__.py  # Pulumi program for configuring DataRobot to serve and monitor AI and App logic
  ```


## Why build AI Apps with DataRobot app templates?

App templates transform your AI projects from notebooks to production-ready applications. Too often, getting models into production means rewriting code, juggling credentials, and coordinating with multiple tools and teams just to make simple changes. DataRobot's composable AI apps framework eliminates these bottlenecks, letting you spend more time experimenting with your ML and app logic and less time wrestling with plumbing and deployment.

- Start building in minutes: Deploy complete AI applications instantly, then customize AI logic or front-end independently - no architectural rewrites needed.
- Keep working your way: Data scientists keep working in notebooks, developers in IDEs, and configs stay isolated - update any piece without breaking others.
- Iterate with confidence: Make changes locally and deploy with confidence - spend less time writing and troubleshooting plumbing, more time improving your app.

Each template provides an end-to-end AI architecture, from raw inputs to deployed application, while remaining highly customizable for specific business requirements.

## Make changes

### Change the data and how the model is trained
1. Edit the following two notebooks:
   - `notebooks/train_model.ipynb`: Handles training data ingest and preparation and model training settings.
   - `notebooks/prep_scoring_data.ipynb`: Handles scoring data preparation (the data used to show forecasts in the front-end).
   
   The last cell of each notebook is required, as it writes outputs needed for the rest of the pipeline.

**Recent improvements in `train_model.ipynb`:**
- **Dual-mode operation**: The notebook now supports both training new models and using existing deployments
- **Automatic metadata extraction**: When using an existing deployment, the notebook automatically extracts model metadata (target, datetime partition column, etc.)
- **Flexible feature configuration**: Easy configuration of known-in-advance features for what-if analysis
- **Error handling**: Improved error handling with fallback mechanisms for missing model metadata

2. Run the revised notebooks.
3. Run `pulumi up` to update your stack with these changes.
```bash
source set_env.sh  # On windows use `set_env.bat`
pulumi up
```  
4. For a forecasting app that is continuously updated, consider running `prep_scoring_data.ipynb` on a schedule.

### Disable the LLM
In `infra/settings_generative.py`: Set `LLM=None` to disable any generative output altogether.

### Use an existing forecast deployment

To use an existing forecast deployment instead of creating a new one:

1. In `.env`: Set `FORECAST_DEPLOYMENT_ID` to the ID of your existing deployment
2. Run `pulumi up` to update your stack with the existing deployment
   ```bash
   source set_env.sh  # On windows use `set_env.bat`
   pulumi up
   ```

> **⚠️ Note:** When using an existing deployment:
> - The script will skip creating batch prediction jobs and retraining policies  
> - The `train_model.ipynb` notebook will skip training and extract metadata from the existing model
> - You may need to adjust the `feature_settings_config` in the notebook to match your model's known-in-advance features

**Files that need modification for existing deployments:**

When using an existing deployment, you may need to modify these files to match your model's configuration:

1. **`notebooks/train_model.ipynb`** - Update the `feature_settings_config` to match your model's known-in-advance features:
   ```python
   feature_settings_config=[
       FeatureSettingConfig(feature_name="Your_Feature_Name", known_in_advance=True),
       # Add other known-in-advance features from your model
   ]
   ```

2. **`notebooks/prep_scoring_data.ipynb`** - Ensure your scoring data preparation matches the data format expected by your existing model

3. **`forecastic/schema.py`** - Update app settings if your model has different features or requirements

**What happens when using an existing deployment:**

- **Model Training**: Completely skipped - no new model is trained
- **Data Ingestion**: Skipped - uses existing model's training data
- **Metadata Extraction**: The notebook extracts target, datetime partition column, and other model metadata from your existing deployment
- **Resource Creation**: Only creates the application frontend and LLM components (if enabled)
- **Batch Prediction**: Not created (you'll need to set up your own if needed)
- **Retraining Policy**: Not created (you'll need to set up your own if needed)

### Change the LLM

1. Modify the `LLM` setting in `infra/settings_generative.py` by changing `LLM=LLMs.AZURE_OPENAI_GPT_4_O_MINI` to any other LLM from the `LLMs` object. 
     - Trial users: Please set `LLM=LLMs.AZURE_OPENAI_GPT_4_O_MINI` since GPT-4o is not supported in the trial. Use the `OPENAI_API_DEPLOYMENT_ID` in `.env` to override which model is used in your azure organisation. You'll still see GPT 4o-mini in the playground, but the deployed app will use the provided azure deployment.  
2. To use an existing TextGen model or deployment:
      - In `infra/settings_generative.py`: Set `LLM=LLMs.DEPLOYED_LLM`.
      - In `.env`: Set either the `TEXTGEN_REGISTERED_MODEL_ID` or the `TEXTGEN_DEPLOYMENT_ID`
      - In `.env`: Set `CHAT_MODEL_NAME` to the model name expected by the deployment (e.g. "claude-3-7-sonnet-20250219" for an anthropic deployment, "datarobot-deployed-llm" for NIM models ) 
3. In `.env`: If not using an existing TextGen model or deployment, provide the required credentials dependent on your choice.
4. Run `pulumi up` to update your stack (Or rerun your quickstart).
      ```bash
      source set_env.sh  # On windows use `set_env.bat`
      pulumi up
      ```

> **⚠️ Availability information:**  
> Using a NIM model requires custom model GPU inference, a premium feature. You will experience errors by using this type of model without the feature enabled. Contact your DataRobot representative or administrator for information on enabling this feature.

### Change the front-end
1. Ensure you have already run `pulumi up` at least once (to provision the time series deployment).
2. Streamlit assets are in `frontend/` and can be edited. After provisioning the stack
   at least once, you can also test the front-end locally using `streamlit run app.py` from the
   `frontend/` directory (don't forget to initialize your environment using `source set_env.sh`).
```bash
source set_env.sh  # On windows use `set_env.bat`
cd frontend
streamlit run app.py
```
3. Run `pulumi up` again to update your stack with the changes.
```bash
source set_env.sh  # On windows use `set_env.bat`
pulumi up
```

#### Change the language in the front-end
Optionally, you can set the application locale in `forecastic/i18n.py`, e.g. `APP_LOCALE = LanguageCode.JA`. Supported locales are Japanese and English, with English set as the default.

#### Application resources
The application now supports inheriting resource configurations from the Application Source. When the Application Source is created, the system automatically fetches its resource settings (replicas, memory, CPU) via the DataRobot API and applies them to the Custom Application.

**How it works:**
1. The Application Source is created with its resource configuration
2. The system fetches the source's resource details using `application_source.id`
3. These resources are automatically applied to the Custom Application

**Environment variables required:**
- `DATAROBOT_ENDPOINT`: Your DataRobot API endpoint
- `DATAROBOT_API_TOKEN`: Your DataRobot API token

**Fallback behavior:**
- If resources cannot be fetched from the Application Source, the system falls back to DataRobot's automatic resource allocation
- Error messages are logged as warnings, ensuring deployment continues successfully

### Environment Variables

The following environment variables can be configured in your `.env` file:

**Required for all deployments:**
- `DATAROBOT_ENDPOINT`: Your DataRobot API endpoint (e.g., `https://app.datarobot.com`)
- `DATAROBOT_API_TOKEN`: Your DataRobot API token

**Optional for existing deployments:**
- `FORECAST_DEPLOYMENT_ID`: ID of an existing forecast deployment to reuse instead of creating a new one
- `TEXTGEN_REGISTERED_MODEL_ID`: ID of an existing registered model for LLM functionality
- `TEXTGEN_DEPLOYMENT_ID`: ID of an existing LLM deployment for LLM functionality
- `CHAT_MODEL_NAME`: Model name for LLM deployments (e.g., "claude-3-7-sonnet-20250219", "datarobot-deployed-llm")

**Optional for LLM providers:**
- `OPENAI_API_KEY`: OpenAI API key (for OpenAI LLMs)
- `OPENAI_API_DEPLOYMENT_ID`: Azure OpenAI deployment ID (for Azure OpenAI)
- `ANTHROPIC_API_KEY`: Anthropic API key (for Claude models)
- `GOOGLE_API_KEY`: Google API key (for Google LLMs)

**Optional for advanced configuration:**
- `DATAROBOT_DEFAULT_USE_CASE`: Use case ID to associate with the project

## Share results
1. Log into the DataRobot application.
2. Navigate to **Registry > Applications**.
3. Navigate to the application you want to share, open the actions menu, and select **Share** from the dropdown.

## Delete all provisioned resources
```bash
pulumi down
```
Then run the jupyter notebook `notebooks/delete_non_pulumi_assets.ipynb`.

## Setup for advanced users
For manual control over the setup process, adapt the following steps for MacOS/Linux to your environent:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
source set_env.sh
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
e.g., for Windows/conda/cmd.exe the previous example would change to the following:
```bash
conda create --prefix .venv pip
conda activate .\.venv
pip install -r requirements.txt
set_env.bat
pulumi stack init YOUR_PROJECT_NAME
pulumi up 
```
For projects that will be maintained, DataRobot recommends forking the repo so upstream fixes and improvements can be merged in the future.

## Data privacy
Your data privacy is important to DataRobot. Data handling is governed by the DataRobot [Privacy Policy](https://www.datarobot.com/privacy/). Review the policy before using your own data with DataRobot.
