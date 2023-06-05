class StripeException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Error during stripe API call"
        super().__init__(msg)
