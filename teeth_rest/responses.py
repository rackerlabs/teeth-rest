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

    def bind_application(self, app, request):
        self.app = app
        self.request = request


class CreatedResponse(ApplicationDependentResponse):
    def __init__(self, location_endpoint, url_parameters):
        super(CreatedResponse, self).__init__(status=201)
        self._location_endpoint = location_endpoint
        self._url_parameters = url_parameters

    def bind_application(self, app, request):
        super(CreatedResponse, self).bind_application(app, request)
        bound_urls = app.url_map.bind_to_environ(request)
        self.headers.set('Location', bound_urls.build(self._location_endpoint, self._url_parameters))


class JSONResponse(ApplicationDependentResponse):
    def __init__(self, obj, status):
        super(JSONResponse, self).__init__(status=status, content_type='application/json')
        self._body_obj = obj

    def bind_application(self, app, request):
        super(JSONResponse, self).bind_application(app, request)
        self.set_data(self.app.encoder.encode(self._body_obj))


class OKResponse(JSONResponse):
    def __init__(self, obj):
        super(OKResponse, self).__init__(obj, 200)
