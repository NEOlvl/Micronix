import pyvisa
import bisect
import numpy as np
address = "TCPIP0::localhost::5025::SOCKET"

# class Messager():
#     def __init__(self):
#         rm = pyvisa.ResourceManager()
#
#         self.res = rm.open_resource(address, timeout=1000)
#     def query(self, message:str):
#         self.res.read_termination = '\n'
#         self.res.write_termination = '\n'
#         try:
#             print("{:30}".format("Message: " + message) + "{:>40}".format(" return: " + self.res.query(message)))
#
#         except pyvisa.errors.VisaIOError:
#             print("{:30}".format("Message: " + message) + "{:>40}".format(" not answer"))
#
#     def write(self, message: str):
#         self.res.read_termination = '\n'
#         self.res.write(message)
#         print("{:30}".format("Message: " + message))
def take_closest(myList, myNumber):
    pos = bisect.bisect_left(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before

def take_closest_left(myList, myNumber):
    pos = bisect.bisect_right(myList, myNumber)
    if pos == 0:
        return myList[0]
    if pos == len(myList):
        return myList[-1]
    before = myList[pos - 1]
    after = myList[pos]
    if after - myNumber < myNumber - before:
        return after
    else:
        return before


def closest_value(input_list, input_value):
    arr = np.asarray(input_list)
    i = (np.abs(arr - input_value)).argmin()
    return arr[i]

def DataArrDist(arr_x, arr_y):
    float_list = [float(i) for i in arr_y]
    index_res = float_list.index(min(float_list))
    f0 = arr_x[index_res]
    f1 = arr_x[float_list.index(closest_value(float_list[(index_res - 50):index_res], (min(float_list) + 3)))]
    f2 = arr_x[float_list.index(closest_value(float_list[index_res:index_res + 50], (min(float_list) + 3)))]
    Q = float(f0)/(float(f2)-float(f1))
    return {'f0': f0, 'f1': f1, 'f2': f2, 'Q':Q}


class Messager():
    def __init__(self):
        rm = pyvisa.ResourceManager()
        try:
            self.res = rm.open_resource(address, timeout=500)
        except pyvisa.errors.VisaIOError:
            print('ERROR')
    def query(self, message:str):
        self.res.read_termination = '\n'
        self.res.write_termination = '\n'

        try:
            tmp = self.res.query(message)
            print("{:30}".format("Message: " + message) + "{:>40}".format(" return: " + tmp))
            return tmp
        except pyvisa.errors.VisaIOError:
            print("{:30}".format("Message: " + message) + "{:>40}".format(" not answer"))
            return 'error'


    def write(self, message: str):
        self.res.read_termination = '\n'
        self.res.write(message)
        print("{:30}".format("Message: " + message))



messager = Messager()
print(messager)
if(messager.query("SENS:FREQ:STAR 8 GHz") == 'error'):
    print('Stop function')
messager.query("SENS:FREQ:STOP 12 GHz")
tmp = messager.query("CALC1:DATA:FDAT?").split(",")
tmp_x = messager.query("CALC1:DATA:XAXis?").split(",")
arr_end = []
i_q = 1
for i in tmp:
    if i_q % 2 != 0:
        arr_end.append(i)
        print(i)
    i_q += 1
print(arr_end)
arr_end = arr_end
print(tmp_x)
float_list = [float(i) for i in arr_end]
print('Значение резонанса:')
print(min(float_list))
index_res = float_list.index(min(float_list))
# print('index:' + str(index_res))
print('Частота резонанса:')
print (tmp_x[index_res])
# print(index_res-50)
# print(float_list[index_res-50:index_res])
# print('Значения с левой стороны:')
# print(closest_value(float_list[(index_res-50):index_res], min(float_list) + 3))
# print(tmp_x[float_list.index(closest_value(float_list[(index_res-50):index_res], (min(float_list) + 3)))])
#
# print('Значения с правой стороны:')
# print(closest_value(float_list[index_res:index_res+50], (min(float_list) + 3)))
# print(tmp_x[float_list.index(closest_value(float_list[index_res:index_res+50], (min(float_list) + 3)))])
print(DataArrDist(tmp_x, arr_end))
