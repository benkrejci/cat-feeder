import time

import beam
import lid
import rfid

import board
import digitalio
import time

DELAY_AFTER_OPEN_S = 0
DELAY_BEFORE_CLOSE_S = 0.75

BUTTON_LED_PIN = board.D3
BUTTON_INPUT_PIN = board.D0

button_led = digitalio.DigitalInOut(BUTTON_LED_PIN)
button_led.direction = digitalio.Direction.OUTPUT
button_led.value = True
button_input = digitalio.DigitalInOut(BUTTON_INPUT_PIN)
button_input.pull = digitalio.Pull.UP

class State:
    CLOSED = 0
    JUST_OPENED= 1
    OPEN = 2
    CLOSE_PENDING = 3
    MANUALLY_OPENED = 4

state = State.CLOSED
last_action_time_ns = 0

last_is_object_present = False

def error_light():
    while True:
        button_led.value = not button_led.value
        time.sleep(0.5)


if beam.is_object_present():
    print("ERROR: Beam object detection on startup; possible broken connection")
    error_light()

print("-> Monitoring for cat to arrive...")
try:
    while True:
        is_tag_present, tag_id = rfid.is_tag_present()
        is_object_present = beam.is_object_present()
        is_button_pressed = not button_input.value

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

        # MANUALLY_OPENED: Button pressed
        # JUST_OPENED: Cat arrived
        if state is State.CLOSED:
            if is_button_pressed:
                # if is_object_present:
                #     print("-> Button pressed, but object in way of beam; doing nothing")
                # else:
                print("-> Button pressed, opening...")
                lid.open()
                state = State.MANUALLY_OPENED
                print("-> Open, waiting for manual close.")
            if is_tag_present:
                # if is_object_present:
                #     print("-> Cat detected, but object in way of beam; doing nothing")
                # else:
                print("-> Cat arrived, opening...")
                lid.open()
                state = State.JUST_OPENED
                last_action_time_ns = time.monotonic_ns()
                print("-> Open, waiting %ds grace period..." % DELAY_AFTER_OPEN_S)

        # OPEN: After grace period for cat to enter beam
        elif state is State.JUST_OPENED:
            since_open_s = (time.monotonic_ns() - last_action_time_ns) / 1e9
            if since_open_s >= DELAY_AFTER_OPEN_S:
                print("-> Open grace period over, monitoring for cat to leave...")
                state = State.OPEN

        # CLOSE_PENDING: Cat gone
        elif state is State.OPEN:
            if not is_tag_present and not is_object_present:
                print("-> Cat gone, waiting to make sure...")
                state = State.CLOSE_PENDING
                last_action_time_ns = time.monotonic_ns()

        # CLOSED: After button press
        elif state is State.MANUALLY_OPENED:
            if is_button_pressed:
                if is_object_present:
                    print("-> Button pressed, but object in way of beam; doing nothing")
                else:
                    print("-> Button pressed, closing...")
                    if lid.close(shouldCancel = lambda progress: progress > 0.5 and beam.is_object_present()):
                        state = State.CLOSED
                        print("Closed, monitoring for cat to arrive...")
                    else:
                        print("Close cancelled");
                        state = State.OPEN
            elif is_object_present:
                print("-> Object present, exiting manual mode.")
                state = State.OPEN

        # CLOSED: After cat has been confirmed gone for period
        elif state is State.CLOSE_PENDING:
            if is_tag_present or is_object_present:
                print("-> Cat back, canceling pending close.")
                state = State.OPEN
            else:
                since_close_s = (time.monotonic_ns() - last_action_time_ns) / 1e9
                if since_close_s >= DELAY_BEFORE_CLOSE_S:
                    print("Closing after waiting %ds..." % since_close_s)
                    if lid.close(shouldCancel = lambda progress: progress < 0.5 and beam.is_object_present()):
                        state = State.CLOSED
                        print("Closed, monitoring for cat to arrive...")
                    else:
                        print("Close cancelled");
                        state = State.OPEN
except Exception as e:
    print(f"Uncaught exception: {e}")
    error_light()
