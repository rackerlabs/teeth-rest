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

from werkzeug.wrappers import BaseResponse


class ApplicationDependentResponse(BaseResponse):
    def __init__(self, *args, **kwargs):
        super(ApplicationDependentResponse, self).__init__(*args, **kwargs)
        self.app = None

    def __call__(self, *args, **kwargs):
        if not self.app:
            raise RuntimeError('ApplicationDependentResponse called prior to bind_application() call')

        return super(ApplicationDependentResponse, self).__call__(*args, **kwargs)

    def bind_application(self, app):
        self.app = app


class CreatedResponse(ApplicationDependentResponse):
    def __init__(self, request, location_endpoint, url_parameters):
        super(CreatedResponse, self).__init__(status=201)
        self._request = request
        self._location_endpoint = location_endpoint
        self._url_parameters = url_parameters

    def bind_application(self, app):
        super(CreatedResponse, self).bind_application(app)
        bound_urls = app.url_map.bind_to_environ(self._request)
        location = bound_urls.build(self._location_endpoint, self._url_parameters, force_external=True)
        self.headers.set('Location', location)


class DeletedResponse(BaseResponse):
    def __init__(self):
        super(DeletedResponse, self).__init__(status=204)


class UpdatedResponse(BaseResponse):
    def __init__(self, status=204, **kwargs):
        super(UpdatedResponse, self).__init__(status=status, **kwargs)


class JSONResponse(ApplicationDependentResponse):
    def __init__(self, obj, status):
        super(JSONResponse, self).__init__(status=status, content_type='application/json')
        self._body_obj = obj

    def bind_application(self, app):
        super(JSONResponse, self).bind_application(app)
        self.set_data(self.app.encoder.encode(self._body_obj))


class ItemResponse(JSONResponse):
    def __init__(self, obj):
        super(ItemResponse, self).__init__(obj, 200)


class PaginatedResponse(ApplicationDependentResponse):
    def __init__(self, request, objs, list_endpoint, marker, limit, **kwargs):
        super(PaginatedResponse, self).__init__(status=200)
        self._request = request
        self._objs = objs
        self._list_endpoint = list_endpoint
        self._url_parameters = kwargs
        self._url_parameters['limit'] = limit
        self._url_parameters['marker'] = marker

    def bind_application(self, app):
        super(PaginatedResponse, self).bind_application(app)
        bound_urls = app.url_map.bind_to_environ(self._request)
        links = []

        if self._url_parameters['marker'] is not None:
            next_href = bound_urls.build(self._list_endpoint, self._url_parameters, force_external=True)
            links.append({'rel': 'next', 'href': next_href})

        data = {'items': self._objs, 'links': links}
        self.set_data(self.app.encoder.encode(data))
