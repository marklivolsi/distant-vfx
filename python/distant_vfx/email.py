import yagmail


class EmailHandler:

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.recipients = None
        self.events = []

