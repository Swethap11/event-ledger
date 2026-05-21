class EventNotFoundError(Exception):
    def __init__(self, event_id: str):
        self.event_id = event_id


class AccountNotFoundError(Exception):
    def __init__(self, account_id: str):
        self.account_id = account_id
