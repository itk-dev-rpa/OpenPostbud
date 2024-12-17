# OpenPostbud

## Introduction

OpenPostbud is a web application that makes it possible to do mail merge and mass shipment of Digital Post
using Service Platformen.

OpenPostbud is split into two logical parts: The web app and the task workers.
The web app is the frontend presented to the user. The workers run in separate processes
performing any queued up shipment or registration tasks.

## Installation

OpenPostbud needs Python (>=3.11), pip and setuptools installed to be installed.

To install OpenPostbud navigate to the main folder where pyproject.toml is located and call

```bash
pip install .
```

This will build and install OpenPostbud into the active environment.
It will also install any dependencies from pip.

### Libre Office

OpenPostbud uses Libre Office to convert docx files to pdf.
It does so by calling the Libre Office executable in the command line.

## Environment variables

### OpenPostbud app

To run OpenPostbud needs the following environment variables set:

| Name                    | description                                         | Type                    |
| ----------------------- | --------------------------------------------------- | ----------------------- |
| nicegui_storage_secret  | The secret used to store user session tokens        | String                  |
| database_storage_secret | The encryption key used to encrypt database columns | A valid 128-bit AES key |
| auth_lifetime_seconds   | The number of seconds to keep a user logged in      | Integer                 |

### Workers

To run the shipment and registration workers need the following environment variables set:

| Name                           | description                                                           | Type        |
| ------------------------------ | --------------------------------------------------------------------- | ----------- |
| cvr                            | The CVR number of the organisation                                    | String      |
| kombit_cert_path               | The absolute path to the certificate file used for Service Platformen | Path string |
| Kombit_test_env                | Whether to use the test environment of Service Platformen             | boolean     |
| registration_worker_sleep_time | The number of seconds for the registration worker to idle             | Integer     |
| shipment_worker_sleep_time     | The number of seconds for the shipment worker to idle                 | Integer     |
| sender_label                   | The label to set on the sender of Digital Post                        | String      |
| path_to_libreoffice            | The absolute path to the Libre Office executable                      | Path string |

## Running the app

### OpenPostbud app

To run the app run the main.py file in the project folder.

```bash
python OpenPostbud/src/OpenPostbud/main.py
```

This will start a Uvicorn server which listens on port 8080.

### Workers

To run the workers:

```bash
python OpenPostbud/src/OpenPostbud/workers/registration_worker.py
python OpenPostbud/src/OpenPostbud/workers/shipment_worker.py
```

These workers will run in an infinite loop where they check the database for tasks. If there are no tasks the
workers will idle for a set amount of time.

## Database

OpenPostbud uses SQLite and it creates an SQLite database in the current working directory called `database.db`.

Some sensitive columns in the database are encrypted using AES.