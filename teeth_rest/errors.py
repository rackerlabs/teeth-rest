"""
Copyright 2013 Rackspace, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from collections import OrderedDict

from teeth_rest import Serializable


class RESTError(Exception, Serializable):
    """Base class for errors generated in teeth."""
    message = 'An error occurred'
    details = 'An unexpected error occurred. Please try back later.'
    status_code = 500

    def serialize(self, view):
        """Turn a RESTError into a dict."""
        return OrderedDict([
            ('type', self.__class__.__name__),
            ('code', self.status_code),
            ('message', self.message),
            ('details', self.details),
        ])


class UnsupportedContentTypeError(RESTError):
    """
    Error which occurs when a user supplies an unsupported
    `Content-Type` (ie, anything other than `application/json`).
    """
    message = 'Unsupported Content-Type'
    status_code = 400

    def __init__(self, content_type):
        self.details = 'Content-Type "{content_type}" is not supported'.format(content_type=content_type)


class InvalidContentError(RESTError):
    """
    Error which occurs when a user supplies invalid content, either
    because that content cannot be parsed according to the advertised
    `Content-Type`, or due to a content validation error.
    """
    message = 'Invalid request body'
    status_code = 400

    def __init__(self, details):
        self.details = details
