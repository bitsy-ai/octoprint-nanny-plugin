import socket


class SetupIncompleteError(Exception):
    def __init__(
        self,
        msg=f"PrintNanny registration is incomplete. Please visit http://{socket.gethostname()}/ to finish setup.",
        *args,
        **kwargs,
    ):
        super().__init__(msg, *args, **kwargs)
