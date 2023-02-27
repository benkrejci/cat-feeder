import board
import busio

uart = busio.UART(board.MISO, board.D2, baudrate=9600, timeout=0.1)

def is_tag_present():
    data = uart.read(30) # read up to 30 bytes
    uart.reset_input_buffer()
    return data is not None, data
