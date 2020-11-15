# print_nanny_client.GcodeFilesApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**gcode_files_create**](GcodeFilesApi.md#gcode_files_create) | **POST** /api/gcode_files/ | 
[**gcode_files_list**](GcodeFilesApi.md#gcode_files_list) | **GET** /api/gcode_files/ | 
[**gcode_files_partial_update**](GcodeFilesApi.md#gcode_files_partial_update) | **PATCH** /api/gcode_files/{id}/ | 
[**gcode_files_retrieve**](GcodeFilesApi.md#gcode_files_retrieve) | **GET** /api/gcode_files/{id}/ | 
[**gcode_files_update**](GcodeFilesApi.md#gcode_files_update) | **PUT** /api/gcode_files/{id}/ | 
[**gcode_files_update_or_create**](GcodeFilesApi.md#gcode_files_update_or_create) | **POST** /api/gcode_files/update_or_create/ | 

# **gcode_files_create**
> GcodeFile gcode_files_create(name2, file2, file_hash2, name, file, file_hash)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
name2 = 'name_example' # str | 
file2 = 'file_example' # str | 
file_hash2 = 'file_hash_example' # str | 
name = 'name_example' # str | 
file = 'file_example' # str | 
file_hash = 'file_hash_example' # str | 

try:
    api_response = api_instance.gcode_files_create(name2, file2, file_hash2, name, file, file_hash)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GcodeFilesApi->gcode_files_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name2** | **str**|  | 
 **file2** | **str**|  | 
 **file_hash2** | **str**|  | 
 **name** | **str**|  | 
 **file** | **str**|  | 
 **file_hash** | **str**|  | 

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_list**
> PaginatedGcodeFileList gcode_files_list(limit=limit, offset=offset)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.gcode_files_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_partial_update**
> GcodeFile gcode_files_partial_update(id, name2=name2, file2=file2, file_hash2=file_hash2, name=name, file=file, file_hash=file_hash)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this gcode file.
name2 = 'name_example' # str |  (optional)
file2 = 'file_example' # str |  (optional)
file_hash2 = 'file_hash_example' # str |  (optional)
name = 'name_example' # str |  (optional)
file = 'file_example' # str |  (optional)
file_hash = 'file_hash_example' # str |  (optional)

try:
    api_response = api_instance.gcode_files_partial_update(id, name2=name2, file2=file2, file_hash2=file_hash2, name=name, file=file, file_hash=file_hash)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GcodeFilesApi->gcode_files_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this gcode file. | 
 **name2** | **str**|  | [optional] 
 **file2** | **str**|  | [optional] 
 **file_hash2** | **str**|  | [optional] 
 **name** | **str**|  | [optional] 
 **file** | **str**|  | [optional] 
 **file_hash** | **str**|  | [optional] 

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_retrieve**
> GcodeFile gcode_files_retrieve(id)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this gcode file.

try:
    api_response = api_instance.gcode_files_retrieve(id)
    pprint(api_response)
except ApiException as e:
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_update**
> GcodeFile gcode_files_update(name2, file2, file_hash2, name, file, file_hash, id)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
name2 = 'name_example' # str | 
file2 = 'file_example' # str | 
file_hash2 = 'file_hash_example' # str | 
name = 'name_example' # str | 
file = 'file_example' # str | 
file_hash = 'file_hash_example' # str | 
id = 56 # int | A unique integer value identifying this gcode file.

try:
    api_response = api_instance.gcode_files_update(name2, file2, file_hash2, name, file, file_hash, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GcodeFilesApi->gcode_files_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name2** | **str**|  | 
 **file2** | **str**|  | 
 **file_hash2** | **str**|  | 
 **name** | **str**|  | 
 **file** | **str**|  | 
 **file_hash** | **str**|  | 
 **id** | **int**| A unique integer value identifying this gcode file. | 

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **gcode_files_update_or_create**
> GcodeFile gcode_files_update_or_create(name2, file2, file_hash2, name, file, file_hash)



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
api_instance = print_nanny_client.GcodeFilesApi(print_nanny_client.ApiClient(configuration))
name2 = 'name_example' # str | 
file2 = 'file_example' # str | 
file_hash2 = 'file_hash_example' # str | 
name = 'name_example' # str | 
file = 'file_example' # str | 
file_hash = 'file_hash_example' # str | 

try:
    api_response = api_instance.gcode_files_update_or_create(name2, file2, file_hash2, name, file, file_hash)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GcodeFilesApi->gcode_files_update_or_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **name2** | **str**|  | 
 **file2** | **str**|  | 
 **file_hash2** | **str**|  | 
 **name** | **str**|  | 
 **file** | **str**|  | 
 **file_hash** | **str**|  | 

### Return type

[**GcodeFile**](GcodeFile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: multipart/form-data, application/x-www-form-urlencoded
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

