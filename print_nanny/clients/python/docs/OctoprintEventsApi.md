# print_nanny_client.OctoprintEventsApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**octoprint_events_create**](OctoprintEventsApi.md#octoprint_events_create) | **POST** /api/octoprint_events/ | 
[**octoprint_events_list**](OctoprintEventsApi.md#octoprint_events_list) | **GET** /api/octoprint_events/ | 


# **octoprint_events_create**
> OctoPrintEvent octoprint_events_create(octo_print_event_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import octoprint_events_api
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
    api_instance = octoprint_events_api.OctoprintEventsApi(api_client)
    octo_print_event_request = OctoPrintEventRequest(
        dt=dateutil_parser('1970-01-01T00:00:00.00Z'),
        event_type="event_type_example",
        event_data={
            "key": None,
        },
        plugin_version="plugin_version_example",
        octoprint_version="octoprint_version_example",
        print_job=1,
    ) # OctoPrintEventRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.octoprint_events_create(octo_print_event_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling OctoprintEventsApi->octoprint_events_create: %s\n" % e)
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

# **octoprint_events_list**
> PaginatedOctoPrintEventList octoprint_events_list()



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import octoprint_events_api
from print_nanny_client.model.paginated_octo_print_event_list import PaginatedOctoPrintEventList
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
    api_instance = octoprint_events_api.OctoprintEventsApi(api_client)
    limit = 1 # int | Number of results to return per page. (optional)
    offset = 1 # int | The initial index from which to return the results. (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.octoprint_events_list(limit=limit, offset=offset)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling OctoprintEventsApi->octoprint_events_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional]
 **offset** | **int**| The initial index from which to return the results. | [optional]

### Return type

[**PaginatedOctoPrintEventList**](PaginatedOctoPrintEventList.md)

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

