from flask import jsonify, request
from flask_restx import Namespace, Resource
from marshmallow import fields

from neteye.apis.interface_namespace import InterfaceSchema
from neteye.apis.routes import api_bp
from neteye.arp_entry.models import ArpEntry
from neteye.extensions import api, db, ma


class ArpEntrySchema(ma.ModelSchema):
    class Meta:
        model = ArpEntry

    interface = fields.Nested(InterfaceSchema)


arp_entries_schema = ArpEntrySchema(many=True)
arp_entry_schema = ArpEntrySchema()

arp_entries_api = Namespace("arp_entries")


@api_bp.route("arp_entries")
@arp_entries_api.route("/")
class ArpEntrysResource(Resource):
    def get(self):
        return arp_entries_schema.jsonify(ArpEntry.query.all())


@arp_entries_api.route("/<string:id>")
class ArpEntryResource(Resource):
    def get(self, id):
        return arp_entry_schema.jsonify(ArpEntry.query.get(id))


@arp_entries_api.route("/filter")
class ArpEntryResourceFilter(Resource):
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        results = ArpEntry.query.filter(getattr(ArpEntry, field) == filter_str).all()
        return arp_entries_schema.jsonify(results)
