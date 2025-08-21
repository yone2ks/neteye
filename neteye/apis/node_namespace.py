from flask import jsonify, request
from flask_restx import Namespace, Resource, ValidationError, fields, abort

from neteye.extensions import api, ma
from neteye.node.models import Node
import neteye.node.routes as node_imports


class NodeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Node
        load_instance = True

nodes_schema = NodeSchema(many=True)
node_schema = NodeSchema()


nodes_api = Namespace("nodes", description="Nodes API")
api.add_namespace(nodes_api)

node_model = nodes_api.model('Node', {
    'id': fields.String(description='The UUID of the node'),
    'hostname': fields.String(description='The hostname of the node'),
    'description': fields.String(description='The description of the node'),
    'ip_address': fields.String(description='The IP address of the node'),
    'port': fields.Integer(description='The port number of the node'),
    'device_type': fields.String(description='The device type of the node'),
    'scrapli_driver': fields.String(description='The Scrapli driver used by the node'),
    'napalm_driver': fields.String(description='The NAPALM driver used by the node'),
    'ntc_template_platform': fields.String(description='The NTC template platform'),
    'model': fields.String(description='The model of the node'),
    'os_type': fields.String(description='The OS type of the node'),
    'os_version': fields.String(description='The OS version of the node'),
    'username': fields.String(description='The username of the node'),
    'password': fields.String(description='The password of the node'),
    'enable': fields.String(description='The enable password of the node')
})

@nodes_api.route("","/")
class NodesResource(Resource):
    @nodes_api.marshal_list_with(node_model)
    def get(self):
        return Node.query.all()

    @nodes_api.expect(node_model, validate=True)
    @nodes_api.marshal_with(node_model, code=201)
    def post(self):
        try:
            node = node_schema.load(api.payload)
            node.add()
            return node, 201
        except ValidationError as err:
            abort(400, message=err.messages)

@nodes_api.route("/<string:id>")
class NodeResource(Resource):
    @nodes_api.marshal_with(node_model)
    def get(self, id):
        return Node.query.get_or_404(id)

    @nodes_api.expect(node_model)
    @nodes_api.marshal_with(node_model)
    def put(self, id):
        node = Node.query.get_or_404(id)
        try:
            node = node_schema.load(api.payload, instance=node)
            node.commit()
            return node
        except ValidationError as err:
            abort(400, message=err.messages)

    @nodes_api.response(204, "Node deleted")
    def delete(self, id):
        node = Node.query.get_or_404(id)
        node.delete()
        return '', 204


@nodes_api.route("/filter")
class NodeResourceFilter(Resource):
    @nodes_api.marshal_list_with(node_model)
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        if not hasattr(Node, field):
            abort(400, message=f"Invalid field: {field}")
        nodes = Node.query.filter(getattr(Node, field) == filter_str).all()
        return nodes


@nodes_api.route("/<string:id>/command/<string:command>")
class NodeResourceCommand(Resource):
    def get(self, id, command):
        command = command.replace("+", " ")
        node = Node.query.get_or_404(id)
        result = node.command(command)
        return jsonify(result)


@nodes_api.route("/<string:id>/raw_command/<string:command>")
class NodeResourceRawCommand(Resource):
    def get(self, id, command):
        command = command.replace("+", " ")
        node = Node.query.get_or_404(id)
        result = node.raw_command(command)
        return jsonify(result)


@nodes_api.route("/<string:id>/import/node")
class NodeImportNode(Resource):
    @nodes_api.marshal_with(node_model)
    def post(self, id):
        node = Node.query.get_or_404(id)
        node_imports.import_node_data(node)
        return node, 200


@nodes_api.route("/<string:id>/import/serial")
class NodeImportSerial(Resource):
    def post(self, id):
        node = Node.query.get_or_404(id)
        node_imports.import_serials(node)
        return {"message": f"Serials imported for node {node.hostname}"}, 200


@nodes_api.route("/<string:id>/import/interface")
class NodeImportInterface(Resource):
    def post(self, id):
        node = Node.query.get_or_404(id)
        node_imports.import_interfaces(node)
        return {"message": f"Interfaces imported for node {node.hostname}"}, 200


@nodes_api.route("/<string:id>/import/arp_entry")
class NodeImportArpEntry(Resource):
    def post(self, id):
        node = Node.query.get_or_404(id)
        node_imports.import_arp_entries(node)
        return {"message": f"ARP entries imported for node {node.hostname}"}, 200


@nodes_api.route("/<string:id>/import/all_data")
class NodeImportAll(Resource):
    def post(self, id):
        node = Node.query.get_or_404(id)
        node_imports.import_all_data(node)
        return {"message": f"All data imported for node {node.hostname}"}, 200
