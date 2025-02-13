# Sample App - Authorization to an API endpoint for a console application using External ID


This repository includes a simple Python FastAPI app with a single route (`/generate_name`) that returns JSON. The application is deployed to Azure Container Apps and uses App Services built-in Authentication to secure the endpoint using Microsoft Entra External ID.

It also contains a sample CLI application which shows how to access the application as a signed-in user from the command line, using Device Code flow to sign-in.


## Opening the project

This project has [Dev Container support](https://code.visualstudio.com/docs/devcontainers/containers), so it will be be setup automatically if you open it in Github Codespaces or in local VS Code with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

### Authentication configuration

You will create two application registations in Entra External ID, one for the API running in Azure Container Apps and one for the Console application. As part of this, you will grant permissions on the Console application to access the backend API.

You can follow the instructions in [Azure Container Apps documentation](https://learn.microsoft.com/en-us/azure/container-apps/authentication-entra) as follows:

1. Create an app registration for the container app using ['Option 2: Use an existing registration created separately'](https://learn.microsoft.com/en-us/azure/container-apps/authentication-entra#-option-2-use-an-existing-registration-created-separately). At this stage, you don't need to add the Redirect URL mentioned in step 5 iv - we'll fill that in after deployment of our application. You can use `http://localhost` as a placeholder.

    Note down the `client ID` and `client secret` and you'll need them when deploying the application.

 2. Create a app registration for the console CLI application using ['Configure client apps to access your container app -Native client application'](https://learn.microsoft.com/en-us/azure/container-apps/authentication-entra#native-client-application). At this stage, you don't need to add the Redirect URL mentioned in step 3  - we'll fill that in after deployment of our application. You can use `http://localhost` as a placeholder.

    Again, note down the `client id` of this  application as you'll need this when configuring the CLI application.

### Deployment

This repo is set up for deployment on Azure Container Apps using the configuration files in the `infra` folder.

This diagram shows the architecture of the deployment:

![Diagram of app architecture: Azure Container Apps environment, Azure Container App, Azure Container Registry, Container, and Key Vault](docs/readme_arch_diagram.png)

Steps for deployment:

1. Sign up for a [free Azure account](https://azure.microsoft.com/free/) and create an Azure Subscription.
2. Install the [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd). (If you open this repository in Codespaces or with the VS Code Dev Containers extension, that part will be done for you.)
3. Login to Azure:

    ```shell
    azd auth login
    ```

4. Provision and deploy all the resources:

    ```shell
    azd up
    ```

    It will prompt you to provide an `azd` environment name (like "fastapi-app"), select a subscription from your Azure account, and select a location (like "eastus").

    You will be prompted for the following configuration information:

    * `authTenantId`: The Tenant ID of the External ID tenant.
    * `authTenantSubdomain`: The subdomain of the External ID tenant (This is the portion of the primary domain before the .onmicrosoft.com part, e.g. mytenant).
    * `authClientId` : The Client ID of the External ID app for the API.
    * `authClientSecret` : The Client Secret of the External ID app for the API.

    Then it will provision the resources in your account and deploy the latest code. If you get an error with deployment, changing the location can help, as there may be availability constraints for some of the resources.

5. When `azd` has finished deploying, you'll see an endpoint URI in the command output. You should now add a redirect URI to both application registrations  of the form `<endpoint-uri>/.auth/login/aad/callback`. For example, `https://<hostname>.<region>.azurecontainerapps.io/.auth/login/aad/callback`.

6. Update the configuration of the CLI client by modifying `cli/config.py` with your configuration details.

7. Run the CLI application

   ```shell
   uv run -m cli.main
   ```

### Local development with Docker

You can also run this app with Docker, thanks to the `Dockerfile`.

You need to either have Docker Desktop installed or have this open in Github Codespaces for these commands to work. ⚠️ If you're on an Apple M1/M2, you won't be able to run `docker` commands inside a Dev Container; either use Codespaces or do not open the Dev Container.

1. Build the image:

    ```shell
    docker build --tag fastapi-app ./src
    ```

2. Run the image:

    ```shell
    docker run --publish 3100:3100 fastapi-app
    ```


3. Click 'http://127.0.0.1:3100' in the terminal, which should open a new tab in the browser.

4. Try the API at '/generate_name' and try passing in a parameter at the end of the URL, like '/generate_name?starts_with=N'.

### Costs

Pricing varies per region and usage, so it isn't possible to predict exact costs for your usage.
The majority of the Azure resources used in this infrastructure are on usage-based pricing tiers.
However, Azure Container Registry has a fixed cost per registry per day.

You can try the [Azure pricing calculator](https://azure.com/e/9f8185b239d240b398e201078d0c4e7a) for the resources:

- Azure Container App: Consumption tier with 0.5 CPU, 1GiB memory/storage. Pricing is based on resource allocation, and each month allows for a certain amount of free usage. [Pricing](https://azure.microsoft.com/pricing/details/container-apps/)
- Azure Container Registry: Basic tier. [Pricing](https://azure.microsoft.com/pricing/details/container-registry/)
- Log analytics: Pay-as-you-go tier. Costs based on data ingested. [Pricing](https://azure.microsoft.com/pricing/details/monitor/)

⚠️ To avoid unnecessary costs, remember to take down your app if it's no longer in use,
either by deleting the resource group in the Portal or running `azd down`.


## Getting help

If you're working with this project and running into issues, please post in **Discussions**.
