#
# import eel
# from random import randint
#
# eel.init("web_pack")
#
# # Exposing the random_python function to javascript
# @eel.expose
# def graph_x():
#     print("Random function running")
#     return randint(1,100)
#
# # Start the index.html file
# eel.start("measure.html", mode='brave', size=(1920,1080),  cmdline_args=[ '--start-fullscreen'])
import pyvisa
import pandas as pd
import eel
from random import randint
import json
import sqlite3
address = "TCPIP0::localhost::5025::SOCKET"

class Messager():
    def __init__(self):
        rm = pyvisa.ResourceManager()

        self.res = rm.open_resource(address, timeout=500)
    def query(self, message:str):
        self.res.read_termination = '\n'
        self.res.write_termination = '\n'

        try:
            tmp = self.res.query(message)
            print("{:30}".format("Message: " + message) + "{:>40}".format(" return: " + tmp))
            return tmp
        except pyvisa.errors.VisaIOError:
            print("{:30}".format("Message: " + message) + "{:>40}".format(" not answer"))
            return ''


    def write(self, message: str):
        self.res.read_termination = '\n'
        self.res.write(message)
        print("{:30}".format("Message: " + message))


eel.init("web_pack")

# Exposing the random_python function to javascript
@eel.expose
def random_python():
    print("Random function running")
    return randint(1,100)


# Load the xlsx file
df_orders = pd.read_csv('web_pack/data/noname.csv')
data = pd.DataFrame(df_orders).to_numpy()
#print(data)
df_orders2 = pd.read_csv('web_pack/data/N3-RES2.csv')
data2 = pd.DataFrame(df_orders2).to_numpy()

arr_gg1 = []
arr_db1 = []
arr_db2 = []
for fild in data:
    arr_gg1.append(fild[0]/1000000000)
    arr_db1.append(fild[1])
    # print(filf[0])

for fild in data2:
    arr_db2.append(fild[1])


print(arr_gg1)

print(arr_gg1[0])

arr_gg = ' , '.join(map(str, arr_gg1))
arr_db = ' , '.join(map(str, arr_db1))
arr_db2 = ' , '.join(map(str, arr_db2))

messager = Messager()
messager.query("SENS:FREQ:STAR 8 GHz")
messager.query("SENS:FREQ:STOP 12 GHz")
tmp = messager.query("CALC1:DATA:FDAT?").split(",") #CALC:TRAC:DATA:XAX?
arr_end = []
i_q = 1
for i in tmp:
    if  i_q % 2 != 0:
        arr_end.append(i)
        print(i)
    i_q += 1
print(arr_end)
@eel.expose
def graph_x():
    return json.dumps(arr_gg)

@eel.expose
def graph_y():
    tmp = messager.query("CALC:DATA:FDAT?").split(",")
    arr_end = []
    i_q = 1
    for i in tmp:
        if i_q % 2 != 0:
            arr_end.append(i)
            print(i)
        i_q += 1
    return json.dumps(' , '.join(map(str, arr_end)))
@eel.expose
def graph_y2():
    return json.dumps(arr_db2)

eel.spawn(graph_x)

# Start the index.html file
eel.start("measure2.html", mode='brave', size=(1920,1080),  cmdline_args=[ '--start-fullscreen'])

# con = sqlite3.connect("test.db")
# cursor = con.cursor()

# Создаем таблицу Users
#cursor.execute("CREATE TABLE IF NOT EXISTS Test (id INTEGER PRIMARY KEY, username TEXT NOT NULL, email TEXT NOT NULL, age INTEGER)")
#cursor.execute('INSERT INTO Test (username, email, age) VALUES (?, ?, ?)', ('Egor', 'egor@example.com', 21))

# cursor.execute('SELECT * FROM Test')
# users = cursor.fetchall()
#
# arr = []
#
# # Выводим результаты
# for user in users:
#     id, name, email, age = user
#     arr.append(name)
#     print(name)
#
#
# # Сохраняем изменения и закрываем соединение
# con.commit()
# con.close()
#
# print(arr)