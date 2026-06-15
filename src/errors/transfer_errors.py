class TransferError(Exception):
    pass


class InsufficientFundsError(TransferError):
    pass


class OriginAccountNotFoundError(TransferError):
    pass


class DestinationAccountNotFoundError(TransferError):
    pass


class InvalidAmountError(TransferError):
    pass


class SameAccountTransferError(TransferError):
    pass


class IdempotencyConflictError(TransferError):
    pass


class TransferNotFoundError(TransferError):
    pass


class TransferAccessDeniedError(TransferError):
    pass
