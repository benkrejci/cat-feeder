import board
import digitalio

beam = digitalio.DigitalInOut(board.D7)
beam.direction = digitalio.Direction.INPUT
beam.pull = digitalio.Pull.UP

def is_object_present():
    return not beam.value
