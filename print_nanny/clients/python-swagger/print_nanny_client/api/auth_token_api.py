# coding: utf-8

"""

    No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)  # noqa: E501

    OpenAPI spec version: 0.0.0
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from print_nanny_client.api_client import ApiClient


class AuthTokenApi(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    Ref: https://github.com/swagger-api/swagger-codegen
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def auth_token_create(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
        else:
            (data) = self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
            return data

    def auth_token_create_with_http_info(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create_with_http_info(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['body', 'username2', 'password2', 'username', 'password']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method auth_token_create" % key
                )
            params[key] = val
        del params['kwargs']
        # verify the required parameter 'body' is set
        if ('body' not in params or
                params['body'] is None):
            raise ValueError("Missing the required parameter `body` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username2' is set
        if ('username2' not in params or
                params['username2'] is None):
            raise ValueError("Missing the required parameter `username2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password2' is set
        if ('password2' not in params or
                params['password2'] is None):
            raise ValueError("Missing the required parameter `password2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username' is set
        if ('username' not in params or
                params['username'] is None):
            raise ValueError("Missing the required parameter `username` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password' is set
        if ('password' not in params or
                params['password'] is None):
            raise ValueError("Missing the required parameter `password` when calling `auth_token_create`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501

        body_params = None
        if 'body' in params:
            body_params = params['body']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/x-www-form-urlencoded', 'multipart/form-data', 'application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['cookieAuth', 'tokenAuth']  # noqa: E501

        return self.api_client.call_api(
            '/api/auth-token/', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='AuthToken',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def auth_token_create(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
        else:
            (data) = self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
            return data

    def auth_token_create_with_http_info(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create_with_http_info(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['body', 'username2', 'password2', 'username', 'password']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method auth_token_create" % key
                )
            params[key] = val
        del params['kwargs']
        # verify the required parameter 'body' is set
        if ('body' not in params or
                params['body'] is None):
            raise ValueError("Missing the required parameter `body` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username2' is set
        if ('username2' not in params or
                params['username2'] is None):
            raise ValueError("Missing the required parameter `username2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password2' is set
        if ('password2' not in params or
                params['password2'] is None):
            raise ValueError("Missing the required parameter `password2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username' is set
        if ('username' not in params or
                params['username'] is None):
            raise ValueError("Missing the required parameter `username` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password' is set
        if ('password' not in params or
                params['password'] is None):
            raise ValueError("Missing the required parameter `password` when calling `auth_token_create`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501

        body_params = None
        if 'body' in params:
            body_params = params['body']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/x-www-form-urlencoded', 'multipart/form-data', 'application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['cookieAuth', 'tokenAuth']  # noqa: E501

        return self.api_client.call_api(
            '/api/auth-token/', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='AuthToken',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)

    def auth_token_create(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """
        kwargs['_return_http_data_only'] = True
        if kwargs.get('async_req'):
            return self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
        else:
            (data) = self.auth_token_create_with_http_info(body, username2, password2, username, password, **kwargs)  # noqa: E501
            return data

    def auth_token_create_with_http_info(self, body, username2, password2, username, password, **kwargs):  # noqa: E501
        """auth_token_create  # noqa: E501

        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True
        >>> thread = api.auth_token_create_with_http_info(body, username2, password2, username, password, async_req=True)
        >>> result = thread.get()

        :param async_req bool
        :param AuthTokenRequest body: (required)
        :param str username2: (required)
        :param str password2: (required)
        :param str username: (required)
        :param str password: (required)
        :return: AuthToken
                 If the method is called asynchronously,
                 returns the request thread.
        """

        all_params = ['body', 'username2', 'password2', 'username', 'password']  # noqa: E501
        all_params.append('async_req')
        all_params.append('_return_http_data_only')
        all_params.append('_preload_content')
        all_params.append('_request_timeout')

        params = locals()
        for key, val in six.iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method auth_token_create" % key
                )
            params[key] = val
        del params['kwargs']
        # verify the required parameter 'body' is set
        if ('body' not in params or
                params['body'] is None):
            raise ValueError("Missing the required parameter `body` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username2' is set
        if ('username2' not in params or
                params['username2'] is None):
            raise ValueError("Missing the required parameter `username2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password2' is set
        if ('password2' not in params or
                params['password2'] is None):
            raise ValueError("Missing the required parameter `password2` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'username' is set
        if ('username' not in params or
                params['username'] is None):
            raise ValueError("Missing the required parameter `username` when calling `auth_token_create`")  # noqa: E501
        # verify the required parameter 'password' is set
        if ('password' not in params or
                params['password'] is None):
            raise ValueError("Missing the required parameter `password` when calling `auth_token_create`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = {}

        form_params = []
        local_var_files = {}
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501
        if 'username' in params:
            form_params.append(('username', params['username']))  # noqa: E501
        if 'password' in params:
            form_params.append(('password', params['password']))  # noqa: E501

        body_params = None
        if 'body' in params:
            body_params = params['body']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # HTTP header `Content-Type`
        header_params['Content-Type'] = self.api_client.select_header_content_type(  # noqa: E501
            ['application/x-www-form-urlencoded', 'multipart/form-data', 'application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['cookieAuth', 'tokenAuth']  # noqa: E501

        return self.api_client.call_api(
            '/api/auth-token/', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_type='AuthToken',  # noqa: E501
            auth_settings=auth_settings,
            async_req=params.get('async_req'),
            _return_http_data_only=params.get('_return_http_data_only'),
            _preload_content=params.get('_preload_content', True),
            _request_timeout=params.get('_request_timeout'),
            collection_formats=collection_formats)
