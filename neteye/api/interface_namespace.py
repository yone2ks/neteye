from flask import jsonify, request
from flask_restx import Namespace, Resource, ValidationError
from marshmallow import fields

from neteye.api.node_namespace import NodeSchema
from neteye.api.routes import api_bp
from neteye.extensions import api, db, ma
from neteye.interface.models import Interface
from neteye.node.models import Node


class InterfaceSchema(ma.ModelSchema):
    class Meta:
        model = Interface

    node = fields.Nested(NodeSchema)


interfaces_schema = InterfaceSchema(many=True)
interface_schema = InterfaceSchema()

interfaces_api = Namespace("interfaces")


@api_bp.route("interfaces")
@interfaces_api.route("/")
class InterfacesResource(Resource):
    def get(self):
        return interfaces_schema.jsonify(Interface.query.all())


    def post(self):
        data = request.get_json()
        node = Node.query.get(data['node_id'])
        interface = Interface(
        node_id=data["node_id"],
        name=data["name"],
        description=data["description"],
        ip_address=data["ip_address"],
        mask=data["mask"],
        speed=data["speed"],
        duplex=data["duplex"],
        mtu=data["mtu"],
        status=data["status"],
        )
        interface.add()
        return "create interface"


@interfaces_api.route("/<string:id>")
class InterfaceResource(Resource):
    def get(self, id):
        return interface_schema.jsonify(Interface.query.get(id))


@interfaces_api.route("/filter")
class InterfaceResourceFilter(Resource):
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        results = Interface.query.filter(getattr(Interface, field) == filter_str).all()
        return interfaces_schema.jsonify(results)
