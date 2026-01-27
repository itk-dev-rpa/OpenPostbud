# OpenPostbud

## Introduction

OpenPostbud is a web application that makes it possible to do mail merge and mass shipment of Digital Post
using Kombit's Serviceplatformen.

OpenPostbud is split into two logical parts: The web app and the task workers.
The web app is the frontend presented to the user. The workers run in separate processes
performing any queued up shipment or registration tasks.

## Installation

OpenPostbud comes with a Docker compose file that will install and start all necessary processes.

Remember to create a `.env` file with all needed environment variables.
See below for explanations as well as `.env.example`.

### Libre Office

OpenPostbud uses Libre Office to convert docx files to pdf.
It does so by calling the Libre Office executable in the command line.
This is automatically installed by Docker.

## Environment variables

### OpenPostbud app

OpenPostbud needs the following environment variables set:

| Name                           | description                                                                | Type                    |
| ------------------------------ | -------------------------------------------------------------------------- | ----------------------- |
| nicegui_storage_secret         | The secret used to store user session tokens                               | String                  |
| database_storage_secret        | The encryption key used to encrypt database columns                        | A valid 128-bit AES key |
| auth_lifetime_seconds          | The number of seconds to keep a user logged in                             | Integer                 |
| client_id                      | OIDC client id                                                             | String                  |
| client_secret                  | OIDC client secret                                                         | String                  |
| discovery_url                  | OIDC discovery url                                                         | URL                     |
| redirect_url                   | OIDC redirect url                                                          | URL                     |
| ui_port                        | Port the application listens on                                            | Integer                 |
| ui_host                        | Host IP to listen on                                                       | string                  |
| ui_reload                      | Reload application when changes are detected                               | boolean                 |
| auth_lifetime_seconds          | How long a user session is valid                                           | integer                 |
| shipment_lifetime_days         | How long a shipment should be kept in the database after creation          | integer                 |
| registration_job_lifetime_days | How long a registration task should be kept in the database after creation | integer                 |

### Workers

The shipment, registration and message broker workers need the following environment variables set:

| Name                             | description                                                               | Type        |
| -------------------------------- | ------------------------------------------------------------------------- | ----------- |
| cvr                              | The CVR number of the organisation                                        | String      |
| kombit_cert_path                 | The absolute path to the certificate file used for Service Platformen     | Path string |
| Kombit_test_env                  | Whether to use the test environment of Service Platformen                 | boolean     |
| registration_worker_sleep_time   | The number of seconds for the registration worker to idle                 | Integer     |
| shipment_worker_sleep_time       | The number of seconds for the shipment worker to idle                     | Integer     |
| sender_label                     | The label to set on the sender of Digital Post                            | String      |
| message_broker_queue_id          | The UUID of the message broker queue. Get this from the Kombit admin page | UUID        |
| message_broker_worker_sleep_time | The number of seconds for the message broker worker to idle               | Integer     |

### Development

Under development it's possible to set some environment variables to help with testing.

| Name         | Description                         | Type        |
| ------------ | ----------------------------------- | ----------- |
| ssl_certfile | Path to self signed ssl certificate | Path String |
| ssl_keyfile  | Path to certificate key file        | Path String |

## Commandline interface (CLI)

OpenPostbud adds a command line executable called `OpenPostbud`.
Use `OpenPostbud -h` to see help information about the CLI.

## Database

OpenPostbud uses SQLite and it creates an SQLite database in the current working directory called `database.db`.

Some sensitive columns in the database are encrypted using AES.

## Authentication

The OpenPostbud web app uses Microsoft OIDC to authenticate users. This needs to be set up in Microsoft Entra.

Admins can use the CLI command `OpenPostbud admin_access` to get a single-use login URL.
