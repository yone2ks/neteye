from flask import jsonify, request
from flask_restx import Namespace, Resource, ValidationError, fields, abort

from neteye.api.node_namespace import NodeSchema
from neteye.api.routes import api_bp
from neteye.extensions import api, db, ma
from neteye.interface.models import Interface
from neteye.node.models import Node


class InterfaceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Interface
        load_instance = True


interfaces_schema = InterfaceSchema(many=True)
interface_schema = InterfaceSchema()

interfaces_api = Namespace("interfaces", description="Interfaces API")
api.add_namespace(interfaces_api)

interface_model = interfaces_api.model('Interface', {
    'id': fields.String(description='The UUID of the interface'),
    'node_id': fields.String(description='The node ID this interface belongs to'),
    'name': fields.String(description='The name of the interface'),
    'description': fields.String(description='The description of the interface'),
    'ip_address': fields.String(description='The IP address of the interface'),
    'mask': fields.String(description='The subnet mask of the interface'),
    'speed': fields.String(description='The speed of the interface'),
    'duplex': fields.String(description='The duplex mode of the interface'),
    'mtu': fields.Integer(description='The MTU of the interface'),
    'status': fields.String(description='The status of the interface')
})

@interfaces_api.route("", "/")
class InterfacesResource(Resource):
    @interfaces_api.marshal_list_with(interface_model)
    def get(self):
        return Interface.query.all()

    @interfaces_api.expect(interface_model, validate=True)
    @interfaces_api.marshal_with(interface_model, code=201)
    def post(self):
        try:
            interface = interface_schema.load(api.payload)
            interface.add()
            return interface, 201
        except ValidationError as err:
            abort(400, message=err.messages)


@interfaces_api.route("/<string:id>")
class InterfaceResource(Resource):
    @interfaces_api.marshal_with(interface_model)
    def get(self, id):
        return Interface.query.get_or_404(id)

    @interfaces_api.expect(interface_model)
    @interfaces_api.marshal_with(interface_model)
    def put(self, id):
        interface = Interface.query.get_or_404(id)
        try:
            interface = interface_schema.load(api.payload, instance=interface)
            interface.commit()
            return interface
        except ValidationError as err:
            abort(400, message=err.messages)

    @interfaces_api.response(204, "Interface deleted")
    def delete(self, id):
        interface = Interface.query.get_or_404(id)
        interface.delete()
        return '', 204


@interfaces_api.route("/filter")
class InterfaceResourceFilter(Resource):
    @interfaces_api.marshal_list_with(interface_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if not hasattr(Interface, field):
            abort(400, message=f"Invalid field: {field}")
        results = Interface.query.filter(getattr(Interface, field) == filter_str).all()
        return results
