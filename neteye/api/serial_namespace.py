from flask import jsonify, request
from flask_restx import Namespace, ValidationError, fields, abort

from neteye.api.node_namespace import NodeSchema
from neteye.api.routes import api_bp
from neteye.api.routes import AuthenticatedResource
from neteye.extensions import api, db, ma
from neteye.serial.models import Serial


class SerialSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Serial
        load_instance = True

serials_schema = SerialSchema(many=True)
serial_schema = SerialSchema()

serials_api = Namespace("serials", description="Serials API")
api.add_namespace(serials_api)

serial_model = serials_api.model('Serial', {
    'id': fields.String(description='The UUID of the serial'),
    'node_id': fields.String(description='The node ID this serial belongs to'),
    'serial': fields.String(description='The serial number'),
    'description': fields.String(description='The description of the serial')
})

@serials_api.route("", "/")
class SerialsResource(AuthenticatedResource):
    @serials_api.marshal_list_with(serial_model)
    def get(self):
        return Serial.query.all()

    @serials_api.expect(serial_model, validate=True)
    @serials_api.marshal_with(serial_model, code=201)
    def post(self):
        try:
            serial = serial_schema.load(api.payload)
            serial.add()
            return serial, 201
        except ValidationError as err:
            abort(400, message=err.messages)


@serials_api.route("/<string:id>")
class SerialResource(AuthenticatedResource):
    @serials_api.marshal_with(serial_model)
    def get(self, id):
        return db.get_or_404(Serial, id)

    @serials_api.expect(serial_model)
    @serials_api.marshal_with(serial_model)
    def put(self, id):
        serial = db.get_or_404(Serial, id)
        try:
            serial = serial_schema.load(api.payload, instance=serial)
            serial.commit()
            return serial
        except ValidationError as err:
            abort(400, message=err.messages)

    @serials_api.response(204, "Serial deleted")
    def delete(self, id):
        serial = db.get_or_404(Serial, id)
        serial.delete()
        return '', 204


SERIAL_FILTER_FIELDS = {"serial_number", "product_id", "description"}

@serials_api.route("/filter")
class SerialResourceFilter(AuthenticatedResource):
    @serials_api.marshal_list_with(serial_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if field not in SERIAL_FILTER_FIELDS:
            abort(400, message=f"Invalid field: {field}. Allowed: {sorted(SERIAL_FILTER_FIELDS)}")
        results = Serial.query.filter(getattr(Serial, field) == filter_str).all()
        return results
