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

import json
from uuid import UUID

from structlog import get_logger
from werkzeug.routing import Map, Submount, Rule, BaseConverter, ValidationError
from werkzeug.wrappers import BaseRequest
from werkzeug.exceptions import HTTPException, NotFound as WerkzeugNotFound
from werkzeug.http import parse_options_header

from teeth_rest import errors, encoding, responses


class UUIDConverter(BaseConverter):
    """
    Validate and transform UUIDs in urls.
    """

    def __init__(self, url_map):
        super(UUIDConverter, self).__init__(url_map)

    def to_python(self, value):
        """
        Transform a UUID string into a python UUID.
        """
        try:
            return UUID(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        """
        Transform a python UUID into a string.
        """
        return str(value)


class APIServer(object):
    def __init__(self, encoder=None):
        self.log = get_logger()
        self.url_map = Map(converters={'uuid': UUIDConverter})
        if encoder:
            self.encoder = encoder
        else:
            self.encoder = encoding.RESTJSONEncoder(encoding.SerializationViews.PUBLIC, indent=4)

    def __call__(self, environ, start_response):
        request = BaseRequest(environ)
        response = self.dispatch_request(request)
        if isinstance(response, responses.ApplicationDependentResponse):
            response.bind_application(self)
        return response(environ, start_response)

    def add_component(self, prefix, component):
        """
        Route an absolute prefix to a component.
        """
        self.url_map.add(Submount(prefix, component.register_for_rules(self)))

    def dispatch_request(self, request):
        """
        Given a Werkzeug request, generate a Response.
        """
        url_adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = url_adapter.match()
            return endpoint(request, **values)
        except errors.RESTError as e:
            self.log.error('error handling request', exception=e)
            return responses.JSONResponse(e, e.status_code)
        except WerkzeugNotFound as e:
            e = errors.NotFound()
            return responses.JSONResponse(e, e.status_code)
        except Exception as e:
            self.log.error('error handling request', exception=e)
            e = errors.RESTError()
            return responses.JSONResponse(e, e.status_code)


class APIComponent(object):
    """
    Base class for implementing API components.
    """
    def __init__(self):
        self.log = get_logger()
        self.rules = []
        self.app = None
        self.add_routes()

    def __call__(self, environ, start_response):
        request = BaseRequest(environ)
        return self.dispatch_request(request)(environ, start_response)

    def add_routes(self):
        """
        Called during initialization. Override to map relative routes to methods.
        """
        pass

    def route(self, method, pattern, fn):
        """
        Route a relative path to a method.
        """
        if self.app:
            raise RuntimeError('Routes may not be added after an APIComponent is registered with'
                               ' an APIApplication')

        self.rules.append(Rule(pattern, methods=[method], endpoint=fn))

    def register_for_rules(self, app):
        if self.app:
            raise RuntimeError('APIComponents may not be registered with multiple APIApplications')
        self.app = app

        return self.rules

    def parse_content(self, request):
        """
        Extract the content from the passed request, and attempt to
        parse it according to the specified `Content-Type`.

        Note: currently only `application/json` is supported.
        """
        content_type_header = request.headers.get('content-type', default='application/json')
        content_type = parse_options_header(content_type_header)[0]

        if content_type == 'application/json':
            try:
                return json.loads(request.get_data())
            except Exception as e:
                raise errors.InvalidContentError(e.message)
        else:
            raise errors.UnsupportedContentTypeError(content_type)
