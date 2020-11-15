# print_nanny_client.SchemaApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**schema_retrieve**](SchemaApi.md#schema_retrieve) | **GET** /api/schema/ | 

# **schema_retrieve**
> dict(str, Object) schema_retrieve(lang=lang)



OpenApi3 schema for this API. Format can be selected via content negotiation.  - YAML: application/vnd.oai.openapi - JSON: application/vnd.oai.openapi+json

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
api_instance = print_nanny_client.SchemaApi(print_nanny_client.ApiClient(configuration))
lang = 'lang_example' # str |  (optional)

try:
    api_response = api_instance.schema_retrieve(lang=lang)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchemaApi->schema_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **lang** | **str**|  | [optional] 

### Return type

[**dict(str, Object)**](Object.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.oai.openapi+json, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

