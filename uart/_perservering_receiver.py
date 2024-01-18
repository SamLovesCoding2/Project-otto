import logging
from typing import Optional

from ._message_receiver import HostMessageReceiver
from ._transceiver import MessageParseUnhandledError


class PerseveringReceiver(HostMessageReceiver):
    """
    A receiver that perseveres past message parse errors.

    Otherwise, it has the same functionality as the "child" receiver that is passed in.

    Args:
        child_receiver: The receiver that will have added functionality as a persevering receiver.
        max_num_parse_errors: The maximum number of message parse errors that will be ignored.
    """

    child_receiver: HostMessageReceiver
    max_num_parse_errors: int
    error_counter: int

    def __init__(self, receiver: HostMessageReceiver, num_of_errors: int):
        self.child_receiver = receiver
        self.max_num_parse_errors = num_of_errors
        self.error_counter = 0

    def process_in(self, max_packets: Optional[int] = None):
        """
        Executes the "read message" method of the child receiver.

        Ignores message parse errors until max_num_of_errors times. After max_num_of_errors times,
        an exception is thrown notifying that too many message parse errors have occured.

        If any other error occurs, that error is thrown back as an exception.
        """
        # While a message has not been successfully processed.
        while True:
            # If a message has successfully processed, just reset the persevering receiver.
            try:
                self.child_receiver.process_in(max_packets)
                break

            # If message has failed to parse, increment the number of times a message parse error
            # has been raised.
            except MessageParseUnhandledError:
                self.error_counter += 1

                logging.error("Failed to parse message.", exc_info=True)

                # Upon reaching the max number of message parse errors, crash the program.
                if self.error_counter >= self.max_num_parse_errors:
                    self.error_counter = 0
                    raise Exception("Too many messages failed to parse.")

            # If message cannot be processed due to any other error,
            # just raise the error and continue as normal.
            except Exception as error:
                logging.error("Unable to handle message.", exc_info=True)
                raise error

    def reset_states(self):
        """
        Resets the states of the child receiver.
        """
        self.child_receiver.reset_states()
