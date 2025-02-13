#
# Sample console application that demonstrates how to sign in to an Azure Container Apps application using
# the device code flow with an Entra External ID tenant.
#
# You should insert your own values for the following variables in `config.py`:
# - CLIENT_ID: The Application (client) ID of the console app registration
# - API_CLIENT_ID: The Application (client) ID of the API app registration
# - TENANT_SUBDOMAIN: The subdomain of the External ID tenant
# - API_URL: The URL of the API app hosted in Azure Container Apps
#

import json
import sys

import msal
import requests

from .config import config


#
# To sign in via device code flow we have to:
# 1. Get an access token from Entra External ID
# 2. Present that token for validation to Easy Auth
#    (https://learn.microsoft.com/en-us/azure/container-apps/authentication#client-directed-sign-in). If
#    the token is valid, Easy Auth will return an `authenticationToken` that we can use to call our API.
# 3. Call our API at /generate_name with the `X-ZUMO-AUTH` header set to the `authenticationToken` we received in step 2
#
def main(config):
    app = msal.PublicClientApplication(config["CLIENT_ID"], authority=construct_authority(config["TENANT_SUBDOMAIN"]))

    access_token = get_access_token_device_code(app, f"api://{config['API_CLIENT_ID']}/user_impersonation")

    authentication_token = get_authentication_token(config["API_URL"], access_token)

    if authentication_token:
        name = generate_name(config["API_URL"], authentication_token)
        print(f"Generated name: {name}")
    else:
        print("Failed to get authentication token")


#
# Call our API Endpoint hosted in Azure Container Apps using the authentication token
#
def generate_name(api_root, auth_token):
    response = requests.get(f"{api_root}/generate_name", headers={"X-ZUMO-AUTH": auth_token})

    if response.ok:
        return response.json()["name"]
    else:
        response.raise_for_status()


#
# Get an access token using the device code flow
#   - As External ID does not correctly return a device login URL, we have to construct it manually
#
def get_access_token_device_code(app, scope):

    flow = app.initiate_device_flow(scopes=[scope])
    if "user_code" not in flow:
        raise ValueError(f"Fail to create device flow. Err: {json.dumps(flow, indent=4)}")

    devicelogin_url = construct_devicelogin(app.authority)
    print(
        f"To sign in, use a web browser to open the page {devicelogin_url} and "
        f"enter the code {flow['user_code']} to authenticate"
    )
    sys.stdout.flush()

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        return result["access_token"]
    else:
        raise ValueError(f"Fail to sign in via device flow. Err: {result.get('error')}")


#
# Given an access token with has the appropriate scope to access the application, get
# an authentication token from Easy Auth
#
# https://learn.microsoft.com/en-us/azure/container-apps/authentication#client-directed-sign-in
#
def get_authentication_token(api_root, access_token):
    body = {"access_token": access_token}
    validation_uri = f"{api_root}/.auth/login/aad"

    response = requests.post(validation_uri, json=body)

    if response.ok:
        return response.json()["authenticationToken"]
    else:
        response.raise_for_status()


def construct_authority(subdomain):
    return f"https://{subdomain}.ciamlogin.com/{subdomain}.onmicrosoft.com"


#
# For External ID, the devicelogin endpoint returned during the device code flow is wrong!
# We have to construct it manually.  It's the same as the authority endpoint, but with the last segments of the path
# changed from `v2.0/authorize` to `deviceauth`.
def construct_devicelogin(authority):
    return authority.authorization_endpoint.replace("v2.0/authorize", "deviceauth")


if __name__ == "__main__":
    main(config)
