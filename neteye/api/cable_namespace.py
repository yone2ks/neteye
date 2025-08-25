from flask import jsonify, request
from flask_restx import Namespace, Resource, ValidationError, fields, abort

from neteye.api.interface_namespace import InterfaceSchema
from neteye.api.routes import api_bp
from neteye.cable.models import Cable
from neteye.extensions import api, db, ma


class CableSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cable
        load_instance = True


cables_schema = CableSchema(many=True)
cable_schema = CableSchema()

cables_api = Namespace("cables", description="Cables API")
api.add_namespace(cables_api)

cable_model = cables_api.model('Cable', {
    'id': fields.String(description='The UUID of the cable'),
    'src_node_id': fields.String(description='The source node ID'),
    'src_interface_id': fields.String(description='The source interface ID'),
    'dst_node_id': fields.String(description='The destination node ID'),
    'dst_interface_id': fields.String(description='The destination interface ID'),
    'description': fields.String(description='The description of the cable')
})

@cables_api.route("", "/")
class CablesResource(Resource):
    @cables_api.marshal_list_with(cable_model)
    def get(self):
        return Cable.query.all()

    @cables_api.expect(cable_model, validate=True)
    @cables_api.marshal_with(cable_model, code=201)
    def post(self):
        try:
            cable = cable_schema.load(api.payload)
            cable.add()
            return cable, 201
        except ValidationError as err:
            abort(400, message=err.messages)


@cables_api.route("/<string:id>")
class CableResource(Resource):
    @cables_api.marshal_with(cable_model)
    def get(self, id):
        return Cable.query.get_or_404(id)

    @cables_api.expect(cable_model)
    @cables_api.marshal_with(cable_model)
    def put(self, id):
        cable = Cable.query.get_or_404(id)
        try:
            cable = cable_schema.load(api.payload, instance=cable)
            cable.commit()
            return cable
        except ValidationError as err:
            abort(400, message=err.messages)

    @cables_api.response(204, "Cable deleted")
    def delete(self, id):
        cable = Cable.query.get_or_404(id)
        cable.delete()
        return '', 204


@cables_api.route("/filter")
class CableResourceFilter(Resource):
    @cables_api.marshal_list_with(cable_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if not hasattr(Cable, field):
            abort(400, message=f"Invalid field: {field}")
        results = Cable.query.filter(getattr(Cable, field) == filter_str).all()
        return results
