# Forecastic Reactic Recipe
Forecastic-reactic is a customizable recipe for building a building forecasts. It is shinier than forecastic.

In addition to creating a hosted, shareable user interface, Forecastic provides:

* Generative forecast summarization explaining important factors in predictions
* Explorable explanations over time
* Whatif scenario analysis

![reactic-forecastic-gif]

[reactic-forecastic-gif]: https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/reacticforecastic.gif

## Getting started
1. Create a [new][virtualenv-docs] python virtual environment with python >= 3.9.

2. Install `kedro` and create a new kedro project from this template
   ```bash
   pip install kedro
   kedro new --starter=https://github.com/datarobot/recipe-forecastic-reactic.git --checkout main
   cd your_project_name
   ```

3. Follow the prompts to choose between using the default dataset (flat file) or providing an ai catalog asset

4. `cd` to the newly created directory and install requirements for this template: `pip install -r requirements.txt`

5. Populate the following credentials in `conf/local/credentials.yml`:
   ```yaml
   datarobot:
     endpoint: <your endpoint>
     api_token: <your api token>
     prediction_environment_id: <your prediction environment id>

   azure_openai_llm_credentials:
     azure_endpoint: <your api endpoint>
     api_key: <your api key>
     api_version: <your api version>
     deployment_name: <your deployment name>
   ```

6. (AI Catalog dataset only) in each of the params files, fill in the empty values with the appropriate values for your dataset. Use the contents of the [`from_file`][from-file-params] folder to see examples of these parameters when they are filled in.

7. Run the pipeline: `kedro run`. Start exploring the pipeline using the kedro GUI: `kedro viz --include-hooks`

![kedro-viz]

[virtualenv-docs]: https://docs.python.org/3/library/venv.html#creating-virtual-environments
[from-file-params]: https://github.com/datarobot/recipe-forecastic-reactic/tree/main/recipe-forecastic-reactic/conf/base/from_file
[kedro-viz]:https://s3.amazonaws.com/datarobot_public/drx/recipe_gifs/kedro-viz.gif

## Making changes to the pipeline
The following files govern pipeline execution. In general, you will not need to modify
any other boilerplate files as you customize the pipeline.:

- `conf/base/parameters_*.yml`: pipeline configuration options and hyperparameters
- `conf/local/credentials.yml`: API tokens and other secrets
- `conf/base/catalog_*.yml`: file storage locations that can be used as node inputs or outputs,
  including locations of supporting assets to build DR custom models, execution environments
- `src/your_project_name/pipelines/*/nodes.py`: function definitions for the pipeline nodes
- `src/your_project_name/pipelines/*/pipeline.py`: node names, inputs and outputs
- `src/datarobotx/idp`: directory contains function definitions for for reusable idempotent DR nodes
- `include/`: directory contains raw assets and templates used by the pipeline

For a deeper orientation to kedro principles and project structure visit the [Kedro][kedro-docs]
documentation.

[kedro-docs]: https://docs.kedro.org/en/stable/

### A note on the frontend
While most templates include a frontend built in Streamlit, this application template is built
using the react framework and utilizes private code repositories in order to build a set of static webpages.
The frontend *cannot* be edited beyond modifying the configuration file parameters returned by the pipeline. Reach out to your DataRobot representative for any changes to the frontend.

### Example changes
1. Many simple pipeline configuration options can be changed by editing 
   `conf/base/parameters.yml` and then rerunning the pipeline using `kedro run`,
   e.g.:
   * Names for each created DataRobot asset
   * Feature derviation and forecast windows
   * Modeling settings such as number of workers and advanced options
   * Known in advance features
   * Calendar generation settings
   * Minimum threshold for important features

2. When not choosing to load datasets from the ai catalog, the training and scoring data for the project are housed in `include/your_project_name/autopilot`; if a new dataset is required, save the new datasets to this directory, edit the corresponding entries in the params_*.yaml files and call `kedro run` after to run the pipeline with the new data.

3. Update function definitions in `nodes.py` to change the actual logic for
   a step in the pipeline or to define a new node, e.g.:
   * `put_forecast_distance_into_registered_model_name()`: changes the name of the registered model
      so that it includes the forecast distance.
   * `ensure_deployment_settings`: Configures settings such as accuracy tracking and data drift in the deployed model.

4. Add newly defined nodes to the pipeline, change execution order, or reconfigure
   node input/output connections by editing `pipelines.yaml`.
   * `generate_calendar()`: this is a node that generates a calendar for the project and could be removed by simply deleting the node and it's corresponding reference `make_autopilot_run`.

### Required inputs for training and scoring (required when using alternative datasets)

There are some special rules for creating the forecastic-reactic web application with this template.
Specifically, the scoring and training dataset adhere to the following requirements:
   - A multiseries_id column must exist that uniquely identifies each time series.
   Note that **even if the dataset is single series**, this column must be present with a constant value in the dataset.
   - (Scoring dataset only) An association column id column must uniquely identify each row in the scoring dataset. A best practice for creating an association_id column is to concatenate the multiseries_id and date columns.
   - (Scoring dataset only) The scoring data should contain future dates to be predicted. See the [timeseries docs][timeseries-docs] for information on creating a prediction-ready dataset.


[timeseries-docs]: https://docs.datarobot.com/en/docs/modeling/time/ts-predictions.html#create-a-prediction-ready-dataset

## <a name="gh-auth"></a> Authenticating with GitHub
How to install `gh` [GitHub CLI][GitHub CLI-link]

Run `gh auth login` in the terminal and answer the following questions with:
- `? What account do you want to log into?` **GitHub.com**
- `? What is your preferred protocol for Git operations on this host?` **HTTPS**
- `? Authenticate Git with your GitHub credentials?` **Yes**
- `? How would you like to authenticate GitHub CLI?` **Login with a web browser**

Copy the code in: `! First copy your one-time code:` **XXXX-XXXX**

Open a web browser at https://github.com/login/device and enter the above code manually.

You should see in the terminal:
- `✓ Authentication complete.`
- `✓ Logged in as YOUR_USERNAME`

More details on GitHub authentication [here][gh-docs].

[GitHub CLI-link]: https://github.com/cli/cli
[gh-docs]: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#https


## Contributing

If you are making changes to the codebase or constructing your own template, then the cycle of running `kedro new`, testing changes on the instantiated pipeline and copying the changes over to the core template can be inconvenient. For faster development, take the following steps:
1. Clone the repository.
2. Create a virtual environment and install the requirements: `pip install -r requirements.txt`.
3. Add your credentials to `recipe-forecastic-reactic/conf/local/credentials.yml`.
4. Add a file to `recipe-forecastic-reactic/conf/base/globals.yml` with the following content:
   ```yaml
   project_name: your_project_name  # Overrides "${globals:project_name}" in parameters.yml
   ```
5. Copy the `datarobotx` folder containing the idp helpers into the `recipe-forecastic-reactic/src` folder of the recipe template. You can find these by instantiating a new project with `kedro new`.
6. Define an environment variable `SOURCE=[file|ai_catalog]` and `kedro run` to test your pipeline. For example, to test the pipeline with a file-based source, run `SOURCE=file kedro run`. 
7. When you are finished, it is usually a good idea to execute `kedro run -p delete_assets`. This will remove DataRobot assets created during the pipeline run and unclutter your DataRobot instance.
