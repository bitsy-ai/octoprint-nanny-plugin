# print_nanny_client.RemoteControlApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**gcode_files_create**](RemoteControlApi.md#gcode_files_create) | **POST** /api/gcode-files/ | 
[**gcode_files_list**](RemoteControlApi.md#gcode_files_list) | **GET** /api/gcode-files/ | 
[**gcode_files_partial_update**](RemoteControlApi.md#gcode_files_partial_update) | **PATCH** /api/gcode-files/{id}/ | 
[**gcode_files_retrieve**](RemoteControlApi.md#gcode_files_retrieve) | **GET** /api/gcode-files/{id}/ | 
[**gcode_files_update**](RemoteControlApi.md#gcode_files_update) | **PUT** /api/gcode-files/{id}/ | 
[**gcode_files_update_or_create**](RemoteControlApi.md#gcode_files_update_or_create) | **POST** /api/gcode-files/update_or_create/ | 
[**print_jobs_create**](RemoteControlApi.md#print_jobs_create) | **POST** /api/print-jobs/ | 
[**print_jobs_list**](RemoteControlApi.md#print_jobs_list) | **GET** /api/print-jobs/ | 
[**print_jobs_partial_update**](RemoteControlApi.md#print_jobs_partial_update) | **PATCH** /api/print-jobs/{id}/ | 
[**print_jobs_retrieve**](RemoteControlApi.md#print_jobs_retrieve) | **GET** /api/print-jobs/{id}/ | 
[**print_jobs_update**](RemoteControlApi.md#print_jobs_update) | **PUT** /api/print-jobs/{id}/ | 
[**printer_profiles_create**](RemoteControlApi.md#printer_profiles_create) | **POST** /api/printer-profiles/ | 
[**printer_profiles_list**](RemoteControlApi.md#printer_profiles_list) | **GET** /api/printer-profiles/ | 
[**printer_profiles_partial_update**](RemoteControlApi.md#printer_profiles_partial_update) | **PATCH** /api/printer-profiles/{id}/ | 
[**printer_profiles_retrieve**](RemoteControlApi.md#printer_profiles_retrieve) | **GET** /api/printer-profiles/{id}/ | 
[**printer_profiles_update**](RemoteControlApi.md#printer_profiles_update) | **PUT** /api/printer-profiles/{id}/ | 
[**printer_profiles_update_or_create**](RemoteControlApi.md#printer_profiles_update_or_create) | **POST** /api/printer-profiles/update_or_create/ | 


# **gcode_files_create**
> PrintJob gcode_files_create(name, file, file_hash)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_create(name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_create(name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  | 
 **file** | **file**|  | 
 **file_hash** | **str**|  | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_list**
> PaginatedGcodeFileList gcode_files_list(limit=limit, offset=offset)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

    try:
        api_response = api_instance.gcode_files_list(limit=limit, offset=offset)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_list: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

    try:
        api_response = api_instance.gcode_files_list(limit=limit, offset=offset)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_list: %s\n" % e)
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
> GcodeFile gcode_files_partial_update(id, name=name, file=file, file_hash=file_hash)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.
name = 'name_example' # str |  (optional)
file = '/path/to/file' # file |  (optional)
file_hash = 'file_hash_example' # str |  (optional)

    try:
        api_response = api_instance.gcode_files_partial_update(id, name=name, file=file, file_hash=file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_partial_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.
name = 'name_example' # str |  (optional)
file = '/path/to/file' # file |  (optional)
file_hash = 'file_hash_example' # str |  (optional)

    try:
        api_response = api_instance.gcode_files_partial_update(id, name=name, file=file, file_hash=file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. | 
 **name** | **str**|  | [optional] 
 **file** | **file**|  | [optional] 
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
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.

    try:
        api_response = api_instance.gcode_files_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_retrieve: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.

    try:
        api_response = api_instance.gcode_files_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_retrieve: %s\n" % e)
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
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.
name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_update(id, name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this gcode file.
name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_update(id, name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. | 
 **name** | **str**|  | 
 **file** | **file**|  | 
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
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_update_or_create(name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_update_or_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    name = 'name_example' # str | 
file = '/path/to/file' # file | 
file_hash = 'file_hash_example' # str | 

    try:
        api_response = api_instance.gcode_files_update_or_create(name, file, file_hash)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->gcode_files_update_or_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name** | **str**|  | 
 **file** | **file**|  | 
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
**200** |  |  -  |
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_create**
> PrintJob print_jobs_create(print_job_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    print_job_request = print_nanny_client.PrintJobRequest() # PrintJobRequest | 

    try:
        api_response = api_instance.print_jobs_create(print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    print_job_request = print_nanny_client.PrintJobRequest() # PrintJobRequest | 

    try:
        api_response = api_instance.print_jobs_create(print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **print_job_request** | [**PrintJobRequest**](PrintJobRequest.md)|  | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** |  |  -  |
**400** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_list**
> PaginatedPrintJobList print_jobs_list(limit=limit, offset=offset)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

    try:
        api_response = api_instance.print_jobs_list(limit=limit, offset=offset)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_list: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

    try:
        api_response = api_instance.print_jobs_list(limit=limit, offset=offset)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional] 
 **offset** | **int**| The initial index from which to return the results. | [optional] 

### Return type

[**PaginatedPrintJobList**](PaginatedPrintJobList.md)

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

# **print_jobs_partial_update**
> PrintJob print_jobs_partial_update(id, patched_print_job_request=patched_print_job_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.
patched_print_job_request = print_nanny_client.PatchedPrintJobRequest() # PatchedPrintJobRequest |  (optional)

    try:
        api_response = api_instance.print_jobs_partial_update(id, patched_print_job_request=patched_print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_partial_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.
patched_print_job_request = print_nanny_client.PatchedPrintJobRequest() # PatchedPrintJobRequest |  (optional)

    try:
        api_response = api_instance.print_jobs_partial_update(id, patched_print_job_request=patched_print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this print job. | 
 **patched_print_job_request** | [**PatchedPrintJobRequest**](PatchedPrintJobRequest.md)|  | [optional] 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_retrieve**
> PrintJob print_jobs_retrieve(id)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.

    try:
        api_response = api_instance.print_jobs_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_retrieve: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.

    try:
        api_response = api_instance.print_jobs_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this print job. | 

### Return type

[**PrintJob**](PrintJob.md)

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

# **print_jobs_update**
> PrintJob print_jobs_update(id, print_job_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.
print_job_request = print_nanny_client.PrintJobRequest() # PrintJobRequest | 

    try:
        api_response = api_instance.print_jobs_update(id, print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this print job.
print_job_request = print_nanny_client.PrintJobRequest() # PrintJobRequest | 

    try:
        api_response = api_instance.print_jobs_update(id, print_job_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->print_jobs_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this print job. | 
 **print_job_request** | [**PrintJobRequest**](PrintJobRequest.md)|  | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_create**
> PrintJob printer_profiles_create(printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_create(printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_create(printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **printer_profile_request** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_list**
> PaginatedPrinterProfileList printer_profiles_list(limit=limit, name=name, offset=offset, user=user)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
name = 'name_example' # str | name (optional)
offset = 56 # int | The initial index from which to return the results. (optional)
user = 'user_example' # str | user (optional)

    try:
        api_response = api_instance.printer_profiles_list(limit=limit, name=name, offset=offset, user=user)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_list: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    limit = 56 # int | Number of results to return per page. (optional)
name = 'name_example' # str | name (optional)
offset = 56 # int | The initial index from which to return the results. (optional)
user = 'user_example' # str | user (optional)

    try:
        api_response = api_instance.printer_profiles_list(limit=limit, name=name, offset=offset, user=user)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional] 
 **name** | **str**| name | [optional] 
 **offset** | **int**| The initial index from which to return the results. | [optional] 
 **user** | **str**| user | [optional] 

### Return type

[**PaginatedPrinterProfileList**](PaginatedPrinterProfileList.md)

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

# **printer_profiles_partial_update**
> PrinterProfile printer_profiles_partial_update(id, patched_printer_profile_request=patched_printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.
patched_printer_profile_request = print_nanny_client.PatchedPrinterProfileRequest() # PatchedPrinterProfileRequest |  (optional)

    try:
        api_response = api_instance.printer_profiles_partial_update(id, patched_printer_profile_request=patched_printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_partial_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.
patched_printer_profile_request = print_nanny_client.PatchedPrinterProfileRequest() # PatchedPrinterProfileRequest |  (optional)

    try:
        api_response = api_instance.printer_profiles_partial_update(id, patched_printer_profile_request=patched_printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this printer profile. | 
 **patched_printer_profile_request** | [**PatchedPrinterProfileRequest**](PatchedPrinterProfileRequest.md)|  | [optional] 

### Return type

[**PrinterProfile**](PrinterProfile.md)

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

# **printer_profiles_retrieve**
> PrinterProfile printer_profiles_retrieve(id)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.

    try:
        api_response = api_instance.printer_profiles_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_retrieve: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.

    try:
        api_response = api_instance.printer_profiles_retrieve(id)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this printer profile. | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

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

# **printer_profiles_update**
> PrinterProfile printer_profiles_update(id, printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.
printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_update(id, printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    id = 56 # int | A unique integer value identifying this printer profile.
printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_update(id, printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this printer profile. | 
 **printer_profile_request** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

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

# **printer_profiles_update_or_create**
> PrinterProfile printer_profiles_update_or_create(printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_update_or_create(printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_update_or_create: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
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
    api_instance = print_nanny_client.RemoteControlApi(api_client)
    printer_profile_request = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 

    try:
        api_response = api_instance.printer_profiles_update_or_create(printer_profile_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling RemoteControlApi->printer_profiles_update_or_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **printer_profile_request** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**400** |  |  -  |
**200** |  |  -  |
**201** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

