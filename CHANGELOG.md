# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Fixed
- Fixed credential handling when no credentials available
- Fixed chart not displaying correctly if data is not ordered by date 

## [0.1.19] - 2025-07-08

### Changed
- Better document reuse of existing forecast deployments via `FORECAST_DEPLOYMENT_ID` environment variable

### Added
- Ability to automatically populate `resources` field of created Custom Applications from their Custom Application Sources


## [0.1.18] - 2025-07-01

### Added
- Support for reusing existing forecast deployments via `FORECAST_DEPLOYMENT_ID` environment variable
- Ability to skip model training when using existing deployments for faster app setup
- Automatic extraction of model metadata from existing DataRobot deployments

## [0.1.17] - 2025-04-07

### Added
- Forecast assistant now uses a DataRobot LLM Blueprint
- LLM integration is now optional
- Support for existing textgen deployments or registered models
- Installed [the datarobot-pulumi-utils library](https://github.com/datarobot-oss/datarobot-pulumi-utils) to incorporate majority of reused logic in the `infra.*` subpackages.

## [0.1.16] - 2025-03-06

### Fixed
- "Already linked" error

### Changed
- remove drx calls in pulumi main program

## [0.1.15] - 2025-01-15

### Fixed

- Codespace python env no longer broken by quickstart
- Scoring dataset id no longer overridden by pulumi if project has been run before

### Changed

- Move pulumi entrypoint to the infra directory

## [0.1.14] - 2025-01-06

### Added

- Update safe_dump to support unicode

## [0.1.13] - 2024-12-18

### Changed
- App backend no longer depends on the current working dir to read yaml settings
- Default scoring data is a 6 month period


### Fixed

- Removed duplicative plotting call from streamlit frontend
- Minor formatting issue in streamlit date picker font
- quickstart now asks you to change the default project name
- quickstart now prints the application URL
- quickstart.py now supports multiline values correctly, even with multiple comments

## [0.1.12] - 2024-12-12

### Fixed

- quickstart.py now supports multiline values correctly
- Corrected column pointing in is_target_derived logic

### Added

- App metadata to api for creator email and created date

### Changed

- Logic for deciding default number of historical rows to render in timeseries plots
- Add python 3.9 requirement to README

## [0.1.11] - 2024-12-09

### Added

- rest_api.py that provides API routes using FastAPI and functions from api.py
- new route `/share` for application sharing
- add context tracing to this recipe.

### Fixed

- Fix comment handling in quickstart

### Changed

- add 3.9 compatibility check to mypy
- add new functions to format predictions for React frontend
- add pyproject.toml to store lint and test configuration
- revise README based on user feedback
- update pulumi-datarobot to >=0.4.5

## [0.1.10] - 2024-11-14

### Changed

- Bring release/10.2 in sync with main

## [0.1.9] - 2024-11-14

### Changed

- Removed specific concurrency for batch predictions.
- improvements to the README

## [0.1.8] - 2024-11-12

### Changed

- Bring release/10.2 in sync with main

## [0.1.7] - 2024-11-12

### Fixed

- Ensure app settings update does not cause `pulumi up` to fail
- Typehinting no longer breaks on python3.9

### Changed

- Update DataRobot logo

## [0.1.6] - 2024-11-07

### Changed

- Bring release/10.2 in sync with main

## [0.1.5] - 2024-11-07

### Added

- quickstart.py script for getting started more quickly

## [0.1.4] - 2024-10-28

### Added

- Changelog file to keep track of changes in the project.
- App localization support for Spanish and Japanese.
- Link Application and Deployment to the use case in DR
