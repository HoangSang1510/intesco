import inspect

from odoo.addons.base_rest.models import rest_service_registration as main


class InheritRestApiMethodTransformer(main.RestApiMethodTransformer):

    def _inherit_method_to_routes(self, method):
        """
        Generate the restapi.method's routes
        :param method:
        :return: A list of routes used to get access to the method
        """

        method_name = method.__name__
        signature = inspect.signature(method)
        dict_param = signature.parameters

        param_api_path = dict_param.get('api_path', False)

        # Forced-return the pre_defined API paths from
        # the param of the function
        if param_api_path:
            dict_api_path = param_api_path.default

            res = []

            for _k in dict_api_path:
                res.append((dict_api_path[_k], _k))

            return res

        # Without forcing pre_defined API paths from the params of the function
        id_in_path_required = "_id" in dict_param

        path = "/{}".format(method_name)

        if id_in_path_required:
            path = "/<int:id>" + path

        if method_name in ("get", "search"):
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            return [(paths, "GET")]

        elif method_name == "delete":
            routes = [(path, "POST")]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            routes.append((path, "DELETE"))

        elif method_name == "update":
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            routes = [(paths, "POST"), (path, "PUT")]

        elif method_name == "create":
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            routes = [(paths, "POST")]

        else:
            routes = [(path, "POST")]

        return routes

    main.RestApiMethodTransformer._method_to_routes = _inherit_method_to_routes
