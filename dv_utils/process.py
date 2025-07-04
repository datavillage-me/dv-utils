"""
This module defines a dummy event processor as an example.
"""
import time
from .log_utils import log, LogLevel

from .client import Client



def process_event_dummy(evt: dict):
    """
    Process an incoming event
    """
    start = time.time()

    try:
        log(f"Processing event {evt}", LogLevel.INFO)

        client = Client()

        # Use userIds provided in the event, or get all active users for this application
        user_ids = evt.get("userIds") if "userIds" in evt else client.get_users()

        log(f"Processing {len(user_ids)} users", LogLevel.INFO)
        for user_id in user_ids:
            try:

                # retrieve data graph for user
                user_data = client.get_data(user_id)

                log(f"{len(user_data)} statements for user {user_id}", LogLevel.INFO)

                # for the sake of this example, write some RDF with the number of user statements into the user's pod
                client.write_results(
                    user_id,
                    "inferences",
                    f"<https://datavillage.me/{user_id}> <https://datavillage.me/count> {len(user_data)}",
                )

            # pylint: disable=broad-except
            except Exception as err:
                log(f"Failed to process user {user_id} : {err}", LogLevel.WARN)

    # pylint: disable=broad-except
    except Exception as err:
        log(f"Failed processing event: {err}", LogLevel.ERROR)
    finally:
        log(f"Processed event in {time.time() - start:.{3}f}s", LogLevel.INFO)
