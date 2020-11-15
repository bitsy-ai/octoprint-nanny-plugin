# print_nanny_client.GcodeFilesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**gcode_files_create**](GcodeFilesApi.md#gcode_files_create) | **POST** /api/gcode_files/ | 
[**gcode_files_list**](GcodeFilesApi.md#gcode_files_list) | **GET** /api/gcode_files/ | 
[**gcode_files_partial_update**](GcodeFilesApi.md#gcode_files_partial_update) | **PATCH** /api/gcode_files/{id}/ | 
[**gcode_files_retrieve**](GcodeFilesApi.md#gcode_files_retrieve) | **GET** /api/gcode_files/{id}/ | 
[**gcode_files_update**](GcodeFilesApi.md#gcode_files_update) | **PUT** /api/gcode_files/{id}/ | 
[**gcode_files_update_or_create**](GcodeFilesApi.md#gcode_files_update_or_create) | **POST** /api/gcode_files/update_or_create/ | 


# **gcode_files_create**
> GcodeFile gcode_files_create(name, file, file_hash)



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
    name = "name_example" # str | 
    file = open('/path/to/file', 'rb') # file_type | 
    file_hash = "file_hash_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_create(name, file, file_hash)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  |
 **file** | **file_type**|  |
 **file_hash** | **str**|  |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_list**
> PaginatedGcodeFileList gcode_files_list()



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import gcode_files_api
from print_nanny_client.model.paginated_gcode_file_list import PaginatedGcodeFileList
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
    limit = 1 # int | Number of results to return per page. (optional)
    offset = 1 # int | The initial index from which to return the results. (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.gcode_files_list(limit=limit, offset=offset)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional]
 **offset** | **int**| The initial index from which to return the results. | [optional]

### Return type

[**PaginatedGcodeFileList**](PaginatedGcodeFileList.md)

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
    name = "name_example" # str |  (optional)
    file = open('/path/to/file', 'rb') # file_type |  (optional)
    file_hash = "file_hash_example" # str |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_partial_update(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_partial_update: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.gcode_files_partial_update(id, name=name, file=file, file_hash=file_hash)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. |
 **name** | **str**|  | [optional]
 **file** | **file_type**|  | [optional]
 **file_hash** | **str**|  | [optional]

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
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
> GcodeFile gcode_files_update(id, name, file, file_hash)



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
    name = "name_example" # str | 
    file = open('/path/to/file', 'rb') # file_type | 
    file_hash = "file_hash_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_update(id, name, file, file_hash)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. |
 **name** | **str**|  |
 **file** | **file_type**|  |
 **file_hash** | **str**|  |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_update_or_create**
> GcodeFile gcode_files_update_or_create(name, file, file_hash)



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
    name = "name_example" # str | 
    file = open('/path/to/file', 'rb') # file_type | 
    file_hash = "file_hash_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.gcode_files_update_or_create(name, file, file_hash)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling GcodeFilesApi->gcode_files_update_or_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  |
 **file** | **file_type**|  |
 **file_hash** | **str**|  |

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**202** |  |  -  |
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

