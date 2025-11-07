import pyvisa
import serial
rm = pyvisa.ResourceManager()
print(rm.list_resources())


ser = serial.Serial('COM5', 9600)
ser.write(b'Hello, Arduino!')
response = ser.readline()
decoded_response = response.decode('utf-8')
print(decoded_response)
ser.close()
