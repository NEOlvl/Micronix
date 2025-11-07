import pandas as pd
import eel
from random import randint
import sqlite3

eel.init("web_pack")

# Exposing the random_python function to javascript
@eel.expose
def random_python():
    print("Random function running")
    return randint(1,100)


# Load the xlsx file
df_orders = pd.read_csv('web_pack/data/N1-RES1.csv')
data = pd.DataFrame(df_orders).to_numpy()
#print(data)


arr_gg = []
arr_db = []
for filf in data:
    arr_gg.append(filf[0])
    arr_db.append(filf[1])
    print(filf[0])

print(arr_gg)

print(arr_gg[0])

arr_gg = ' , '.join(map(str, arr_gg))
arr_db = ' , '.join(map(str, arr_db))

print(arr_db)

@eel.expose
def graph_x():
    return arr_gg


# Start the index.html file
eel.start("measure.html", mode='brave', size=(1920,1080),  cmdline_args=[ '--start-fullscreen'])

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