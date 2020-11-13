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
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import events_api
from print_nanny_client.model.octo_print_event_request import OctoPrintEventRequest
from print_nanny_client.model.octo_print_event import OctoPrintEvent
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
    api_instance = events_api.EventsApi(api_client)
    octo_print_event_request = OctoPrintEventRequest(
        dt=dateutil_parser('1970-01-01T00:00:00.00Z'),
        event_type="event_type_example",
        event_data={
            "key": None,
        },
        plugin_version="plugin_version_example",
        octoprint_version="octoprint_version_example",
        user=1,
        print_job=1,
    ) # OctoPrintEventRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.events_octoprint_create(octo_print_event_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
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
> PredictEvent events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import events_api
from print_nanny_client.model.predict_event import PredictEvent
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
    api_instance = events_api.EventsApi(api_client)
    dt = dateutil_parser('1970-01-01T00:00:00.00Z') # datetime | 
    original_image = open('/path/to/file', 'rb') # file_type | 
    annotated_image = open('/path/to/file', 'rb') # file_type | 
    event_data = "event_data_example" # str | 
    plugin_version = "plugin_version_example" # str | 
    octoprint_version = "octoprint_version_example" # str | 
    print_job = 1 # int, none_type |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling EventsApi->events_predict_create: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.events_predict_create(dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job=print_job)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling EventsApi->events_predict_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dt** | **datetime**|  |
 **original_image** | **file_type**|  |
 **annotated_image** | **file_type**|  |
 **event_data** | **str**|  |
 **plugin_version** | **str**|  |
 **octoprint_version** | **str**|  |
 **print_job** | **int, none_type**|  | [optional]

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

