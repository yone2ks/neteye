from flask import jsonify, request
from flask_restx import Namespace, ValidationError, fields, abort

from neteye.api.interface_namespace import InterfaceSchema
from neteye.api.routes import api_bp
from neteye.cable.models import Cable
from neteye.api.routes import AuthenticatedResource
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
    'a_interface_id': fields.String(description='The A-side interface ID'),
    'b_interface_id': fields.String(description='The B-side interface ID'),
    'cable_type': fields.String(description='The type of the cable'),
    'link_speed': fields.String(description='The link speed'),
    'description': fields.String(description='The description of the cable')
})

@cables_api.route("", "/")
class CablesResource(AuthenticatedResource):
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
class CableResource(AuthenticatedResource):
    @cables_api.marshal_with(cable_model)
    def get(self, id):
        return db.get_or_404(Cable, id)

    @cables_api.expect(cable_model)
    @cables_api.marshal_with(cable_model)
    def put(self, id):
        cable = db.get_or_404(Cable, id)
        try:
            cable = cable_schema.load(api.payload, instance=cable)
            cable.commit()
            return cable
        except ValidationError as err:
            abort(400, message=err.messages)

    @cables_api.response(204, "Cable deleted")
    def delete(self, id):
        cable = db.get_or_404(Cable, id)
        cable.delete()
        return '', 204


CABLE_FILTER_FIELDS = {"cable_type", "description", "link_speed"}

@cables_api.route("/filter")
class CableResourceFilter(AuthenticatedResource):
    @cables_api.marshal_list_with(cable_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if field not in CABLE_FILTER_FIELDS:
            abort(400, message=f"Invalid field: {field}. Allowed: {sorted(CABLE_FILTER_FIELDS)}")
        results = Cable.query.filter(getattr(Cable, field) == filter_str).all()
        return results
