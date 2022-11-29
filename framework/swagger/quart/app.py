from quart import Quart, request
import inspect

app = Quart(__name__)


def get_view_function_args(app, endpoint):
    view_func = app.view_functions[endpoint]
    return list(inspect.signature(view_func).parameters)


@app.route('/api/hello')
async def hello(container=None):
    req = request

    endpoint = req.endpoint
    view_func = app.view_functions[endpoint]
    params = inspect.signature(view_func)

    return 'howdy'


app.run(debug=True)
