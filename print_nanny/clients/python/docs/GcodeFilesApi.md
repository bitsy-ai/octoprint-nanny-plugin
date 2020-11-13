# print_nanny_client.GcodeFilesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**gcode_files_create**](GcodeFilesApi.md#gcode_files_create) | **POST** /api/gcode_files/ | 
[**gcode_files_list**](GcodeFilesApi.md#gcode_files_list) | **GET** /api/gcode_files/ | 
[**gcode_files_partial_update**](GcodeFilesApi.md#gcode_files_partial_update) | **PATCH** /api/gcode_files/{id}/ | 
[**gcode_files_retrieve**](GcodeFilesApi.md#gcode_files_retrieve) | **GET** /api/gcode_files/{id}/ | 
[**gcode_files_update**](GcodeFilesApi.md#gcode_files_update) | **PUT** /api/gcode_files/{id}/ | 


# **gcode_files_create**
> GcodeFile gcode_files_create(gcode_file_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.gcode_file import GcodeFile
from print_nanny_client.model.gcode_file_request import GcodeFileRequest
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
    api_instance = gcode_files_api.GcodeFilesApi(api_client)
    gcode_file_request = GcodeFileRequest(
        name="name_example",
        file=open('/path/to/file', 'rb'),
        file_hash="file_hash_example",
        user=1,
    ) # GcodeFileRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_create(gcode_file_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **gcode_file_request** | [**GcodeFileRequest**](GcodeFileRequest.md)|  |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_list**
> [GcodeFile] gcode_files_list()



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.gcode_file import GcodeFile
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
    api_instance = gcode_files_api.GcodeFilesApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        api_response = api_instance.gcode_files_list()
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_list: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**[GcodeFile]**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_partial_update**
> GcodeFile gcode_files_partial_update(id)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.patched_gcode_file_request import PatchedGcodeFileRequest
from print_nanny_client.model.gcode_file import GcodeFile
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
    api_instance = gcode_files_api.GcodeFilesApi(api_client)
    id = 1 # int | A unique integer value identifying this gcode file.
    patched_gcode_file_request = PatchedGcodeFileRequest(
        name="name_example",
        file=open('/path/to/file', 'rb'),
        file_hash="file_hash_example",
        user=1,
    ) # PatchedGcodeFileRequest |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_partial_update(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_partial_update: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.gcode_files_partial_update(id, patched_gcode_file_request=patched_gcode_file_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. |
 **patched_gcode_file_request** | [**PatchedGcodeFileRequest**](PatchedGcodeFileRequest.md)|  | [optional]

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_retrieve**
> GcodeFile gcode_files_retrieve(id)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.gcode_file import GcodeFile
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
    api_instance = gcode_files_api.GcodeFilesApi(api_client)
    id = 1 # int | A unique integer value identifying this gcode file.

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_retrieve(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_update**
> GcodeFile gcode_files_update(id, gcode_file_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.gcode_file import GcodeFile
from print_nanny_client.model.gcode_file_request import GcodeFileRequest
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
    api_instance = gcode_files_api.GcodeFilesApi(api_client)
    id = 1 # int | A unique integer value identifying this gcode file.
    gcode_file_request = GcodeFileRequest(
        name="name_example",
        file=open('/path/to/file', 'rb'),
        file_hash="file_hash_example",
        user=1,
    ) # GcodeFileRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_update(id, gcode_file_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. |
 **gcode_file_request** | [**GcodeFileRequest**](GcodeFileRequest.md)|  |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

