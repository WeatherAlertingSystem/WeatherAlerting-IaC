# WeatherAlerting-IaC

## Prerequisites
1. Install [Pulumi](https://www.pulumi.com/docs/get-started/install/)
2. Install [Poetry](https://python-poetry.org/docs/#installation)
3. Configure [AWS cli](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) - `aws configure`
4. Install [pre-commit](https://pre-commit.com/#installation)

## How to work with this project?
1. Install git hook scripts for `precommit`
    ```
    pre-commit install
    ```
2. Install needed python packages
    ```
    poetry install
    ```
3. Login to pulumi state
    ```
    source ./scripts/pulumi-state-login.sh
    ```
4. Create or update the AWS resources in a pulumi stack
    ```
    pulumi up
    ```
