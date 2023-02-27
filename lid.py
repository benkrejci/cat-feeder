# Write your code here :-)
"""CircuitPython Essentials UART Serial example"""
import board
import pwmio
import time
from adafruit_motor import stepper

STEPS = 136
LOCK_STEPS = 0.3

OPEN_TIME = 0.6
LOCK_TIME = 0.15

MICROSTEP_RESOLUTION = 16
MICROSTEPS = STEPS * MICROSTEP_RESOLUTION
LOCK_MICROSTEPS = LOCK_STEPS * MICROSTEP_RESOLUTION

STEP_DELAY = OPEN_TIME / STEPS
MICROSTEP_DELAY = OPEN_TIME / MICROSTEPS
LOCK_MICROSTEP_DELAY = LOCK_TIME / LOCK_MICROSTEPS

coils = (
    pwmio.PWMOut(board.D9, variable_frequency=True),  # A1
    pwmio.PWMOut(board.D10, variable_frequency=True),  # A2
    pwmio.PWMOut(board.D11, variable_frequency=True),  # B1
    pwmio.PWMOut(board.D12, variable_frequency=True),  # B2
)

#coils = (
#    digitalio.DigitalInOut(board.D9),  # A1
#    digitalio.DigitalInOut(board.D10),  # A2
#    digitalio.DigitalInOut(board.D11),  # B1
#    digitalio.DigitalInOut(board.D12),  # B2
#)

#for coil in coils:
#    coil.direction = digitalio.Direction.OUTPUT

motor = stepper.StepperMotor(coils[0], coils[1], coils[2], coils[3], microsteps=MICROSTEP_RESOLUTION)
motor.release()

def wait(last_time, delay):
    now = time.monotonic_ns()
    elapsed = (now - last_time) / 1_000_000_000
    if elapsed < delay:
        time.sleep(delay - elapsed)
    return time.monotonic_ns()

def move(microsteps, delay, direction, shouldCancel = None):
    last_step = 0
    absolute_microstep = 0
    relative_microstep = 0
    # Make sure we end on a whole step so motor doesn't whine
    while relative_microstep < microsteps or \
          absolute_microstep % MICROSTEP_RESOLUTION is not 0:
        relative_microstep += 1
        last_step = wait(last_step, delay)
        absolute_microstep = motor.onestep(direction=direction, style=stepper.MICROSTEP)
        if shouldCancel and shouldCancel(relative_microstep / microsteps):
            move(
                relative_microstep,
                delay,
                stepper.BACKWARD if direction is stepper.FORWARD else stepper.FORWARD
            )
            return False
    return True


is_open = False

def open():
    global is_open
    if is_open:
        print("WARN: open() called while is_open is already True")
        return
    move(MICROSTEPS, MICROSTEP_DELAY, stepper.FORWARD)
    motor.release()
    is_open = True

def close(shouldCancel = None):
    global is_open
    if not is_open:
        print("WARN,: close() called while is_open is already False")
        quit()
    success = move(MICROSTEPS, MICROSTEP_DELAY, stepper.BACKWARD, shouldCancel)
    motor.release()
    #move(LOCK_MICROSTEPS, LOCK_MICROSTEP_DELAY, stepper.FORWARD)
    #motor.release()
    is_open = not success
    return success
