from flask import jsonify, request
from flask_restx import Namespace, Resource

from neteye.apis.routes import api_bp
from neteye.extensions import api, db, ma
from neteye.history.models import (OPERATION_TYPE, arp_entry_transaction,
                                   arp_entry_version, cable_transaction,
                                   cable_version, interface_transaction,
                                   interface_version, node_transaction,
                                   node_version, serial_transaction,
                                   serial_version)


class NodeVersionSchema(ma.ModelSchema):
    class Meta:
        model = node_version


node_versions_schema = NodeVersionSchema(many=True)
node_version_schema = NodeVersionSchema()


class NodeTransactionSchema(ma.ModelSchema):
    class Meta:
        model = node_transaction


node_transactions_schema = NodeTransactionSchema(many=True)
node_transaction_schema = NodeTransactionSchema()


class InterfaceVersionSchema(ma.ModelSchema):
    class Meta:
        model = interface_version


interface_versions_schema = InterfaceVersionSchema(many=True)
interface_version_schema = InterfaceVersionSchema()


class InterfaceTransactionSchema(ma.ModelSchema):
    class Meta:
        model = interface_transaction


interface_transactions_schema = InterfaceTransactionSchema(many=True)
interface_transaction_schema = InterfaceTransactionSchema()


class SerialVersionSchema(ma.ModelSchema):
    class Meta:
        model = serial_version


serial_versions_schema = SerialVersionSchema(many=True)
serial_version_schema = SerialVersionSchema()


class SerialTransactionSchema(ma.ModelSchema):
    class Meta:
        model = serial_transaction


serial_transactions_schema = SerialTransactionSchema(many=True)
serial_transaction_schema = SerialTransactionSchema()


class CableVersionSchema(ma.ModelSchema):
    class Meta:
        model = cable_version


cable_versions_schema = CableVersionSchema(many=True)
cable_version_schema = CableVersionSchema()


class CableTransactionSchema(ma.ModelSchema):
    class Meta:
        model = cable_transaction


cable_transactions_schema = CableTransactionSchema(many=True)
cable_transaction_schema = CableTransactionSchema()


class ArpEntryVersionSchema(ma.ModelSchema):
    class Meta:
        model = arp_entry_version


arp_entry_versions_schema = ArpEntryVersionSchema(many=True)
arp_entry_version_schema = ArpEntryVersionSchema()


class ArpEntryTransactionSchema(ma.ModelSchema):
    class Meta:
        model = arp_entry_transaction


arp_entry_transactions_schema = ArpEntryTransactionSchema(many=True)
arp_entry_transaction_schema = ArpEntryTransactionSchema()


history_api = Namespace("history")
