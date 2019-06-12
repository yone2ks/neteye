from flask import jsonify, request
from flask_restplus import Resource, Namespace
from neteye.interface.models import Interface
from neteye.extensions import ma, api, db
from neteye.apis.routes import api_bp

class InterfaceSchema(ma.ModelSchema):
    class Meta:
        model = Interface

interfaces_schema = InterfaceSchema(many=True)
interface_schema= InterfaceSchema()

interfaces_api = Namespace('interfaces')

@api_bp.route('interfaces')
@interfaces_api.route('/')
class InterfacesResource(Resource):
    def get(self):
        return interfaces_schema.jsonify(Interface.query.all())

@interfaces_api.route('/<int:id>')
class InterfaceResource(Resource):
    def get(self, id):
        return interface_schema.jsonify(Interface.query.get(id))

