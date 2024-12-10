# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Unreleased

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
