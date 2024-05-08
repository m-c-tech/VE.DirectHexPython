import busio
import digitalio
import microcontroller as cpu
import struct
from struct import pack, unpack
import array
import binascii

TX = cpu.pin.PA22
RX = cpu.pin.PA23

def little_endian(hex_value): # Order Hex bytes in little endian order
    # Extract the integer value from the hexadecimal input
    value = int(hex_value)
    # Initialize the result
    result = 0
    # Reorder bytes in little-endian format
    while value:
        result = (result << 8) | (value & 0xff)  # Append byte to result in little-endian format
        value >>= 8
    return result

# Commands
Get_ID = 0x4
Get = 0x7
Set = 0x8

registers = {
    0x0200: 'DeviceModeRegister',
    0x0201: 'DeviceStateRegister',
    0xEDF6: 'BatteryFloatVoltageRegister',
    0xEDF0: 'BatteryMaximumCurrentRegister',
    0xEDD5: 'ChargerVoltageRegister',
    0x0207: 'DeviceOffReasonRegister'
}

# Registers
DeviceModeRegister = 0x0200
DeviceStateRegister = 0x0201
BatteryFloatVoltageRegister = 0xEDF6
BatteryMaximumCurrentRegister = 0xEDF0
ChargerVoltageRegister = 0xEDD5
DeviceOffReasonRegister = 0x0207

def generate_output(command, register, payload=None):
    # Generate the message array based on the hex_command, register, and payload
    message = [command & 0xFF, register & 0xFF, (register >> 8) & 0xFF]
    
    # Check if payload is provided and if it's an integer
    if payload is not None and isinstance(payload, int):
        payload = little_endian(payload)
        if payload < 256:
            # Append the lowest byte of the payload (uint8) to the message
            message.append(payload & 0xFF)
            payload_str = "%02X" % payload
        elif payload < 65536:
            # Pack the payload as an unsigned 16-bit integer (uint16) in big-endian byte order
            # Extend the message with the packed bytes representing the uint16 payload
            message.extend(struct.pack('>H', payload))
            payload_str = "%04X" % payload
        else:
            # Pack the payload as an unsigned 32-bit integer (uint32) in big-endian byte order
            # Extend the message with the packed bytes representing the uint32 payload
            message.extend(struct.pack('>I', payload))
            payload_str = "%06X" % payload

    # Calculate the checksum
    checksum = 0x55
    for byte in message:
        checksum -= byte
        checksum &= 0xFF  # Ensure checksum stays within range of 0 to 255
    message.append(checksum & 0xFF)


    # Convert the components to their string representations with appropriate lengths
    hex_command_str = "%X" % command
    register_str = "%04X" % little_endian(register)
    checksum_str = "%02X" % checksum

        # Concatenate the strings with appropriate formatting
    output = ":" + hex_command_str + register_str + checksum_str
    if payload is not None:
            output = ":" + hex_command_str + register_str + payload_str + checksum_str
    return output

def lookup_command_name(command): # Function to lookup command name
    return registers.get(command, 'Unknown')

def decode_input(input):
    # Remove the ":" prefix from the output
    input = input[1:]

    # Extract the hex command, register, and checksum
    received_hex_command_str = input[:1]
    received_register_str = input[1:5]
    
    received_checksum_str = input[-2:]


    # Calculate the checksum of the message
    message_str = input[2:-2]
    checksum = 0x55
    for i in range(0, len(message_str), 2):
        byte = int(message_str[i:i+2], 16)
        checksum -= byte

    # Verify checksum
    #if checksum != int(received_checksum_str, 16):
        #print("Checksum error!")
        #return None

    # Convert hex strings back to hexadecimal format
    received_hex_command = "0x" + received_hex_command_str
    received_register = little_endian("0x" + received_register_str)

    # Determine payload length based on message length
    received_payload_length = len(message_str) - 4 if len(message_str) > 4 else 0
    # Extract payload if present
    if received_payload_length > 0:
        if received_payload_length == 4:
            received_payload = little_endian(int(message_str[4:], 16))
        elif received_payload_length == 6:
            received_payload = little_endian(int(message_str[4:9], 16))

    return received_hex_command, received_register, received_payload  # Output example: ('0x07', '0x0140', 255)



print("victron serial dump")
uart = busio.UART(TX, RX, baudrate=19200)

output = generate_output(Get, ChargerVoltageRegister) # Example usage for ouptput string generation
print("Command to send:")
print(output)
uart.write(str.encode (output+"\n"))

data = uart.readline()
data_string = ''.join([chr(b) for b in data])

print("Data received:")
print(data_string, end="")

print("Command decoded:")
print(decode_input(data_string)[0]) 

print("Register decoded:")
print(lookup_command_name(decode_input(data_string)[1]))  # Output: DeviceStateRegister

print("Payload decoded:")
print(int(decode_input(data_string)[2]))


while True:
    break