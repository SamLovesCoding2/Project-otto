from project_otto.host_communications import SelectNewTargetRequestManager
from project_otto.messages import SelectNewTargetMessage
from project_otto.timestamps import JetsonTimestamp
from project_otto.uart import RxHandler


class SelectNewTargetMessageHandler(RxHandler[SelectNewTargetMessage, JetsonTimestamp]):
    """Handler for SelectNewTargetMessage."""

    _msg_cls = SelectNewTargetMessage

    def __init__(self, request_manager: SelectNewTargetRequestManager):
        self._request_manager = request_manager

    def handle(self, msg: SelectNewTargetMessage, timestamp: JetsonTimestamp):
        """
        Registers the received selection request with the backing manager.
        """
        self._request_manager.register_new_selection_message(msg)
