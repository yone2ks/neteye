from neteye.base.models import Base
from neteye.interface.models import Interface

def get_records_by_node(model: Base, node_id: str) -> list:
    """
    get related records by node id
    
    Args:
        model (Base): The SQLAlchemy model class.
        node_id (str): The ID of the node to filter by.

    Returns:
        list: List of records filtered by node_id.
    """
    if hasattr(model, 'node_id'):
        return model.query.filter_by(node_id=node_id).all()
    elif hasattr(model, 'interface_id'):
        return model.query.join(Interface).filter(Interface.node_id == node_id).all()
    elif hasattr(model, 'a_interface_id') and hasattr(model, 'b_interface_id'):
        return model.query.filter(
            (model.a_interface.has(Interface.node_id == node_id)) |
            (model.b_interface.has(Interface.node_id == node_id))
        ).all()
    else:
        raise ValueError(f'{model.__name__} has no node_id or interface_id attribute')
