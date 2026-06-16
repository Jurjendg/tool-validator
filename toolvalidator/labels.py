LABEL_ORDER = ["A++++", "A+++", "A++", "A+", "A", "B", "C", "D", "E", "F", "G"]


def label_from_beng2(score: float | None) -> str | None:
    if score is None:
        return None
    if score <= 0:
        return "A++++"
    if score <= 50:
        return "A+++"
    if score <= 75:
        return "A++"
    if score <= 105:
        return "A+"
    if score <= 160:
        return "A"
    if score <= 190:
        return "B"
    if score <= 250:
        return "C"
    if score <= 290:
        return "D"
    if score <= 335:
        return "E"
    if score <= 380:
        return "F"
    return "G"


def label_distance(left: str | None, right: str | None) -> int | None:
    if left is None or right is None:
        return None
    try:
        return abs(LABEL_ORDER.index(left) - LABEL_ORDER.index(right))
    except ValueError:
        return None

