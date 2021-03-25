from flask import jsonify, request
from flask_restplus import Namespace, Resource
from marshmallow import fields

from neteye.apis.interface_namespace import InterfaceSchema
from neteye.apis.routes import api_bp
from neteye.cable.models import Cable
from neteye.extensions import api, db, ma


class CableSchema(ma.ModelSchema):
    class Meta:
        model = Cable

    src_interface = fields.Nested(InterfaceSchema)
    dst_interface = fields.Nested(InterfaceSchema)


cables_schema = CableSchema(many=True)
cable_schema = CableSchema()

cables_api = Namespace("cables")


@api_bp.route("cables")
@cables_api.route("/")
class CablesResource(Resource):
    def get(self):
        return cables_schema.jsonify(Cable.query.all())


@cables_api.route("/<int:id>")
class CableResource(Resource):
    def get(self, id):
        return cable_schema.jsonify(Cable.query.get(id))


@cables_api.route("/filter")
class CableResourceFilter(Resource):
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        results = Cable.query.filter(getattr(Cable, field) == filter_str).all()
        return cables_schema.jsonify(results)
