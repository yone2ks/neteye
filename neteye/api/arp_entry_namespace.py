from flask import jsonify, request
from flask_restx import Namespace, Resource, ValidationError, fields, abort

from neteye.api.interface_namespace import InterfaceSchema
from neteye.api.routes import api_bp
from neteye.arp_entry.models import ArpEntry
from neteye.extensions import api, db, ma


class ArpEntrySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArpEntry
        load_instance = True


arp_entries_schema = ArpEntrySchema(many=True)
arp_entry_schema = ArpEntrySchema()

arp_entries_api = Namespace("arp_entries", description="ARP Entries API")
api.add_namespace(arp_entries_api)

arp_entry_model = arp_entries_api.model('ArpEntry', {
    'id': fields.String(description='The UUID of the ARP entry'),
    'node_id': fields.String(description='The node ID this ARP entry belongs to'),
    'ip_address': fields.String(description='The IP address of the ARP entry'),
    'mac_address': fields.String(description='The MAC address of the ARP entry'),
    'interface': fields.String(description='The interface of the ARP entry')
})

@arp_entries_api.route("", "/")
class ArpEntrysResource(Resource):
    @arp_entries_api.marshal_list_with(arp_entry_model)
    def get(self):
        return ArpEntry.query.all()

    @arp_entries_api.expect(arp_entry_model, validate=True)
    @arp_entries_api.marshal_with(arp_entry_model, code=201)
    def post(self):
        try:
            arp_entry = arp_entry_schema.load(api.payload)
            arp_entry.add()
            return arp_entry, 201
        except ValidationError as err:
            abort(400, message=err.messages)


@arp_entries_api.route("/<string:id>")
class ArpEntryResource(Resource):
    @arp_entries_api.marshal_with(arp_entry_model)
    def get(self, id):
        return ArpEntry.query.get_or_404(id)

    @arp_entries_api.expect(arp_entry_model)
    @arp_entries_api.marshal_with(arp_entry_model)
    def put(self, id):
        arp_entry = ArpEntry.query.get_or_404(id)
        try:
            arp_entry = arp_entry_schema.load(api.payload, instance=arp_entry)
            arp_entry.commit()
            return arp_entry
        except ValidationError as err:
            abort(400, message=err.messages)

    @arp_entries_api.response(204, "ARP entry deleted")
    def delete(self, id):
        arp_entry = ArpEntry.query.get_or_404(id)
        arp_entry.delete()
        return '', 204


@arp_entries_api.route("/filter")
class ArpEntryResourceFilter(Resource):
    @arp_entries_api.marshal_list_with(arp_entry_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if not hasattr(ArpEntry, field):
            abort(400, message=f"Invalid field: {field}")
        results = ArpEntry.query.filter(getattr(ArpEntry, field) == filter_str).all()
        return results
