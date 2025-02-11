param name string
param location string = resourceGroup().location
param tags object = {}

param identityName string
param containerAppsEnvironmentName string
param containerRegistryName string
param serviceName string = 'api'
param exists bool
param azureKeyVaultName string

param authClientId string
@secure()
param authClientSecret string
param authClientSecretName string
param authTenantId string
param authTenantSubdomain string

var openIdIssuer = 'https://${authTenantSubdomain}.ciamlogin.com/${authTenantId}/v2.0'

resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' existing = {
  name: azureKeyVaultName
}

resource apiIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}

module webKVAccess 'core/security/keyvault-access.bicep' = {
  name: '${serviceName}-keyvault-access'
  params: {
    keyVaultName: keyVault.name
    principalId: apiIdentity.properties.principalId
  }
}

module authClientSecretStorage 'core/security/keyvault-secret.bicep' = if (!empty(authClientSecret)) {
  name: 'secrets'
  params: {
    keyVaultName: azureKeyVaultName
    name: authClientSecretName
    secretValue: authClientSecret
  }
}

module app 'core/host/container-app-upsert.bicep' = {
  name: '${serviceName}-container-app-module'
  params: {
    name: name
    location: location
    tags: union(tags, { 'azd-service-name': serviceName })
    identityName: apiIdentity.name
    exists: exists
    containerAppsEnvironmentName: containerAppsEnvironmentName
    containerRegistryName: containerRegistryName
    targetPort: 3100
    keyvaultIdentities: {
      'microsoft-provider-authentication-secret': {
        keyVaultUrl: '${keyVault.properties.vaultUri}secrets/${authClientSecretName}'
        identity: apiIdentity.id
      }
    }
  }
  dependsOn: [
    webKVAccess
  ]
}

module auth 'app/container-apps-auth.bicep' = {
  name: '${serviceName}-container-apps-auth-module'
  params: {
    name: app.outputs.name
    clientId: authClientId
    clientSecretName: 'microsoft-provider-authentication-secret'
    openIdIssuer: openIdIssuer
  }
}

output SERVICE_API_IDENTITY_PRINCIPAL_ID string = apiIdentity.properties.principalId
output SERVICE_API_NAME string = app.outputs.name
output SERVICE_API_URI string = app.outputs.uri
output SERVICE_API_IMAGE_NAME string = app.outputs.imageName
