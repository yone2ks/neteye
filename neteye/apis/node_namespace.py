from flask import jsonify, request
from flask_restx import Namespace, Resource

from neteye.apis.routes import api_bp
from neteye.extensions import api, db, ma
from neteye.node.models import Node


class NodeSchema(ma.ModelSchema):
    class Meta:
        model = Node


nodes_schema = NodeSchema(many=True)
node_schema = NodeSchema()

nodes_api = Namespace("nodes")


@api_bp.route("nodes")
@nodes_api.route("/")
class NodesResource(Resource):
    def get(self):
        return nodes_schema.jsonify(Node.query.all())

    def post(self):
        try:
            data = node_schema.load(request.get_json())
        except ValidationError as err:
            errors = err.messages
            valid_data = err.valid_data
        db.session.add(data)
        db.session.commit()
        return "create node"


@nodes_api.route("/<int:id>")
class NodeResource(Resource):
    def get(self, id):
        return node_schema.jsonify(Node.query.get(id))

    def put(self, id):
        data, errors = node_schema.load(request.get_json())
        node = Node.query.get(id)
        node.hostname = data.hostname
        node.description = data.description
        node.ip_address = data.ip_address
        node.username = data.username
        node.password = data.password
        node.enable = data.enable
        db.session.commit()
        return "update node"

    def delete(self, id):
        node = Node.query.get(id)
        db.session.delete(node)
        db.session.commit()
        return "delete node"


@nodes_api.route("/filter")
class NodeResourceFilter(Resource):
    def get(self):
        field = request.args.get("field")
        filter_str = request.args.get("filter_str")
        results = Node.query.filter(getattr(Node, field) == filter_str).all()
        return nodes_schema.jsonify(results)


@nodes_api.route("/<string:id>/command/<string:command>")
class NodeResourceCommand(Resource):
    def get(self, id, command):
        command = command.replace("_", " ")
        node = Node.query.get(id)
        result = node.command(command)
        return jsonify(result)


@nodes_api.route("/<string:id>/raw_command/<string:command>")
class NodeResourceRawCommand(Resource):
    def get(self, id, command):
        command = command.replace("_", " ")
        node = Node.query.get(id)
        result = node.raw_command(command)
        return jsonify(result)
