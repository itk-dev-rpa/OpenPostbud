# OpenPostbud

## Introduction

OpenPostbud is a web application that makes it possible to do mail merge and mass shipment of mail
using Kombit's Serviceplatformen.

A shipment can be sent in one of three ways, chosen by the user when the shipment is created:

- **Digital Post**: Sent as Digital Post. Recipients not registered for Digital Post are marked as failed.
- **Fysisk Post**: Sent as physical mail (Fjernprint). The recipient's address must be printed in the
  letter itself so it is visible through the window of the envelope.
- **Digital med fysisk fallback**: Sent as Digital Post if the recipient is registered for it, otherwise
  sent as physical mail. The channel each individual letter was sent through is recorded and shown in the UI.

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

| Name                           | description                                                                | Type                    | Default |
| ------------------------------ | -------------------------------------------------------------------------- | ----------------------- | ------- |
| nicegui_storage_secret         | The secret used to store user session tokens                               | String                  |         |
| database_storage_secret        | The encryption key used to encrypt database columns                        | A valid 128-bit AES key |         |
| client_id                      | OIDC client id                                                             | String                  |         |
| client_secret                  | OIDC client secret                                                         | String                  |         |
| discovery_url                  | OIDC discovery url                                                         | URL                     |         |
| redirect_url                   | OIDC redirect url                                                          | URL                     |         |
| auth_lifetime_seconds          | How long a user session is valid                                           | integer                 |         |
| shipment_lifetime_days         | How long a shipment should be kept in the database after creation          | integer                 |         |
| registration_job_lifetime_days | How long a registration task should be kept in the database after creation | integer                 |         |
| app_reload                     | Whether the app should reload on code changes                              | boolean                 | False   |

### Workers

The shipment, registration and message broker workers need the following environment variables set:

| Name                             | description                                                               | Type        | Default |
| -------------------------------- | ------------------------------------------------------------------------- | ----------- | ------- |
| cvr                              | The CVR number of the organisation                                        | String      |         |
| kombit_cert_path                 | The absolute path to the certificate file used for Service Platformen     | Path string |         |
| Kombit_test_env                  | Whether to use the test environment of Service Platformen                 | boolean     |         |
| registration_worker_sleep_time   | The number of seconds for the registration worker to idle                 | Integer     |         |
| shipment_worker_sleep_time       | The number of seconds for the shipment worker to idle                     | Integer     |         |
| shipment_worker_delay            | The number of seconds to wait before a new shipment is processed          | Integer     | 300     |
| sender_label                     | The label to set on the sender of Digital Post                            | String      |         |
| physical_mail_forsendelse_type   | The forsendelsestype id agreed with the print provider (Fjernprint)       | Integer     |         |
| message_broker_queue_id          | The UUID of the message broker queue. Get this from the Kombit admin page | UUID        |         |
| message_broker_worker_sleep_time | The number of seconds for the message broker worker to idle               | Integer     |         |

### API

| Name                       | description                                            | Type    | Default |
| -------------------------- | ------------------------------------------------------ | ------- | ------- |
| api_jwt_secret             | Secret for signing JWT auth tokens                     | String  |         |
| api_token_lifetime_seconds | The number of seconds for a JWT auth token to be valid | Integer | 3600    |

## Commandline interface (CLI)

OpenPostbud adds a command line executable called `OpenPostbud`.
Use `OpenPostbud -h` to see help information about the CLI.

## Database

OpenPostbud uses SQLite and it creates an SQLite database in the current working directory called `database.db`.

Some sensitive columns in the database are encrypted using AES.

## Authentication

The OpenPostbud web app uses OIDC to authenticate users.

Admins can use the CLI command `OpenPostbud admin_access` to get a single-use login URL.

## Development

### Database migrations

If you need to alter the database schema when developing a new feature you need to add a migration step to the automatic
migration tool. Migration files are located in `src\OpenPostbud\database\migrations\sql`. Please name your new migration
file `XXX_Descriptive_name.sql` where 'XXX' is replaced by the next number in the sequence.
The migration file should only contain valid sql statements. Multiple statements are separated by two blank lines.

Please don't change existing migration files as this will break existing server setups. The migration tool keeps
a checksum of every migration file to avoid database drift.

Migrations are automatically applied when the Docker compose file is run.
