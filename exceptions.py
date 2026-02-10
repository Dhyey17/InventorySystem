class InventoryError(Exception):
    pass

class ItemNotFoundError(InventoryError):
    pass

class InsufficientStockError(InventoryError):
    pass

class UserNotFoundError(InventoryError):
    pass

class UnauthorizedError(InventoryError):
    pass

