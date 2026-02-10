from exceptions import UnauthorizedError


def login_required(session):
    if "seller_id" not in session:
        raise UnauthorizedError

