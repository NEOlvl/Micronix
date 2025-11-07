import json
import datetime
from os import write
from pprint import pprint
from All_Methods_3 import *
import sqlite3 as sql
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from fpdf import FPDF , HTMLMixin

def toFixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"

def closest_value(input_list, input_value):
    arr = np.asarray(input_list)
    i = (np.abs(arr - input_value)).argmin()
    return arr[i]

def Test_Methot(r, R, fE, f0, QE, Q0):

    E = 1 + 0.539 * pow((R/r), 2) * ((float(fE) - float(f0)) / float(f0))
    tgo = (0.269 / E) * pow(R / r, 2) * ((1 / QE) - (1 / Q0))

    return f"E = {E}, tgo = {tgo}"
def DataArrDist(arr_x, arr_y):
    float_list = [float(i) for i in arr_y]
    index_res = float_list.index(min(float_list))
    f0 = arr_x[index_res]
    print(float_list)
    f1 = arr_x[float_list.index(closest_value(float_list[(index_res - 50):index_res], (min(float_list) + 3)))]
    f2 = arr_x[float_list.index(closest_value(float_list[index_res:index_res + 50], (min(float_list) + 3)))]
    Q = float(f0)/(float(f2)-float(f1))
    return {'f0': f0, 'f1': f1, 'f2': f2, 'Q':Q}


# with open('data_base/db_ferro.txt' ) as file:
#   data_db = json.load(file)
#   print(data_db)
#   for data in data_db:
#     print(data_db[data]['measure_id'])
# print(datetime.datetime.now().strftime('%d%m%Y'))
#
# f = open('data_ferro/XF3bUZo_1_QoZR-PljCzeA', 'w')
# f.write(json.dumps(data))
# f.close()

#
# for i in data['y_samples']:
#     print(Methot_Marina(float(data['data_param']['data[3][d]']), float(data['f0']), float(data['f1']), float(data['f2']), float(data['y_samples'][i]['fe']), float(data['data_param']['data[3][d_res]'])/2, float(data['data_param']['data[3][h_res]']), float(data['A0']), float(data['y_samples'][i]['AE'])))
#

connection = sql.connect('data_base/test.db')
cursor = connection.cursor()

# Создаем таблицу ferro_measures
# cursor.execute('''
# CREATE TABLE IF NOT EXISTS measures (
# id INTEGER PRIMARY KEY,
# method_id INTEGER,
# measure_id VARCHAR(100) NULL,
# title VARCHAR(100) NULL,
# description TEXT NULL,
# user VARCHAR(100) NULL,
# data TEXT NULL,
# date_create TEXT NULL
# )
# ''')
currentDateTime = datetime.datetime.now()
# Добавляем нового пользователя
#cursor.execute('INSERT INTO measures (method_id, measure_id, title, description,  date_create) VALUES (?, ?, ?, ?, ?)', (3, '8QRYGvWU001XOAZuFDU2bg', 'СВЧФ_2_221223','Описание', datetime.datetime.now()))
# cursor.execute('DELETE  FROM measures  WHERE id = 1')
cursor.execute('SELECT * FROM measures ')
data_db = cursor.fetchall()
#
for data in data_db:
   print(data)

# # Сохраняем изменения и закрываем соединение

def create_pdf(arr_data, data_bd):
    pdf = FPDF()
    # pdf.set_margins(left=2, right=2, top=2, )
    pdf.add_page()
    pdf.add_font('TNR', '', 'font/timesnewromanpsmt.ttf', uni=True)
    pdf.add_font('TNRB', '', 'font/TNR_bold.ttf', uni=True)
    pdf.set_font('TNRB', '', 14)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Отчёт проведения измерений", ln=1, align="C")
    pdf.cell(200, 10, txt="диэлектрической проницаемости #" + arr_data['title'], ln=2, align="C")
    pdf.ln(15)
    pdf.set_font('TNRB', '', 12)
    pdf.cell(200, 10, txt="Общие данные:", ln=2, align="L")
    pdf.set_font('TNR', '', 12)
    pdf.cell(200, 10, txt="Дата проведения испытаний: " + datetime.datetime.strptime(arr_data['date'], '%d%m%Y').strftime("%d.%m.%Y"), ln=1, align="L")
    match arr_data['data_param']['method']:
        case '1':
            name = 'МФЧ'
            subtitle = 'Исследование по методу фиксированной частоты.'
            d_sample = arr_data['data_param']['data[1][t]']
            text_sample ="Толщина образца: "+ d_sample +" мм;"
        case '2':
            name = 'МФД'
            subtitle = 'Исследование по методу фиксированной длины.'
            d_sample = arr_data['data_param']['data[2][t]']
            text_sample = "Толщина образца: " + d_sample + " мм;"
        case '3':
            name = 'СО'
            subtitle = 'Исследование по методу стержневых образцов.'
            d_sample = arr_data['data_param']['data[3][d]']
            text_sample = "Радиус образца: " + d_sample + " мм;"
        case '4':
            name = 'СВЧФ'
            subtitle = 'Исследование по методу СВЧ ферритов.'
            d_sample = arr_data['data_param']['data[4][d_sample]']
            text_sample = "Радиус образца: " + d_sample + " мм;"
        case _:
            name_method = ''
    pdf.cell(200, 10, txt="" + subtitle, ln=1, align="L")
    pdf.cell(200, 10, txt="Резонансная частота свободного резонатора: "+ str(float(arr_data['f0'])/1000000000) +" ГГц;", ln=1, align="L")

    pdf.cell(200, 10, txt=text_sample, ln=1, align="L")
    pdf.cell(200, 10, txt="Допуск: - ;", ln=1, align="L")
    # data_bd['description'] = 0
    # if data_bd['description'] != 0:
    #     pdf.cell(200, 10, txt="Описание: "+ data_bd['description'] +"  ;", ln=1, align="L")
    pdf.ln(15)
    pdf.set_font('TNRB', '', 12)
    pdf.cell(200, 10, txt="Расчётные данные:", ln=2, align="L")

    data = {}
    i = 1
    for data_sample in arr_data['y_samples']:
        print( arr_data['y_samples'][data_sample]['name'])
        data[len(data) + 1] = {'id': str(i),'name': arr_data['y_samples'][data_sample]['name'], 'fe': str(float(arr_data['y_samples'][data_sample]['fe'])/1000000000),  'tgo': toFixed(arr_data['y_samples'][data_sample]['tgo'] * 10 ** 4, 3), 'e': toFixed(arr_data['y_samples'][data_sample]['E'], 5) }

    col_width = pdf.w / 5.5
    row_height = pdf.font_size
    line_y =  pdf.y
    pdf.multi_cell(10, row_height*2,txt="№", border=1, align="C")
    pdf.y = line_y
    pdf.x = 20
    pdf.multi_cell(40, row_height,txt="Наименование образца", border=1 , align="C")
    pdf.y = line_y
    pdf.x = 60
    pdf.multi_cell(45, row_height,txt="Частота резонанса, ГГц", border=1 , align="C")
    pdf.y = line_y
    pdf.x = 105
    pdf.multi_cell(40, row_height,txt="Тангенс угла потерь, 10^-4", border=1 , align="C")
    pdf.y = line_y
    pdf.x = 145
    pdf.multi_cell(45, row_height,txt="Диэлектрическая проницаемость", border=1 , align="C")
    pdf.ln(0)
    pdf.set_font('TNR', '', 12)
    i = 1
    for row in data:
        line_y = pdf.y
        pdf.multi_cell(10, row_height * 2, txt= str(i), border=1, align="C")
        pdf.y = line_y
        pdf.x = 20
        pdf.multi_cell(40, row_height*2, txt= data[row]['name'], border=1, align="C")
        pdf.y = line_y
        pdf.x = 60
        pdf.multi_cell(45, row_height*2, txt= data[row]['fe'], border=1, align="C")
        pdf.y = line_y
        pdf.x = 105
        pdf.multi_cell(40, row_height*2, txt= data[row]['tgo'], border=1, align="C")
        pdf.y = line_y
        pdf.x = 145
        pdf.multi_cell(45, row_height*2, txt= data[row]['e'], border=1, align="C")
        i = i+1
        pdf.ln(0)

    pdf.ln(15)
    pdf.set_font('TNRB', '', 12)
    pdf.cell(200, 10, txt="Измерение провёл: _____________________", ln=2, align="L")


    # pdf.alias_nb_pages()
    pdf.set_auto_page_break(False)
    pdf.set_y(280)
    pdf.set_font('TNR', '', 8)
    pdf.cell(0, 10, "Отчёт составлен на основе измерений программно-аппаратного комплекса FERRO.", 0, 1, 'L')
    pdf.set_y(283)
    pdf.cell(0, 10, "Версия: beta_v1.1 x64 WIN10. Отчёт в системе: #"+ data_bd['measure_id'], 0, 1, 'L')
    pdf.output("report/"+ arr_data['title'] + ".pdf")


print(float("+9.655000000E+09"))

# arr_measures = []
# with open('data_base/db_ferro.txt' ) as file:
#     data_db = json.load(file)
#     for data in data_db:
#         with open('data_ferro/' + data_db[data]['measure_id'] + '.txt') as file_measure:
#             data_measure = json.load(file_measure)
#
#             arr_end = data['y']
#             float_list = [float(i) for i in arr_end]
#             index_res = float_list.index(min(float_list))
#             f0 = data['x'][index_res]
#             f1 = data['x'][
#             float_list.index(closest_value(float_list[(index_res - 50):index_res], (min(float_list) + 3)))]
#             f2 = data['x'][float_list.index(closest_value(float_list[index_res:index_res + 50], (min(float_list) + 3)))]
#
#             cursor.execute('INSERT INTO measures (method_id, measure_id, title, description,  date_create) VALUES (?, ?, ?, ?, ?)', (float(data_measure['data_param']['method']), data_db[data]['measure_id'], data_measure['title'],data_db[data]['description'], datetime.datetime.now()))
#             create_pdf(data_measure, data_db[data])

# with open('data_ferro/kpFp5fZ0cXELee5zBzMclw.txt') as file_measure:
#     data_measure = json.load(file_measure)
#     data_db = {'measure_id': 'kpFp5fZ0cXELee5zBzMclw'}
#     create_pdf(data_measure, data_db)

# with open('data_ferro/vK5KumBvNSSHqCk-OXPtbw.txt') as file_measure_1:
#     data_measure1 = json.load(file_measure_1)
#     arr_end = data_measure1['y_res'][:500]
#     # print(data_measure1)
#     Result = Methot_Marina(float(data_measure1['data_param']['data[3][d]']), float(data_measure1['f0']),
#                            float(data_measure1['f1']), float(data_measure1['f2']),
#                            float(data_measure1['y_samples']['2']['fe']),
#                            float(data_measure1['data_param']['data[3][d_res]']) / 2,
#                            float(data_measure1['data_param']['data[3][h_res]']), float(data_measure1['A0']), float(data_measure1['y_samples']['1']['AE']), DataArrDist(data_measure1['x'], arr_end)['Q'], DataArrDist(data_measure1['x'], data_measure1['y_samples']['2']['y_res'])['Q'])
#     # print(Result)
#
# with open('data_ferro/vK5KumBvNSSHqCk-OXPtbw.txt') as file_measure:
#     data_measure = json.load(file_measure)
#     arr_end = data_measure['y_res'][:500]
#     # print(DataArrDist(data_measure['x'], arr_end))
#     Result = Methot_Marina(float(data_measure['data_param']['data[3][d]']), float(data_measure['f0']), float(data_measure['f1']), float(data_measure['f2']),
#                   float(data_measure['y_samples']['2']['fe']), float(data_measure['data_param']['data[3][d_res]']) / 2,
#                   float(data_measure['data_param']['data[3][h_res]']), float(data_measure['A0']), float(data_measure['y_samples']['2']['AE']), DataArrDist(data_measure['x'], arr_end)['Q'], DataArrDist(data_measure['x'], data_measure['y_samples']['3']['y_res'])['Q'])
#     #
    # arr_end = data_measure['y_res'][:500]
    # print(DataArrDist(data_measure['x'], arr_end))
    # data_null = DataArrDist(data_measure['x'], arr_end)
    # data_sample = DataArrDist(data_measure['x'], data_measure['y_samples']['1']['y_res'][:500])
    # print(data_sample)
    # print(Test_Methot(3.9 , 22.5, data_sample['f0'], data_null['f0'], data_sample['Q'], data_null['Q']))
    # print(Result)


with open('data_ferro/ZUryV57LaMjeE9mdWbjB_w.txt') as file_measure:
    data_measure = json.load(file_measure)
    arr_end = data_measure['y_res']
    # print(DataArrDist(data_measure['x'], arr_end))
    # print(data_measure)
    data = data_measure
    for i in data['y_samples']:
        ResSample2 = DataArrDist(data['x'], data['y_samples'][i]['y_res'])
        # print(ResSample2)
        arr_results2 = Method_real(float(ResSample2['f0']), float(data['f0']), float(data['f1']),
                                  float(data['f2']), float(ResSample2['f1']), float(ResSample2['f2']),
                                  float(data['data_param']['data[4][d_res]']),
                                  float(data['data_param']['data[4][d_sample]']))
    #     print('Образец № ' + str(i))
    #     print(arr_results2)
    # print('________________')
    ResSample = DataArrDist(data_measure['x'], data_measure['y_samples']['1']['y_res'])
    Result = Method_real(float(data_measure['y_samples']['1']['fe']), float(data_measure['f0']), float(data_measure['f1']), float(data_measure['f2']), float(ResSample['f1']), float(ResSample['f2']), float(data_measure['data_param']['data[4][d_res]']),float(data_measure['data_param']['data[4][d_sample]']))
    Result1 = Methot_Egor_st(float(data_measure['y_samples']['1']['fe']), float(data_measure['f0']),
                         float(data_measure['f1']), float(data_measure['f2']), float(ResSample['f1']),
                         float(ResSample['f2']), float(data_measure['data_param']['data[4][d_res]']),
                         float(data_measure['data_param']['data[4][d_sample]']))
    # print(Result)
    # print(Result1)


connection.commit()
connection.close()
