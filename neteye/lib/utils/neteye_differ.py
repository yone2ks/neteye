from dictdiffer import diff

from neteye.base.models import Base

CHANGE = "change"
REMOVE = "remove"
ADD = "add"


def delta_commit(model: Base, before_keys: set, before: dict, after_keys: set, after: dict) -> None:
    """
    Apply the differences between the 'before' and 'after' states to the database.

    Args:
        model (Base): The SQLAlchemy model class.
        before_keys (set): The set of keys identifying objects in the model before the changes (e.g., interface names, serial numbers).
        before (dict): The dictionary of objects in the model before the changes.
        after_keys (set): The set of keys identifying objects in the model after the changes.
        after (dict): The dictionary of objects in the model after the changes.

    Notes:
        - The model must have the id column.

    Examples:
        - before_keys = {"eth0", "eth1"}
        - before = {"eth0": {"id": 1, "name": "eth0", "ip_address": "192.168.0.1"}, "eth1": {"id": 2, "name": "eth1", "ip_address": ""}}
        - after_keys = {"eth0", "eth2", "eth3"}
        - after = {"eth0": {"id": 1, "name": "eth0", "ip_address": ""}, "eth2": {"id": 3, "name": "eth2", "ip_address": "192.168.10.2"}, "eth3": {"id": 4, "name": "eth3", "ip_address": "192.168.10.3"}}
        - delta = (('add', '', [(0, {'eth2', 'eth3'})]), ('remove', '', [(0, {'eth1'})]))
        - dup = {'eth0'}
        - attr_delta = (('change', 'ip_address', ('192.168.0.1', '')),) # eth0's attributes
    """
    delta = tuple(diff(before_keys, after_keys))
    for diff_type, diff_target, diff_content in delta:
        if diff_type == REMOVE:
            for _, keys in diff_content:
                for key in keys:
                    instance = model.query.get(before[key]["id"])
                    instance.delete()
        elif diff_type == ADD:
            for _, keys in diff_content:
                for key in keys:
                    instance = model(**after[key])
                    instance.add()
    dup = before_keys & after_keys
    for key in dup:
        attr_delta = tuple(diff(before[key], after[key], ignore=set(["id"])))
        for diff_type, diff_target, diff_content in attr_delta:
            if diff_type == CHANGE:
                instance = model.query.get(before[key]["id"])
                setattr(instance, diff_target, diff_content[1])
                instance.commit()
