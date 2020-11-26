# print_nanny_client.UsersApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**users_list**](UsersApi.md#users_list) | **GET** /api/users/ | 
[**users_me_retrieve**](UsersApi.md#users_me_retrieve) | **GET** /api/users/me/ | 
[**users_partial_update**](UsersApi.md#users_partial_update) | **PATCH** /api/users/{id}/ | 
[**users_retrieve**](UsersApi.md#users_retrieve) | **GET** /api/users/{id}/ | 
[**users_update**](UsersApi.md#users_update) | **PUT** /api/users/{id}/ | 


# **users_list**
> PaginatedUserList users_list()



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.users_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_list: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
limit = 56 # int | Number of results to return per page. (optional)
offset = 56 # int | The initial index from which to return the results. (optional)

try:
    api_response = api_instance.users_list(limit=limit, offset=offset)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_list: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Number of results to return per page. | [optional]
 **offset** | **int**| The initial index from which to return the results. | [optional]

### Return type

[**PaginatedUserList**](PaginatedUserList.md)

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

# **users_me_retrieve**
> User users_me_retrieve()



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))

try:
    api_response = api_instance.users_me_retrieve()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_me_retrieve: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))

try:
    api_response = api_instance.users_me_retrieve()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_me_retrieve: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**User**](User.md)

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

# **users_partial_update**
> User users_partial_update(id)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.
patched_user_request = print_nanny_client.PatchedUserRequest() # PatchedUserRequest |  (optional)

try:
    api_response = api_instance.users_partial_update(id, patched_user_request=patched_user_request)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_partial_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.
patched_user_request = print_nanny_client.PatchedUserRequest() # PatchedUserRequest |  (optional)

try:
    api_response = api_instance.users_partial_update(id, patched_user_request=patched_user_request)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_partial_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this user. |
 **patched_user_request** | [**PatchedUserRequest**](PatchedUserRequest.md)|  | [optional]

### Return type

[**User**](User.md)

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

# **users_retrieve**
> User users_retrieve(id)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.

try:
    api_response = api_instance.users_retrieve(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_retrieve: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.

try:
    api_response = api_instance.users_retrieve(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_retrieve: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this user. |

### Return type

[**User**](User.md)

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

# **users_update**
> User users_update(id, user_request)



### Example

* Api Key Authentication (cookieAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.
user_request = print_nanny_client.UserRequest() # UserRequest | 

try:
    api_response = api_instance.users_update(id, user_request)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_update: %s\n" % e)
```

* Bearer (Bearer) Authentication (tokenAuth):
```python
from __future__ import print_function
import time
import print_nanny_client
from print_nanny_client.rest import ApiException
from pprint import pprint
configuration = print_nanny_client.Configuration()
# Configure API key authorization: cookieAuth
configuration.api_key['Session'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Session'] = 'Bearer'
configuration = print_nanny_client.Configuration()
# Configure Bearer authorization (Bearer): tokenAuth
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost
configuration.host = "http://localhost"
# Create an instance of the API class
api_instance = print_nanny_client.UsersApi(print_nanny_client.ApiClient(configuration))
id = 56 # int | A unique integer value identifying this user.
user_request = print_nanny_client.UserRequest() # UserRequest | 

try:
    api_response = api_instance.users_update(id, user_request)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UsersApi->users_update: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **int**| A unique integer value identifying this user. |
 **user_request** | [**UserRequest**](UserRequest.md)|  |

### Return type

[**User**](User.md)

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

