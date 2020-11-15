# print_nanny_client.PrintJobsApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**print_jobs_create**](PrintJobsApi.md#print_jobs_create) | **POST** /api/print_jobs/ | 
[**print_jobs_list**](PrintJobsApi.md#print_jobs_list) | **GET** /api/print_jobs/ | 
[**print_jobs_partial_update**](PrintJobsApi.md#print_jobs_partial_update) | **PATCH** /api/print_jobs/{id}/ | 
[**print_jobs_retrieve**](PrintJobsApi.md#print_jobs_retrieve) | **GET** /api/print_jobs/{id}/ | 
[**print_jobs_update**](PrintJobsApi.md#print_jobs_update) | **PUT** /api/print_jobs/{id}/ | 

# **print_jobs_create**
> PrintJob print_jobs_create(body, dt2, name2, gcode_file_hash2, last_status2, printer_profile2, gcode_file2, dt, name, gcode_file_hash, last_status, printer_profile, gcode_file)



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
api_instance = print_nanny_client.PrintJobsApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PrintJobRequest() # PrintJobRequest | 
dt2 = '2013-10-20T19:20:30+01:00' # datetime | 
name2 = 'name_example' # str | 
gcode_file_hash2 = 'gcode_file_hash_example' # str | 
last_status2 = print_nanny_client.LastStatusEnum() # LastStatusEnum | 
printer_profile2 = 56 # int | 
gcode_file2 = 56 # int | 
dt = '2013-10-20T19:20:30+01:00' # datetime | 
name = 'name_example' # str | 
gcode_file_hash = 'gcode_file_hash_example' # str | 
last_status = print_nanny_client.LastStatusEnum() # LastStatusEnum | 
printer_profile = 56 # int | 
gcode_file = 56 # int | 

try:
    api_response = api_instance.print_jobs_create(body, dt2, name2, gcode_file_hash2, last_status2, printer_profile2, gcode_file2, dt, name, gcode_file_hash, last_status, printer_profile, gcode_file)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrintJobsApi->print_jobs_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PrintJobRequest**](PrintJobRequest.md)|  | 
 **dt2** | **datetime**|  | 
 **name2** | **str**|  | 
 **gcode_file_hash2** | **str**|  | 
 **last_status2** | [**LastStatusEnum**](.md)|  | 
 **printer_profile2** | **int**|  | 
 **gcode_file2** | **int**|  | 
 **dt** | **datetime**|  | 
 **name** | **str**|  | 
 **gcode_file_hash** | **str**|  | 
 **last_status** | [**LastStatusEnum**](.md)|  | 
 **printer_profile** | **int**|  | 
 **gcode_file** | **int**|  | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_list**
> PaginatedPrintJobList print_jobs_list(limit=limit, offset=offset)



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
api_instance = print_nanny_client.PrintJobsApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.print_jobs_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrintJobsApi->print_jobs_list: %s\n" % e)
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_partial_update**
> PrintJob print_jobs_partial_update(id, body=body, dt2=dt2, name2=name2, gcode_file_hash2=gcode_file_hash2, last_status2=last_status2, printer_profile2=printer_profile2, gcode_file2=gcode_file2, dt=dt, name=name, gcode_file_hash=gcode_file_hash, last_status=last_status, printer_profile=printer_profile, gcode_file=gcode_file)



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
api_instance = print_nanny_client.PrintJobsApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this print job.
body = print_nanny_client.PatchedPrintJobRequest() # PatchedPrintJobRequest |  (optional)
dt2 = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
name2 = 'name_example' # str |  (optional)
gcode_file_hash2 = 'gcode_file_hash_example' # str |  (optional)
last_status2 = print_nanny_client.LastStatusEnum() # LastStatusEnum |  (optional)
printer_profile2 = 56 # int |  (optional)
gcode_file2 = 56 # int |  (optional)
dt = '2013-10-20T19:20:30+01:00' # datetime |  (optional)
name = 'name_example' # str |  (optional)
gcode_file_hash = 'gcode_file_hash_example' # str |  (optional)
last_status = print_nanny_client.LastStatusEnum() # LastStatusEnum |  (optional)
printer_profile = 56 # int |  (optional)
gcode_file = 56 # int |  (optional)

try:
    api_response = api_instance.print_jobs_partial_update(id, body=body, dt2=dt2, name2=name2, gcode_file_hash2=gcode_file_hash2, last_status2=last_status2, printer_profile2=printer_profile2, gcode_file2=gcode_file2, dt=dt, name=name, gcode_file_hash=gcode_file_hash, last_status=last_status, printer_profile=printer_profile, gcode_file=gcode_file)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrintJobsApi->print_jobs_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this print job. | 
 **body** | [**PatchedPrintJobRequest**](PatchedPrintJobRequest.md)|  | [optional] 
 **dt2** | **datetime**|  | [optional] 
 **name2** | **str**|  | [optional] 
 **gcode_file_hash2** | **str**|  | [optional] 
 **last_status2** | [**LastStatusEnum**](.md)|  | [optional] 
 **printer_profile2** | **int**|  | [optional] 
 **gcode_file2** | **int**|  | [optional] 
 **dt** | **datetime**|  | [optional] 
 **name** | **str**|  | [optional] 
 **gcode_file_hash** | **str**|  | [optional] 
 **last_status** | [**LastStatusEnum**](.md)|  | [optional] 
 **printer_profile** | **int**|  | [optional] 
 **gcode_file** | **int**|  | [optional] 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_retrieve**
> PrintJob print_jobs_retrieve(id)



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
api_instance = print_nanny_client.PrintJobsApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this print job.

try:
    api_response = api_instance.print_jobs_retrieve(id)
    pprint(api_response)
except ApiException as e:
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **print_jobs_update**
> PrintJob print_jobs_update(body, dt2, name2, gcode_file_hash2, last_status2, printer_profile2, gcode_file2, dt, name, gcode_file_hash, last_status, printer_profile, gcode_file, id)



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
api_instance = print_nanny_client.PrintJobsApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PrintJobRequest() # PrintJobRequest | 
dt2 = '2013-10-20T19:20:30+01:00' # datetime | 
name2 = 'name_example' # str | 
gcode_file_hash2 = 'gcode_file_hash_example' # str | 
last_status2 = print_nanny_client.LastStatusEnum() # LastStatusEnum | 
printer_profile2 = 56 # int | 
gcode_file2 = 56 # int | 
dt = '2013-10-20T19:20:30+01:00' # datetime | 
name = 'name_example' # str | 
gcode_file_hash = 'gcode_file_hash_example' # str | 
last_status = print_nanny_client.LastStatusEnum() # LastStatusEnum | 
printer_profile = 56 # int | 
gcode_file = 56 # int | 
id = 56 # int | A unique integer value identifying this print job.

try:
    api_response = api_instance.print_jobs_update(body, dt2, name2, gcode_file_hash2, last_status2, printer_profile2, gcode_file2, dt, name, gcode_file_hash, last_status, printer_profile, gcode_file, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrintJobsApi->print_jobs_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PrintJobRequest**](PrintJobRequest.md)|  | 
 **dt2** | **datetime**|  | 
 **name2** | **str**|  | 
 **gcode_file_hash2** | **str**|  | 
 **last_status2** | [**LastStatusEnum**](.md)|  | 
 **printer_profile2** | **int**|  | 
 **gcode_file2** | **int**|  | 
 **dt** | **datetime**|  | 
 **name** | **str**|  | 
 **gcode_file_hash** | **str**|  | 
 **last_status** | [**LastStatusEnum**](.md)|  | 
 **printer_profile** | **int**|  | 
 **gcode_file** | **int**|  | 
 **id** | **int**| A unique integer value identifying this print job. | 

### Return type

[**PrintJob**](PrintJob.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

