Teeth REST
==========

Common REST components for [Teeth
Overlord](https://github.com/rackerlabs/teeth-overlord) and [Teeth
Agent](https://github.com/rackerlabs/teeth-agent).

Example usage:

```python
from teeth_rest import component
from teeth_rest import responses

class ExampleAPI(component.APIComponent):
    def __init__(self):
        """Override the constructor to initialize any state that this API
        component will will need access to. For example, accept a configuration
        and use it to instantiate a database connection.
        """
        super(ExampleAPI).__init__()

    def add_routes(self):
        """Called during initialization. Override to map relative routes to
        methods.
        """
        self.route('GET', '/status', self.get_status)

    def get_status(self, request):
        return responses.ItemResponse({'status': 'OK'})


class ExampleAPIServer(component.APIServer):
    def __init__(self):
        super(ExampleAPIServer, self).__init__()
        self.add_component('/v1.0', ExampleAPI())
```
