from flask import Blueprint


def bp_factory(
    module_name, url_prefix="", template_folder="templates", static_folder="./static"
):
    import_name = "neteye.{}".format(module_name)
    template_folder = template_folder
    url_prefix = "/{}".format(module_name) if url_prefix == "" else url_prefix
    static_folder = static_folder
    blueprint = Blueprint(
        module_name,
        import_name=import_name,
        template_folder=template_folder,
        url_prefix=url_prefix,
        static_folder=static_folder,
    )
    return blueprint


root_bp = bp_factory("")