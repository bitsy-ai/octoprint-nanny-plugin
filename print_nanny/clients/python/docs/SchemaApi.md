# print_nanny_client.SchemaApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schema_retrieve**](SchemaApi.md#schema_retrieve) | **GET** /api/schema/ | 


# **schema_retrieve**
> {str: (bool, date, datetime, dict, float, int, list, str, none_type)} schema_retrieve()



OpenApi3 schema for this API. Format can be selected via content negotiation.  - YAML: application/vnd.oai.openapi - JSON: application/vnd.oai.openapi+json

### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import schema_api
from pprint import pprint
# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = print_nanny_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: cookieAuth
configuration.api_key['cookieAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['cookieAuth'] = 'Bearer'

# Configure Bearer authorization (Bearer): tokenAuth
configuration = print_nanny_client.Configuration(
    access_token = 'YOUR_BEARER_TOKEN'
)

# Enter a context with an instance of the API client
with print_nanny_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = schema_api.SchemaApi(api_client)
    lang = "af" # str |  (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.schema_retrieve(lang=lang)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling SchemaApi->schema_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **lang** | **str**|  | [optional]

### Return type

**{str: (bool, date, datetime, dict, float, int, list, str, none_type)}**

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.oai.openapi+json, application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

