import time

import beam
import lid
import rfid

DELAY_AFTER_OPEN_S = 5
DELAY_BEFORE_CLOSE_S = 4

class State:
    CLOSED = 0
    JUST_OPENED= 1
    OPEN = 2
    CLOSE_PENDING = 3

state = State.CLOSED
last_action_time = 0

last_is_object_present = False

print("-> Monitoring for cat to arrive...")
while True:
    is_tag_present, tag_id = rfid.is_tag_present()
    is_object_present = beam.is_object_present()

    if is_tag_present:
        print("Tag detected: %s" % tag_id)

    # Only print on detection change
    if last_is_object_present is not is_object_present:
            print(
              "Beam object detected" \
              if is_object_present \
              else "Beam object no longer detected"
            )
            last_is_object_present = is_object_present

    # JUST_OPENED: Cat arrived
    if state is State.CLOSED:
        if is_tag_present:
            print("-> Cat arrived, opening...")
            lid.open()
            state = State.JUST_OPENED
            last_action_time = time.monotonic_ns()
            print("-> Open, waiting %ds grace period..." % DELAY_AFTER_OPEN_S)
    # OPEN: After grace period for cat to enter beam
    elif state is State.JUST_OPENED:
        since_open_s = (time.monotonic_ns() - last_action_time) / 1e9
        if since_open_s >= DELAY_AFTER_OPEN_S:
            print("-> Open grace period over, monitoring for cat to leave...")
            state = State.OPEN

    # CLOSE_PENDING: Cat gone
    elif state is State.OPEN:
        if not is_tag_present and not is_object_present:
            print("-> Cat gone, waiting to make sure...")
            state = State.CLOSE_PENDING
            last_action_time = time.monotonic_ns()

    # CLOSE: After cat has been confirmed gone for period
    elif state is State.CLOSE_PENDING:
        if is_tag_present or is_object_present:
            print("-> Cat back, canceling pending close.")
            state = State.OPEN
        else:
            since_close_s = (time.monotonic_ns() - last_action_time) / 1e9
            if since_close_s >= DELAY_BEFORE_CLOSE_S:
                print("Closing after waiting %ds..." % since_close_s)
                lid.close()
                state = State.CLOSED
                print("Closed, monitoring for cat to arrive...")
