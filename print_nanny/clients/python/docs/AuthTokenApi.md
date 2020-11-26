# print_nanny_client.AuthTokenApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**auth_token_create**](AuthTokenApi.md#auth_token_create) | **POST** /api/auth-token/ | 


# **auth_token_create**
> AuthToken auth_token_create(username, password)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.AuthTokenApi(print_nanny_client.ApiClient(configuration))
username = 'username_example' # str | 
password = 'password_example' # str | 

try:
    api_response = api_instance.auth_token_create(username, password)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AuthTokenApi->auth_token_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.AuthTokenApi(print_nanny_client.ApiClient(configuration))
username = 'username_example' # str | 
password = 'password_example' # str | 

try:
    api_response = api_instance.auth_token_create(username, password)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AuthTokenApi->auth_token_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **str**|  |
 **password** | **str**|  |

### Return type

[**AuthToken**](AuthToken.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/x-www-form-urlencoded, multipart/form-data, application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

