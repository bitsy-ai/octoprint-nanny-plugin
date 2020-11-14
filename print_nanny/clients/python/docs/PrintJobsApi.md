# print_nanny_client.PrintJobsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**print_jobs_create**](PrintJobsApi.md#print_jobs_create) | **POST** /api/print_jobs/ | 
[**print_jobs_list**](PrintJobsApi.md#print_jobs_list) | **GET** /api/print_jobs/ | 
[**print_jobs_partial_update**](PrintJobsApi.md#print_jobs_partial_update) | **PATCH** /api/print_jobs/{id}/ | 
[**print_jobs_retrieve**](PrintJobsApi.md#print_jobs_retrieve) | **GET** /api/print_jobs/{id}/ | 
[**print_jobs_update**](PrintJobsApi.md#print_jobs_update) | **PUT** /api/print_jobs/{id}/ | 


# **print_jobs_create**
> PrintJob print_jobs_create(print_job_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import print_jobs_api
from print_nanny_client.model.print_job import PrintJob
from print_nanny_client.model.print_job_request import PrintJobRequest
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
    api_instance = print_jobs_api.PrintJobsApi(api_client)
    print_job_request = PrintJobRequest(
        dt=dateutil_parser('1970-01-01T00:00:00.00Z'),
        name="name_example",
        gcode_file_hash="gcode_file_hash_example",
        printer_profile=1,
        gcode_file=1,
    ) # PrintJobRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.print_jobs_create(print_job_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_create: %s\n" % e)
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
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_list**
> [PrintJob] print_jobs_list()



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import print_jobs_api
from print_nanny_client.model.print_job import PrintJob
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
    api_instance = print_jobs_api.PrintJobsApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        api_response = api_instance.print_jobs_list()
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_list: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**[PrintJob]**](PrintJob.md)

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
> PrintJob print_jobs_partial_update(id)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import print_jobs_api
from print_nanny_client.model.print_job import PrintJob
from print_nanny_client.model.patched_print_job_request import PatchedPrintJobRequest
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
    api_instance = print_jobs_api.PrintJobsApi(api_client)
    id = 1 # int | A unique integer value identifying this print job.
    patched_print_job_request = PatchedPrintJobRequest(
        dt=dateutil_parser('1970-01-01T00:00:00.00Z'),
        name="name_example",
        gcode_file_hash="gcode_file_hash_example",
        printer_profile=1,
        gcode_file=1,
    ) # PatchedPrintJobRequest |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.print_jobs_partial_update(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_partial_update: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.print_jobs_partial_update(id, patched_print_job_request=patched_print_job_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_partial_update: %s\n" % e)
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
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_retrieve**
> PrintJob print_jobs_retrieve(id)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import print_jobs_api
from print_nanny_client.model.print_job import PrintJob
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
    api_instance = print_jobs_api.PrintJobsApi(api_client)
    id = 1 # int | A unique integer value identifying this print job.

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.print_jobs_retrieve(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_retrieve: %s\n" % e)
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
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import print_jobs_api
from print_nanny_client.model.print_job import PrintJob
from print_nanny_client.model.print_job_request import PrintJobRequest
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
    api_instance = print_jobs_api.PrintJobsApi(api_client)
    id = 1 # int | A unique integer value identifying this print job.
    print_job_request = PrintJobRequest(
        dt=dateutil_parser('1970-01-01T00:00:00.00Z'),
        name="name_example",
        gcode_file_hash="gcode_file_hash_example",
        printer_profile=1,
        gcode_file=1,
    ) # PrintJobRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.print_jobs_update(id, print_job_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrintJobsApi->print_jobs_update: %s\n" % e)
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
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

