from dictdiffer import diff

from neteye.base.models import Base


def dynamic_filter(model: Base, filter_condition: dict):
    for attribute, value in filter_condition.items():
        query = model.query
        for attribute, value in filter_condition.items():
            query = query.filter(getattr(model, attribute) == value)
        return query.first()


CHANGE = "change"
REMOVE = "remove"
ADD = "add"


def delta_commit(model: Base, before: list, after: list) -> None:
    delta = tuple(diff(before, after))
    for diff_type, diff_target, diff_content in delta:
        if diff_type == CHANGE:
            index, attribute = diff_target
            instance = dynamic_filter(model, before[index])
            setattr(instance, attribute, diff_content[1])
            instance.commit()
        elif diff_type == REMOVE:
            for index, filter_condition in diff_content:
                instance = dynamic_filter(model, filter_condition)
                instance.delete()
        elif diff_type == ADD:
            for index, filter_condition in diff_content:
                instance = model()
                for attribute, value in filter_condition.items():
                    setattr(instance, attribute, value)
                instance.add()
