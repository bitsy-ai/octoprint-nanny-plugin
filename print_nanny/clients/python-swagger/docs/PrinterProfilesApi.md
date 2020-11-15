# print_nanny_client.PrinterProfilesApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**printer_profiles_create**](PrinterProfilesApi.md#printer_profiles_create) | **POST** /api/printer_profiles/ | 
[**printer_profiles_list**](PrinterProfilesApi.md#printer_profiles_list) | **GET** /api/printer_profiles/ | 
[**printer_profiles_partial_update**](PrinterProfilesApi.md#printer_profiles_partial_update) | **PATCH** /api/printer_profiles/{id}/ | 
[**printer_profiles_retrieve**](PrinterProfilesApi.md#printer_profiles_retrieve) | **GET** /api/printer_profiles/{id}/ | 
[**printer_profiles_update**](PrinterProfilesApi.md#printer_profiles_update) | **PUT** /api/printer_profiles/{id}/ | 
[**printer_profiles_update_or_create**](PrinterProfilesApi.md#printer_profiles_update_or_create) | **POST** /api/printer_profiles/update_or_create/ | 

# **printer_profiles_create**
> PrinterProfile printer_profiles_create(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 
axes_e_inverted2 = true # bool | 
axes_e_speed2 = 56 # int | 
axes_x_speed2 = 56 # int | 
axes_x_inverted2 = true # bool | 
axes_y_inverted2 = true # bool | 
axes_y_speed2 = 56 # int | 
axes_z_inverted2 = true # bool | 
axes_z_speed2 = 56 # int | 
extruder_count2 = 56 # int | 
extruder_nozzle_diameter2 = 3.4 # float | 
extruder_offsets2 = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle2 = true # bool | 
heated_bed2 = true # bool | 
heated_chamber2 = true # bool | 
model2 = 'model_example' # str | 
name2 = 'name_example' # str | 
volume_custom_box2 = true # bool | 
volume_depth2 = 3.4 # float | 
volume_formfactor2 = 'volume_formfactor_example' # str | 
volume_height2 = 3.4 # float | 
volume_origin2 = 'volume_origin_example' # str | 
volume_width2 = 3.4 # float | 
axes_e_inverted = true # bool | 
axes_e_speed = 56 # int | 
axes_x_speed = 56 # int | 
axes_x_inverted = true # bool | 
axes_y_inverted = true # bool | 
axes_y_speed = 56 # int | 
axes_z_inverted = true # bool | 
axes_z_speed = 56 # int | 
extruder_count = 56 # int | 
extruder_nozzle_diameter = 3.4 # float | 
extruder_offsets = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle = true # bool | 
heated_bed = true # bool | 
heated_chamber = true # bool | 
model = 'model_example' # str | 
name = 'name_example' # str | 
volume_custom_box = true # bool | 
volume_depth = 3.4 # float | 
volume_formfactor = 'volume_formfactor_example' # str | 
volume_height = 3.4 # float | 
volume_origin = 'volume_origin_example' # str | 
volume_width = 3.4 # float | 

try:
    api_response = api_instance.printer_profiles_create(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 
 **axes_e_inverted2** | **bool**|  | 
 **axes_e_speed2** | **int**|  | 
 **axes_x_speed2** | **int**|  | 
 **axes_x_inverted2** | **bool**|  | 
 **axes_y_inverted2** | **bool**|  | 
 **axes_y_speed2** | **int**|  | 
 **axes_z_inverted2** | **bool**|  | 
 **axes_z_speed2** | **int**|  | 
 **extruder_count2** | **int**|  | 
 **extruder_nozzle_diameter2** | **float**|  | 
 **extruder_offsets2** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle2** | **bool**|  | 
 **heated_bed2** | **bool**|  | 
 **heated_chamber2** | **bool**|  | 
 **model2** | **str**|  | 
 **name2** | **str**|  | 
 **volume_custom_box2** | **bool**|  | 
 **volume_depth2** | **float**|  | 
 **volume_formfactor2** | **str**|  | 
 **volume_height2** | **float**|  | 
 **volume_origin2** | **str**|  | 
 **volume_width2** | **float**|  | 
 **axes_e_inverted** | **bool**|  | 
 **axes_e_speed** | **int**|  | 
 **axes_x_speed** | **int**|  | 
 **axes_x_inverted** | **bool**|  | 
 **axes_y_inverted** | **bool**|  | 
 **axes_y_speed** | **int**|  | 
 **axes_z_inverted** | **bool**|  | 
 **axes_z_speed** | **int**|  | 
 **extruder_count** | **int**|  | 
 **extruder_nozzle_diameter** | **float**|  | 
 **extruder_offsets** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle** | **bool**|  | 
 **heated_bed** | **bool**|  | 
 **heated_chamber** | **bool**|  | 
 **model** | **str**|  | 
 **name** | **str**|  | 
 **volume_custom_box** | **bool**|  | 
 **volume_depth** | **float**|  | 
 **volume_formfactor** | **str**|  | 
 **volume_height** | **float**|  | 
 **volume_origin** | **str**|  | 
 **volume_width** | **float**|  | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_list**
> PaginatedPrinterProfileList printer_profiles_list(limit=limit, name=name, offset=offset, user=user)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
name = 'name_example' # str | name (optional)
offset = 56 # int | The initial index from which to return the results. (optional)
user = 'user_example' # str | user (optional)

try:
    api_response = api_instance.printer_profiles_list(limit=limit, name=name, offset=offset, user=user)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_list: %s\n" % e)
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_partial_update**
> PrinterProfile printer_profiles_partial_update(id, body=body, axes_e_inverted2=axes_e_inverted2, axes_e_speed2=axes_e_speed2, axes_x_speed2=axes_x_speed2, axes_x_inverted2=axes_x_inverted2, axes_y_inverted2=axes_y_inverted2, axes_y_speed2=axes_y_speed2, axes_z_inverted2=axes_z_inverted2, axes_z_speed2=axes_z_speed2, extruder_count2=extruder_count2, extruder_nozzle_diameter2=extruder_nozzle_diameter2, extruder_offsets2=extruder_offsets2, extruder_shared_nozzle2=extruder_shared_nozzle2, heated_bed2=heated_bed2, heated_chamber2=heated_chamber2, model2=model2, name2=name2, volume_custom_box2=volume_custom_box2, volume_depth2=volume_depth2, volume_formfactor2=volume_formfactor2, volume_height2=volume_height2, volume_origin2=volume_origin2, volume_width2=volume_width2, axes_e_inverted=axes_e_inverted, axes_e_speed=axes_e_speed, axes_x_speed=axes_x_speed, axes_x_inverted=axes_x_inverted, axes_y_inverted=axes_y_inverted, axes_y_speed=axes_y_speed, axes_z_inverted=axes_z_inverted, axes_z_speed=axes_z_speed, extruder_count=extruder_count, extruder_nozzle_diameter=extruder_nozzle_diameter, extruder_offsets=extruder_offsets, extruder_shared_nozzle=extruder_shared_nozzle, heated_bed=heated_bed, heated_chamber=heated_chamber, model=model, name=name, volume_custom_box=volume_custom_box, volume_depth=volume_depth, volume_formfactor=volume_formfactor, volume_height=volume_height, volume_origin=volume_origin, volume_width=volume_width)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this printer profile.
body = print_nanny_client.PatchedPrinterProfileRequest() # PatchedPrinterProfileRequest |  (optional)
axes_e_inverted2 = true # bool |  (optional)
axes_e_speed2 = 56 # int |  (optional)
axes_x_speed2 = 56 # int |  (optional)
axes_x_inverted2 = true # bool |  (optional)
axes_y_inverted2 = true # bool |  (optional)
axes_y_speed2 = 56 # int |  (optional)
axes_z_inverted2 = true # bool |  (optional)
axes_z_speed2 = 56 # int |  (optional)
extruder_count2 = 56 # int |  (optional)
extruder_nozzle_diameter2 = 3.4 # float |  (optional)
extruder_offsets2 = [print_nanny_client.list[float]()] # list[list[float]] |  (optional)
extruder_shared_nozzle2 = true # bool |  (optional)
heated_bed2 = true # bool |  (optional)
heated_chamber2 = true # bool |  (optional)
model2 = 'model_example' # str |  (optional)
name2 = 'name_example' # str |  (optional)
volume_custom_box2 = true # bool |  (optional)
volume_depth2 = 3.4 # float |  (optional)
volume_formfactor2 = 'volume_formfactor_example' # str |  (optional)
volume_height2 = 3.4 # float |  (optional)
volume_origin2 = 'volume_origin_example' # str |  (optional)
volume_width2 = 3.4 # float |  (optional)
axes_e_inverted = true # bool |  (optional)
axes_e_speed = 56 # int |  (optional)
axes_x_speed = 56 # int |  (optional)
axes_x_inverted = true # bool |  (optional)
axes_y_inverted = true # bool |  (optional)
axes_y_speed = 56 # int |  (optional)
axes_z_inverted = true # bool |  (optional)
axes_z_speed = 56 # int |  (optional)
extruder_count = 56 # int |  (optional)
extruder_nozzle_diameter = 3.4 # float |  (optional)
extruder_offsets = [print_nanny_client.list[float]()] # list[list[float]] |  (optional)
extruder_shared_nozzle = true # bool |  (optional)
heated_bed = true # bool |  (optional)
heated_chamber = true # bool |  (optional)
model = 'model_example' # str |  (optional)
name = 'name_example' # str |  (optional)
volume_custom_box = true # bool |  (optional)
volume_depth = 3.4 # float |  (optional)
volume_formfactor = 'volume_formfactor_example' # str |  (optional)
volume_height = 3.4 # float |  (optional)
volume_origin = 'volume_origin_example' # str |  (optional)
volume_width = 3.4 # float |  (optional)

try:
    api_response = api_instance.printer_profiles_partial_update(id, body=body, axes_e_inverted2=axes_e_inverted2, axes_e_speed2=axes_e_speed2, axes_x_speed2=axes_x_speed2, axes_x_inverted2=axes_x_inverted2, axes_y_inverted2=axes_y_inverted2, axes_y_speed2=axes_y_speed2, axes_z_inverted2=axes_z_inverted2, axes_z_speed2=axes_z_speed2, extruder_count2=extruder_count2, extruder_nozzle_diameter2=extruder_nozzle_diameter2, extruder_offsets2=extruder_offsets2, extruder_shared_nozzle2=extruder_shared_nozzle2, heated_bed2=heated_bed2, heated_chamber2=heated_chamber2, model2=model2, name2=name2, volume_custom_box2=volume_custom_box2, volume_depth2=volume_depth2, volume_formfactor2=volume_formfactor2, volume_height2=volume_height2, volume_origin2=volume_origin2, volume_width2=volume_width2, axes_e_inverted=axes_e_inverted, axes_e_speed=axes_e_speed, axes_x_speed=axes_x_speed, axes_x_inverted=axes_x_inverted, axes_y_inverted=axes_y_inverted, axes_y_speed=axes_y_speed, axes_z_inverted=axes_z_inverted, axes_z_speed=axes_z_speed, extruder_count=extruder_count, extruder_nozzle_diameter=extruder_nozzle_diameter, extruder_offsets=extruder_offsets, extruder_shared_nozzle=extruder_shared_nozzle, heated_bed=heated_bed, heated_chamber=heated_chamber, model=model, name=name, volume_custom_box=volume_custom_box, volume_depth=volume_depth, volume_formfactor=volume_formfactor, volume_height=volume_height, volume_origin=volume_origin, volume_width=volume_width)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this printer profile. | 
 **body** | [**PatchedPrinterProfileRequest**](PatchedPrinterProfileRequest.md)|  | [optional] 
 **axes_e_inverted2** | **bool**|  | [optional] 
 **axes_e_speed2** | **int**|  | [optional] 
 **axes_x_speed2** | **int**|  | [optional] 
 **axes_x_inverted2** | **bool**|  | [optional] 
 **axes_y_inverted2** | **bool**|  | [optional] 
 **axes_y_speed2** | **int**|  | [optional] 
 **axes_z_inverted2** | **bool**|  | [optional] 
 **axes_z_speed2** | **int**|  | [optional] 
 **extruder_count2** | **int**|  | [optional] 
 **extruder_nozzle_diameter2** | **float**|  | [optional] 
 **extruder_offsets2** | [**list[list[float]]**](list[float].md)|  | [optional] 
 **extruder_shared_nozzle2** | **bool**|  | [optional] 
 **heated_bed2** | **bool**|  | [optional] 
 **heated_chamber2** | **bool**|  | [optional] 
 **model2** | **str**|  | [optional] 
 **name2** | **str**|  | [optional] 
 **volume_custom_box2** | **bool**|  | [optional] 
 **volume_depth2** | **float**|  | [optional] 
 **volume_formfactor2** | **str**|  | [optional] 
 **volume_height2** | **float**|  | [optional] 
 **volume_origin2** | **str**|  | [optional] 
 **volume_width2** | **float**|  | [optional] 
 **axes_e_inverted** | **bool**|  | [optional] 
 **axes_e_speed** | **int**|  | [optional] 
 **axes_x_speed** | **int**|  | [optional] 
 **axes_x_inverted** | **bool**|  | [optional] 
 **axes_y_inverted** | **bool**|  | [optional] 
 **axes_y_speed** | **int**|  | [optional] 
 **axes_z_inverted** | **bool**|  | [optional] 
 **axes_z_speed** | **int**|  | [optional] 
 **extruder_count** | **int**|  | [optional] 
 **extruder_nozzle_diameter** | **float**|  | [optional] 
 **extruder_offsets** | [**list[list[float]]**](list[float].md)|  | [optional] 
 **extruder_shared_nozzle** | **bool**|  | [optional] 
 **heated_bed** | **bool**|  | [optional] 
 **heated_chamber** | **bool**|  | [optional] 
 **model** | **str**|  | [optional] 
 **name** | **str**|  | [optional] 
 **volume_custom_box** | **bool**|  | [optional] 
 **volume_depth** | **float**|  | [optional] 
 **volume_formfactor** | **str**|  | [optional] 
 **volume_height** | **float**|  | [optional] 
 **volume_origin** | **str**|  | [optional] 
 **volume_width** | **float**|  | [optional] 

### Return type

[**PrinterProfile**](PrinterProfile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_retrieve**
> PrinterProfile printer_profiles_retrieve(id)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this printer profile.

try:
    api_response = api_instance.printer_profiles_retrieve(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_retrieve: %s\n" % e)
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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_update**
> PrinterProfile printer_profiles_update(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width, id)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 
axes_e_inverted2 = true # bool | 
axes_e_speed2 = 56 # int | 
axes_x_speed2 = 56 # int | 
axes_x_inverted2 = true # bool | 
axes_y_inverted2 = true # bool | 
axes_y_speed2 = 56 # int | 
axes_z_inverted2 = true # bool | 
axes_z_speed2 = 56 # int | 
extruder_count2 = 56 # int | 
extruder_nozzle_diameter2 = 3.4 # float | 
extruder_offsets2 = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle2 = true # bool | 
heated_bed2 = true # bool | 
heated_chamber2 = true # bool | 
model2 = 'model_example' # str | 
name2 = 'name_example' # str | 
volume_custom_box2 = true # bool | 
volume_depth2 = 3.4 # float | 
volume_formfactor2 = 'volume_formfactor_example' # str | 
volume_height2 = 3.4 # float | 
volume_origin2 = 'volume_origin_example' # str | 
volume_width2 = 3.4 # float | 
axes_e_inverted = true # bool | 
axes_e_speed = 56 # int | 
axes_x_speed = 56 # int | 
axes_x_inverted = true # bool | 
axes_y_inverted = true # bool | 
axes_y_speed = 56 # int | 
axes_z_inverted = true # bool | 
axes_z_speed = 56 # int | 
extruder_count = 56 # int | 
extruder_nozzle_diameter = 3.4 # float | 
extruder_offsets = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle = true # bool | 
heated_bed = true # bool | 
heated_chamber = true # bool | 
model = 'model_example' # str | 
name = 'name_example' # str | 
volume_custom_box = true # bool | 
volume_depth = 3.4 # float | 
volume_formfactor = 'volume_formfactor_example' # str | 
volume_height = 3.4 # float | 
volume_origin = 'volume_origin_example' # str | 
volume_width = 3.4 # float | 
id = 56 # int | A unique integer value identifying this printer profile.

try:
    api_response = api_instance.printer_profiles_update(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 
 **axes_e_inverted2** | **bool**|  | 
 **axes_e_speed2** | **int**|  | 
 **axes_x_speed2** | **int**|  | 
 **axes_x_inverted2** | **bool**|  | 
 **axes_y_inverted2** | **bool**|  | 
 **axes_y_speed2** | **int**|  | 
 **axes_z_inverted2** | **bool**|  | 
 **axes_z_speed2** | **int**|  | 
 **extruder_count2** | **int**|  | 
 **extruder_nozzle_diameter2** | **float**|  | 
 **extruder_offsets2** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle2** | **bool**|  | 
 **heated_bed2** | **bool**|  | 
 **heated_chamber2** | **bool**|  | 
 **model2** | **str**|  | 
 **name2** | **str**|  | 
 **volume_custom_box2** | **bool**|  | 
 **volume_depth2** | **float**|  | 
 **volume_formfactor2** | **str**|  | 
 **volume_height2** | **float**|  | 
 **volume_origin2** | **str**|  | 
 **volume_width2** | **float**|  | 
 **axes_e_inverted** | **bool**|  | 
 **axes_e_speed** | **int**|  | 
 **axes_x_speed** | **int**|  | 
 **axes_x_inverted** | **bool**|  | 
 **axes_y_inverted** | **bool**|  | 
 **axes_y_speed** | **int**|  | 
 **axes_z_inverted** | **bool**|  | 
 **axes_z_speed** | **int**|  | 
 **extruder_count** | **int**|  | 
 **extruder_nozzle_diameter** | **float**|  | 
 **extruder_offsets** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle** | **bool**|  | 
 **heated_bed** | **bool**|  | 
 **heated_chamber** | **bool**|  | 
 **model** | **str**|  | 
 **name** | **str**|  | 
 **volume_custom_box** | **bool**|  | 
 **volume_depth** | **float**|  | 
 **volume_formfactor** | **str**|  | 
 **volume_height** | **float**|  | 
 **volume_origin** | **str**|  | 
 **volume_width** | **float**|  | 
 **id** | **int**| A unique integer value identifying this printer profile. | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_update_or_create**
> PrinterProfile printer_profiles_update_or_create(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width)



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
api_instance = print_nanny_client.PrinterProfilesApi(print_nanny_client.ApiClient(configuration))
body = print_nanny_client.PrinterProfileRequest() # PrinterProfileRequest | 
axes_e_inverted2 = true # bool | 
axes_e_speed2 = 56 # int | 
axes_x_speed2 = 56 # int | 
axes_x_inverted2 = true # bool | 
axes_y_inverted2 = true # bool | 
axes_y_speed2 = 56 # int | 
axes_z_inverted2 = true # bool | 
axes_z_speed2 = 56 # int | 
extruder_count2 = 56 # int | 
extruder_nozzle_diameter2 = 3.4 # float | 
extruder_offsets2 = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle2 = true # bool | 
heated_bed2 = true # bool | 
heated_chamber2 = true # bool | 
model2 = 'model_example' # str | 
name2 = 'name_example' # str | 
volume_custom_box2 = true # bool | 
volume_depth2 = 3.4 # float | 
volume_formfactor2 = 'volume_formfactor_example' # str | 
volume_height2 = 3.4 # float | 
volume_origin2 = 'volume_origin_example' # str | 
volume_width2 = 3.4 # float | 
axes_e_inverted = true # bool | 
axes_e_speed = 56 # int | 
axes_x_speed = 56 # int | 
axes_x_inverted = true # bool | 
axes_y_inverted = true # bool | 
axes_y_speed = 56 # int | 
axes_z_inverted = true # bool | 
axes_z_speed = 56 # int | 
extruder_count = 56 # int | 
extruder_nozzle_diameter = 3.4 # float | 
extruder_offsets = [print_nanny_client.list[float]()] # list[list[float]] | 
extruder_shared_nozzle = true # bool | 
heated_bed = true # bool | 
heated_chamber = true # bool | 
model = 'model_example' # str | 
name = 'name_example' # str | 
volume_custom_box = true # bool | 
volume_depth = 3.4 # float | 
volume_formfactor = 'volume_formfactor_example' # str | 
volume_height = 3.4 # float | 
volume_origin = 'volume_origin_example' # str | 
volume_width = 3.4 # float | 

try:
    api_response = api_instance.printer_profiles_update_or_create(body, axes_e_inverted2, axes_e_speed2, axes_x_speed2, axes_x_inverted2, axes_y_inverted2, axes_y_speed2, axes_z_inverted2, axes_z_speed2, extruder_count2, extruder_nozzle_diameter2, extruder_offsets2, extruder_shared_nozzle2, heated_bed2, heated_chamber2, model2, name2, volume_custom_box2, volume_depth2, volume_formfactor2, volume_height2, volume_origin2, volume_width2, axes_e_inverted, axes_e_speed, axes_x_speed, axes_x_inverted, axes_y_inverted, axes_y_speed, axes_z_inverted, axes_z_speed, extruder_count, extruder_nozzle_diameter, extruder_offsets, extruder_shared_nozzle, heated_bed, heated_chamber, model, name, volume_custom_box, volume_depth, volume_formfactor, volume_height, volume_origin, volume_width)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling PrinterProfilesApi->printer_profiles_update_or_create: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**PrinterProfileRequest**](PrinterProfileRequest.md)|  | 
 **axes_e_inverted2** | **bool**|  | 
 **axes_e_speed2** | **int**|  | 
 **axes_x_speed2** | **int**|  | 
 **axes_x_inverted2** | **bool**|  | 
 **axes_y_inverted2** | **bool**|  | 
 **axes_y_speed2** | **int**|  | 
 **axes_z_inverted2** | **bool**|  | 
 **axes_z_speed2** | **int**|  | 
 **extruder_count2** | **int**|  | 
 **extruder_nozzle_diameter2** | **float**|  | 
 **extruder_offsets2** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle2** | **bool**|  | 
 **heated_bed2** | **bool**|  | 
 **heated_chamber2** | **bool**|  | 
 **model2** | **str**|  | 
 **name2** | **str**|  | 
 **volume_custom_box2** | **bool**|  | 
 **volume_depth2** | **float**|  | 
 **volume_formfactor2** | **str**|  | 
 **volume_height2** | **float**|  | 
 **volume_origin2** | **str**|  | 
 **volume_width2** | **float**|  | 
 **axes_e_inverted** | **bool**|  | 
 **axes_e_speed** | **int**|  | 
 **axes_x_speed** | **int**|  | 
 **axes_x_inverted** | **bool**|  | 
 **axes_y_inverted** | **bool**|  | 
 **axes_y_speed** | **int**|  | 
 **axes_z_inverted** | **bool**|  | 
 **axes_z_speed** | **int**|  | 
 **extruder_count** | **int**|  | 
 **extruder_nozzle_diameter** | **float**|  | 
 **extruder_offsets** | [**list[list[float]]**](list[float].md)|  | 
 **extruder_shared_nozzle** | **bool**|  | 
 **heated_bed** | **bool**|  | 
 **heated_chamber** | **bool**|  | 
 **model** | **str**|  | 
 **name** | **str**|  | 
 **volume_custom_box** | **bool**|  | 
 **volume_depth** | **float**|  | 
 **volume_formfactor** | **str**|  | 
 **volume_height** | **float**|  | 
 **volume_origin** | **str**|  | 
 **volume_width** | **float**|  | 

### Return type

[**PrinterProfile**](PrinterProfile.md)

### Authorization

[cookieAuth](../README.md#cookieAuth), [tokenAuth](../README.md#tokenAuth)

### HTTP request headers

 - **Content-Type**: application/json, application/x-www-form-urlencoded, multipart/form-data
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

