# print_nanny_client.EventsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**events_octoprint_create**](EventsApi.md#events_octoprint_create) | **POST** /api/events/octoprint/ | 
[**events_predict_create**](EventsApi.md#events_predict_create) | **POST** /api/events/predict/ | 


# **events_octoprint_create**
> OctoPrintEvent events_octoprint_create(octo_print_event_request)



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
    api_instance = print_nanny_client.EventsApi(api_client)
    octo_print_event_request = print_nanny_client.OctoPrintEventRequest() # OctoPrintEventRequest | 

    try:
        api_response = api_instance.events_octoprint_create(octo_print_event_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling EventsApi->events_octoprint_create: %s\n" % e)
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
    api_instance = print_nanny_client.EventsApi(api_client)
    octo_print_event_request = print_nanny_client.OctoPrintEventRequest() # OctoPrintEventRequest | 

    try:
        api_response = api_instance.events_octoprint_create(octo_print_event_request)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling EventsApi->events_octoprint_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **octo_print_event_request** | [**OctoPrintEventRequest**](OctoPrintEventRequest.md)|  | 

### Return type

[**OctoPrintEvent**](OctoPrintEvent.md)

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

# **events_predict_create**
> PredictEvent events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job=print_job)



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
    api_instance = print_nanny_client.EventsApi(api_client)
    dt = '2013-10-20T19:20:30+01:00' # datetime | 
original_image = '/path/to/file' # file | 
annotated_image = '/path/to/file' # file | 
event_data = 'event_data_example' # str | 
plugin_version = 'plugin_version_example' # str | 
octoprint_version = 'octoprint_version_example' # str | 
print_job = 56 # int |  (optional)

    try:
        api_response = api_instance.events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job=print_job)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling EventsApi->events_predict_create: %s\n" % e)
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
    api_instance = print_nanny_client.EventsApi(api_client)
    dt = '2013-10-20T19:20:30+01:00' # datetime | 
original_image = '/path/to/file' # file | 
annotated_image = '/path/to/file' # file | 
event_data = 'event_data_example' # str | 
plugin_version = 'plugin_version_example' # str | 
octoprint_version = 'octoprint_version_example' # str | 
print_job = 56 # int |  (optional)

    try:
        api_response = api_instance.events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job=print_job)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling EventsApi->events_predict_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dt** | **datetime**|  | 
 **original_image** | **file**|  | 
 **annotated_image** | **file**|  | 
 **event_data** | **str**|  | 
 **plugin_version** | **str**|  | 
 **octoprint_version** | **str**|  | 
 **print_job** | **int**|  | [optional] 

### Return type

[**PredictEvent**](PredictEvent.md)

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

