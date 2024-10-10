from flask import jsonify, request
from flask_restx import Namespace, Resource
from marshmallow import fields

from neteye.apis.node_namespace import NodeSchema
from neteye.apis.routes import api_bp
from neteye.extensions import api, db, ma
from neteye.serial.models import Serial


class SerialSchema(ma.ModelSchema):
    class Meta:
        model = Serial

    node = fields.Nested(NodeSchema)

serials_schema = SerialSchema(many=True)
serial_schema = SerialSchema()

serials_api = Namespace("serials")


@api_bp.route("serials")
@serials_api.route("/")
class SerialsResource(Resource):
    def get(self):
        return serials_schema.jsonify(Serial.query.all())


@serials_api.route("/<string:id>")
class SerialResource(Resource):
    def get(self, id):
        return serial_schema.jsonify(Serial.query.get(id))


@serials_api.route("/filter")
class SerialResourceFilter(Resource):
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        results = Serial.query.filter(getattr(Serial, field) == filter_str).all()
        return serials_schema.jsonify(results)
