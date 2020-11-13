# print_nanny_client.PrinterProfilesApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**printer_profiles_create**](PrinterProfilesApi.md#printer_profiles_create) | **POST** /api/printer_profiles/ | 
[**printer_profiles_list**](PrinterProfilesApi.md#printer_profiles_list) | **GET** /api/printer_profiles/ | 
[**printer_profiles_partial_update**](PrinterProfilesApi.md#printer_profiles_partial_update) | **PATCH** /api/printer_profiles/{id}/ | 
[**printer_profiles_retrieve**](PrinterProfilesApi.md#printer_profiles_retrieve) | **GET** /api/printer_profiles/{id}/ | 
[**printer_profiles_update**](PrinterProfilesApi.md#printer_profiles_update) | **PUT** /api/printer_profiles/{id}/ | 


# **printer_profiles_create**
> PrinterProfile printer_profiles_create(printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import printer_profiles_api
from print_nanny_client.model.printer_profile import PrinterProfile
from print_nanny_client.model.printer_profile_request import PrinterProfileRequest
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
    api_instance = printer_profiles_api.PrinterProfilesApi(api_client)
    printer_profile_request = PrinterProfileRequest(
        axes_e_inverted=True,
        axes_e_speed=-2147483648,
        axes_x_speed=-2147483648,
        axes_y_inverted=True,
        axes_y_speed=-2147483648,
        axes_z_inverted=True,
        axes_z_speed=-2147483648,
        extruder_count=-2147483648,
        extruder_nozzle_diameter=3.14,
        extruder_offsets=[
            3.14,
        ],
        extruder_shared_nozzle=True,
        heated_bed=True,
        heated_chamber=True,
        model="model_example",
        name="name_example",
        volume_custom_box=True,
        volume_depth=3.14,
        volume_form_factor="volume_form_factor_example",
        volume_height=3.14,
        volume_origin="volume_origin_example",
        user=1,
    ) # PrinterProfileRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.printer_profiles_create(printer_profile_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrinterProfilesApi->printer_profiles_create: %s\n" % e)
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
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_list**
> [PrinterProfile] printer_profiles_list()



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import printer_profiles_api
from print_nanny_client.model.printer_profile import PrinterProfile
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
    api_instance = printer_profiles_api.PrinterProfilesApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        api_response = api_instance.printer_profiles_list()
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrinterProfilesApi->printer_profiles_list: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**[PrinterProfile]**](PrinterProfile.md)

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
> PrinterProfile printer_profiles_partial_update(id)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import printer_profiles_api
from print_nanny_client.model.printer_profile import PrinterProfile
from print_nanny_client.model.patched_printer_profile_request import PatchedPrinterProfileRequest
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
    api_instance = printer_profiles_api.PrinterProfilesApi(api_client)
    id = 1 # int | A unique integer value identifying this printer profile.
    patched_printer_profile_request = PatchedPrinterProfileRequest(
        axes_e_inverted=True,
        axes_e_speed=-2147483648,
        axes_x_speed=-2147483648,
        axes_y_inverted=True,
        axes_y_speed=-2147483648,
        axes_z_inverted=True,
        axes_z_speed=-2147483648,
        extruder_count=-2147483648,
        extruder_nozzle_diameter=3.14,
        extruder_offsets=[
            3.14,
        ],
        extruder_shared_nozzle=True,
        heated_bed=True,
        heated_chamber=True,
        model="model_example",
        name="name_example",
        volume_custom_box=True,
        volume_depth=3.14,
        volume_form_factor="volume_form_factor_example",
        volume_height=3.14,
        volume_origin="volume_origin_example",
        user=1,
    ) # PatchedPrinterProfileRequest |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.printer_profiles_partial_update(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrinterProfilesApi->printer_profiles_partial_update: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.printer_profiles_partial_update(id, patched_printer_profile_request=patched_printer_profile_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrinterProfilesApi->printer_profiles_partial_update: %s\n" % e)
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
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import printer_profiles_api
from print_nanny_client.model.printer_profile import PrinterProfile
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
    api_instance = printer_profiles_api.PrinterProfilesApi(api_client)
    id = 1 # int | A unique integer value identifying this printer profile.

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.printer_profiles_retrieve(id)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
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

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** |  |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **printer_profiles_update**
> PrinterProfile printer_profiles_update(id, printer_profile_request)



### Example

* Api Key Authentication (cookieAuth):
* Bearer (Bearer) Authentication (tokenAuth):
```python
import time
import print_nanny_client
from print_nanny_client.api import printer_profiles_api
from print_nanny_client.model.printer_profile import PrinterProfile
from print_nanny_client.model.printer_profile_request import PrinterProfileRequest
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
    api_instance = printer_profiles_api.PrinterProfilesApi(api_client)
    id = 1 # int | A unique integer value identifying this printer profile.
    printer_profile_request = PrinterProfileRequest(
        axes_e_inverted=True,
        axes_e_speed=-2147483648,
        axes_x_speed=-2147483648,
        axes_y_inverted=True,
        axes_y_speed=-2147483648,
        axes_z_inverted=True,
        axes_z_speed=-2147483648,
        extruder_count=-2147483648,
        extruder_nozzle_diameter=3.14,
        extruder_offsets=[
            3.14,
        ],
        extruder_shared_nozzle=True,
        heated_bed=True,
        heated_chamber=True,
        model="model_example",
        name="name_example",
        volume_custom_box=True,
        volume_depth=3.14,
        volume_form_factor="volume_form_factor_example",
        volume_height=3.14,
        volume_origin="volume_origin_example",
        user=1,
    ) # PrinterProfileRequest | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.printer_profiles_update(id, printer_profile_request)
        pprint(api_response)
    except print_nanny_client.ApiException as e:
        print("Exception when calling PrinterProfilesApi->printer_profiles_update: %s\n" % e)
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

