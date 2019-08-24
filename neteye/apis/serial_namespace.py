from flask import jsonify, request
from flask_restplus import Resource, Namespace
from neteye.serial.models import Serial
from neteye.extensions import ma, api, db
from neteye.apis.routes import api_bp

class SerialSchema(ma.ModelSchema):
    class Meta:
        model = Serial

serials_schema = SerialSchema(many=True)
serial_schema= SerialSchema()

serials_api = Namespace('serials')

@api_bp.route('serials')
@serials_api.route('/')
class SerialsResource(Resource):
    def get(self):
        return serials_schema.jsonify(Serial.query.all())

@serials_api.route('/<int:id>')
class SerialResource(Resource):
    def get(self, id):
        return serial_schema.jsonify(Serial.query.get(id))
