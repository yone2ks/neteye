from dictdiffer import diff

from neteye.base.models import Base

CHANGE = "change"
REMOVE = "remove"
ADD = "add"


def delta_commit(model: Base, before_keys: set, before: dict, after_keys: set, after: dict) -> None:
    delta = tuple(diff(before_keys, after_keys))
    for diff_type, diff_target, diff_content in delta:
        if diff_type == REMOVE:
            for index, keys in diff_content:
                for key in keys:
                    instance = model.query.get(before[key]["id"])
                    instance.delete()
        elif diff_type == ADD:
            for index, keys in diff_content:
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
