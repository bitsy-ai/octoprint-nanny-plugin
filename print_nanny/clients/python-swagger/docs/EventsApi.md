# print_nanny_client.EventsApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**events_octoprint_create**](EventsApi.md#events_octoprint_create) | **POST** /api/events/octoprint/ | 
[**events_octoprint_list**](EventsApi.md#events_octoprint_list) | **GET** /api/events/octoprint/ | 
[**events_predict_create**](EventsApi.md#events_predict_create) | **POST** /api/events/predict/ | 
[**events_predict_list**](EventsApi.md#events_predict_list) | **GET** /api/events/predict/ | 

# **events_octoprint_create**
> OctoPrintEvent events_octoprint_create(body, dt2, event_type2, event_data2, plugin_version2, octoprint_version2, dt, event_type, event_data, plugin_version, octoprint_version)



### Example
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: cookieAuth
configuration = print_nanny_client.Configuration()
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'

# create an instance of the API class
api_instance = print_nanny_client.EventsApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.OctoPrintEventRequest() # OctoPrintEventRequest | 
dt2 = '2013-10-20T19:20:30+01:00' # datetime | 
event_type2 = 'event_type_example' # str | 
event_data2 = {'key': print_nanny_client.Object()} # dict(str, Object) | 
plugin_version2 = 'plugin_version_example' # str | 
octoprint_version2 = 'octoprint_version_example' # str | 
dt = '2013-10-20T19:20:30+01:00' # datetime | 
event_type = 'event_type_example' # str | 
event_data = {'key': print_nanny_client.Object()} # dict(str, Object) | 
plugin_version = 'plugin_version_example' # str | 
octoprint_version = 'octoprint_version_example' # str | 

try:
    api_response = api_instance.events_octoprint_create(body, dt2, event_type2, event_data2, plugin_version2, octoprint_version2, dt, event_type, event_data, plugin_version, octoprint_version)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling EventsApi->events_octoprint_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**OctoPrintEventRequest**](OctoPrintEventRequest.md)|  | 
 **dt2** | **datetime**|  | 
 **event_type2** | **str**|  | 
 **event_data2** | [**dict(str, Object)**](Object.md)|  | 
 **plugin_version2** | **str**|  | 
 **octoprint_version2** | **str**|  | 
 **dt** | **datetime**|  | 
 **event_type** | **str**|  | 
 **event_data** | [**dict(str, Object)**](Object.md)|  | 
 **plugin_version** | **str**|  | 
 **octoprint_version** | **str**|  | 

### Return type

[**OctoPrintEvent**](OctoPrintEvent.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **events_octoprint_list**
> PaginatedOctoPrintEventList events_octoprint_list(limit=limit, offset=offset)



### Example
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: cookieAuth
configuration = print_nanny_client.Configuration()
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'

# create an instance of the API class
api_instance = print_nanny_client.EventsApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.events_octoprint_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling EventsApi->events_octoprint_list: %s\n" % e)
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **events_predict_create**
> PredictEvent events_predict_create(body, dt2, original_image2, annotated_image2, event_data2, plugin_version2, octoprint_version2, print_job2, dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job)



### Example
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: cookieAuth
configuration = print_nanny_client.Configuration()
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'

# create an instance of the API class
api_instance = print_nanny_client.EventsApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PredictEventRequest() # PredictEventRequest | 
dt2 = '2013-10-20T19:20:30+01:00' # datetime | 
original_image2 = 'original_image_example' # str | 
annotated_image2 = 'annotated_image_example' # str | 
event_data2 = {'key': print_nanny_client.Object()} # dict(str, Object) | 
plugin_version2 = 'plugin_version_example' # str | 
octoprint_version2 = 'octoprint_version_example' # str | 
print_job2 = 56 # int | 
dt = '2013-10-20T19:20:30+01:00' # datetime | 
original_image = 'original_image_example' # str | 
annotated_image = 'annotated_image_example' # str | 
event_data = {'key': print_nanny_client.Object()} # dict(str, Object) | 
plugin_version = 'plugin_version_example' # str | 
octoprint_version = 'octoprint_version_example' # str | 
print_job = 56 # int | 

try:
    api_response = api_instance.events_predict_create(body, dt2, original_image2, annotated_image2, event_data2, plugin_version2, octoprint_version2, print_job2, dt, original_image, annotated_image, event_data, plugin_version, octoprint_version, print_job)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling EventsApi->events_predict_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PredictEventRequest**](PredictEventRequest.md)|  | 
 **dt2** | **datetime**|  | 
 **original_image2** | **str**|  | 
 **annotated_image2** | **str**|  | 
 **event_data2** | [**dict(str, Object)**](Object.md)|  | 
 **plugin_version2** | **str**|  | 
 **octoprint_version2** | **str**|  | 
 **print_job2** | **int**|  | 
 **dt** | **datetime**|  | 
 **original_image** | **str**|  | 
 **annotated_image** | **str**|  | 
 **event_data** | [**dict(str, Object)**](Object.md)|  | 
 **plugin_version** | **str**|  | 
 **octoprint_version** | **str**|  | 
 **print_job** | **int**|  | 

### Return type

[**PredictEvent**](PredictEvent.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded, application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **events_predict_list**
> PaginatedPredictEventList events_predict_list(limit=limit, offset=offset)



### Example
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint

# Configure API key authorization: cookieAuth
configuration = print_nanny_client.Configuration()
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'

# create an instance of the API class
api_instance = print_nanny_client.EventsApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.events_predict_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling EventsApi->events_predict_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional] 
 **offset** | **int**| The initial index from which to return the results. | [optional] 

### Return type

[**PaginatedPredictEventList**](PaginatedPredictEventList.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

