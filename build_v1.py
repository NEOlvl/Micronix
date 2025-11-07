import pyvisa
import pandas as pd
import eel
from random import randint
import sqlite3
import json
import datetime
import pytz
from numpy.random.mtrand import random
import string
import secrets
import numpy as np
from All_Methods_3 import *
import sqlite3 as sql
import warnings
from fpdf import FPDF
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

address = "TCPIP0::localhost::5025::SOCKET"

def toFixed(numObj, digits=0):
    return f"{numObj:.{digits}f}"

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

        self.res = rm.open_resource(address, timeout=500)
    def query(self, message:str):
        self.res.read_termination = '\n'
        self.res.write_termination = '\n'

        try:
            tmp = self.res.query(message)
            # print("{:30}".format("Message: " + message) + "{:>40}".format(" return: " + tmp))
            return tmp
        except pyvisa.errors.VisaIOError:
            print("{:30}".format("Message: " + message) + "{:>40}".format(" not answer"))
            print("ERROR ERROR")
            return 0


    def write(self, message: str):
        self.res.read_termination = '\n'
        self.res.write(message)
        print("{:30}".format("Message: " + message))




@eel.expose
def request_caban(start_f = 8, stop_f = 12):
    messager = Messager()
    messager.query("SENS:FREQ:STAR " + str(start_f) +" GHz")
    messager.query("SENS:FREQ:STOP " + str(stop_f) + " GHz")
    tmp = messager.query("CALC1:DATA:FDAT?").split(",")
    tmp_x = messager.query("CALC1:DATA:XAXis?").split(",")
    arr_end = []
    i_q = 1
    for i in tmp:
        if i_q % 2 != 0:
            arr_end.append(i)
            # print(i)
        i_q += 1
    # print(arr_end)
    # print(tmp_x)
    # print(min(arr_end))
    return {'x': tmp_x, 'y': arr_end}
    # return json.dumps(' , '.join(map(str, arr_end)))

@eel.expose
def bd_create():
    connection = sql.connect('data_base/test.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO measures (method_id, measure_id, title) VALUES (?, ?, ?)',(2, 'djs893nid', 'TEST'))
    connection.commit()
    connection.close()

@eel.expose
def ferro_query(method, pharams):
    if(pharams != 0):
        print(pharams)
        arr_method = json.dumps(pharams)
        nn = json.loads(arr_method)
        list_from_dict = list(zip(nn.keys(), nn.values()))
        arr_data = {}
        for i in list_from_dict:
            arr_data[i[0]] = i[1]
        print(arr_data)

    match method:
        case 'new_create':
            key = secrets.token_urlsafe(16)
            print('Create method')
            current_time = datetime.datetime.now(pytz.timezone('Europe/Samara'))
            match arr_data['method']:
                case '1':
                    name = 'ФРЧ'
                    subtitle = 'Исследование по методу фиксированной частоты.'
                    arr_data_metod = arr_data
                case '2':
                    name = 'ФРД'
                    subtitle = 'Исследование по методу фиксированной длины.'
                    arr_data_metod = arr_data
                case '3':
                    name = 'СО'
                    subtitle = 'Исследование по методу стержневых образцов.'
                    arr_data_metod = arr_data
                case '4':
                    name = 'СВЧФ'
                    subtitle = 'Исследование по методу СВЧ ферритов.'
                    arr_data_metod = arr_data
                case _:
                    name_method = ''

            date = datetime.datetime.now().strftime('%d%m%Y')
            name_method = name + '_' + str(randint(1, 30)) + '_' + date
            time = str(current_time.hour) + ':' + str(current_time.minute)

            data = request_caban()
            if(data == 0):
                status = 'error'
                print('ERROR')
                return "ERROR"
            else:
                arr_end = data['y']
                float_list = [float(i) for i in arr_end]
                index_res = float_list.index(min(float_list))
                f0 = data['x'][index_res]
                f1 = data['x'][float_list.index(closest_value(float_list[(index_res-50):index_res], (min(float_list) + 3)))]
                f2 = data['x'][float_list.index(closest_value(float_list[index_res:index_res+50], (min(float_list) + 3)))]
                A0 = min(float_list)
                AE = 0
                status = 'ok'
                print(DataArrDist(data['x'], data['y']))

            data_file = {'data_param': arr_data_metod,'title': name_method, 'description': "", 'f0': f0,'f1': f1,'f2': f2, 'A0': A0, 'AE': AE,'date': date, 'time': time, 'x': data['x'], 'y_res':  data['y'],'y_samples': {} }
            print(data_file)

            f = open('data_ferro/'+key+'.txt', 'w')
            f.write(json.dumps(data_file))
            f.close()

            connection = sql.connect('data_base/test.db')
            cursor = connection.cursor()
            cursor.execute('INSERT INTO measures (method_id, measure_id, title, date_create) VALUES (?, ?, ?, ?)',(float(arr_data['method']), key, name_method, datetime.datetime.now()))
            connection.commit()
            connection.close()

            with open('data_base/db_ferro.txt') as file:
                data_db = json.load(file)
                data_db[len(data_db)+1] = {'method_id': float(arr_data['method']), 'measure_id': key, "description": "После применения калибровочных мер.", 'title': name_method, 'date': date, 'time': time, }

            f = open('data_base/db_ferro.txt', 'w')
            f.write(json.dumps(data_db))
            f.close()


            answer = {'id': key, 'title': name_method, 'subtitle': subtitle, 'status':status}
            return json.dumps(answer)
        case 'new_sample':
            id_file = arr_data['id_m']
            data = request_caban()
            arr_end = data['y']
            float_list = [float(i) for i in arr_end]
            index_res = float_list.index(min(float_list))
            fe = data['x'][index_res]
            AE = min(float_list)
            data_ref = data
            with open('data_ferro/'+id_file+'.txt') as file:
                data = json.load(file)
                data['y_samples'][len(data['y_samples'])+1] = {'name': arr_data['new_sample_name'], 'y_res': data_ref['y'], 'fe': fe, 'AE': AE, 'tgo': 0, 'E':0}
                # print(data)
            f = open('data_ferro/'+id_file+'.txt', 'w')
            f.write(json.dumps(data))
            f.close()
            return json.dumps({'id': id_file, 'name': arr_data['new_sample_name']})
        case 'create_graph':
            data = request_caban()
            return json.dumps(' , '.join(map(str, data['y'])))
        case 'create_graph_x':
            data = request_caban()
            return json.dumps(' , '.join(map(str, data['x'])))
        case 'method_end':
            id_file = arr_data['id_m']
            with open('data_ferro/'+id_file+'.txt') as file:
                data = json.load(file)
                match data['data_param']['method']:
                    case '1':
                        for i in data['y_samples']:
                            ResSample = DataArrDist(data['x'], data['y_samples'][i]['y_res'])
                            arr_results =  Methot_Vlad(float(data['data_param']['data[1][t]']), float(data['data_param']['data[1][d_res]']),
                                                       float(data['f0']), float(data['f1']), float(data['f2']), float(data['y_samples'][i]['fe']),
                                                       float(data['data_param']['data[1][h_res]']), float(data['data_param']['data[1][del_L]']),
                                                       float(data['A0']), float(data['y_samples'][i]['AE']))
                            if(arr_results['status'] == 'ok'):
                                data['y_samples'][i]['E'] = arr_results['E']
                                data['y_samples'][i]['tgo'] = arr_results['tgo']
                            else:
                                print('Error')
                                print(arr_results)


                    case '2':
                        for i in data['y_samples']:
                            ResSample = DataArrDist(data['x'], data['y_samples'][i]['y_res'])
                            arr_results = Methot_Nikita(float(data['data_param']['data[2][t]']),
                                                        float(data['data_param']['data[2][d_res]']),
                                                        float(data['data_param']['data[2][h_res]']), float(data['f0']),
                                                        float(data['f1']), float(data['f2']), float(ResSample['f0']),
                                                        float(data['A0']), float(data['y_samples'][i]['AE']))
                            if(arr_results['status'] == 'ok'):
                                data['y_samples'][i]['E'] = arr_results['E']
                                data['y_samples'][i]['tgo'] = arr_results['tgo']
                            else:
                                print('Error')
                                print(arr_results)



                    case '3':
                        for i in data['y_samples']:
                            ResArr = DataArrDist(data['x'], data['y_res'])
                            ResSample = DataArrDist(data['x'], data['y_samples'][i]['y_res'][:500])
                            arr_results = Methot_Marina(float(data['data_param']['data[3][d]']), float(data['f0']),
                                                        float(data['f1']), float(data['f2']), float(data['y_samples'][i]['fe']),
                                                        float(data['data_param']['data[3][d_res]'])/2, float(data['data_param']['data[3][h_res]']),
                                                        float(data['A0']),float(data['y_samples'][i]['AE']), float(ResArr['Q']), float(ResSample['Q']))
                            # /print(a, f0, f1, f2, fE, R0, L, A0, AE, Q0, QE)
                            if(arr_results['status'] == 'ok'):
                                data['y_samples'][i]['E'] = arr_results['E']
                                data['y_samples'][i]['tgo'] = arr_results['tgo']
                            else:
                                print('Error')
                                print(arr_results)
                    case '4':
                        if float(data['data_param']['data[4][form]']) == 0:
                            a = 1.12
                            b = 1.12
                        else:
                            a = 1.12
                            b = 1.12
                        #arr_results = Methot_Egor(a, b, float(data['data_param']['data[4][d_sample]']), float(data['data_param']['data[4][d_res]']), f1, f1sh, deld, Ms, float(data['data_param']['data[4][form]']))
                        for i in data['y_samples']:
                            ResSample =  DataArrDist(data['x'], data['y_samples'][i]['y_res'])
                            arr_results = Method_real(float(ResSample['f0']), float(data['f0']), float(data['f1']),
                                                      float(data['f2']), float(ResSample['f1']), float(ResSample['f2']),
                                                      float(data['data_param']['data[4][d_res]']), float(data['data_param']['data[4][d_sample]']))
                            if (arr_results['status'] == 'ok'):
                                data['y_samples'][i]['E'] = arr_results['E']
                                data['y_samples'][i]['tgo'] = arr_results['tgo']
                            else:
                                print('Error')
                                print(arr_results)

            f = open('data_ferro/' + id_file + '.txt', 'w')
            f.write(json.dumps(data))
            f.close()
            return json.dumps({'results': arr_results, 'id': id_file})
        case 'read_data':
            id_file = arr_data['id_m']
            with open('data_ferro/' + id_file+ '.txt' ) as file:
                data = json.load(file)
                data['Dist'] = DataArrDist(data['x'], data['y_res'])
                for i in data['y_samples']:
                    data['y_samples'][i]['Dist'] = DataArrDist(data['x'], data['y_samples'][i]['y_res'])
                print(data)
                return json.dumps(data)
        case 'measure_data':
            arr_measures = []
            connection = sql.connect('data_base/test.db')
            cursor = connection.cursor()

            # cursor.execute('DELETE  FROM measures  WHERE id = 1')
            cursor.execute('SELECT * FROM measures order by id desc LIMIT 5')
            data_db = cursor.fetchall()

            for data in data_db:
                print(data)
                print(data[2])
                try:
                    with open('data_ferro/'+ data[2]+'.txt') as file_measure:
                          data_measure = json.load(file_measure)
                          data_measure['id_m'] = data[2]
                          if 'tgo' in data_measure['y_samples']['1']:
                              data_measure['y_samples']['1']['tgo'] = toFixed(data_measure['y_samples']['1']['tgo'] * 10 ** 4, 3)
                          else:
                              data_measure['y_samples']['1']['tgo'] = "??"

                          if 'E' in data_measure['y_samples']['1']:
                              data_measure['y_samples']['1']['E'] = toFixed(data_measure['y_samples']['1']['E'], 5)
                          else:
                              data_measure['y_samples']['1']['E'] = "??"
                          # if data_measure['y_samples']['1']['tgo'] == '':
                          #     data_measure['y_samples']['1']['tgo'] = "??"
                          # else:
                          #     data_measure['y_samples']['1']['tgo'] = toFixed(data_measure['y_samples']['1']['tgo'] * 10 ** 4, 3)

                          arr_measures.append(data_measure)
                except FileNotFoundError:
                    print(f"Запрашиваемый файл {data[2]} не найден")
            connection.commit()
            connection.close()

            # with open('data_base/db_ferro.txt' ) as file:
            #     data_db = json.load(file)
            #     # print(reversed(data_db))
            #     i = 0
            #     for data in reversed(data_db):
            #         with open('data_ferro/'+data_db[data]['measure_id']+'.txt') as file_measure:
            #             print(data_db[data]['measure_id'])
            #             data_measure = json.load(file_measure)
            #             data_measure['id_m'] = data_db[data]['measure_id']
            #             if data_measure['y_samples']['1']['tgo'] == '':
            #                 data_measure['y_samples']['1']['tgo'] = "??"
            #             else:
            #                 data_measure['y_samples']['1']['tgo'] = toFixed(data_measure['y_samples']['1']['tgo'] * 10 ** 4, 3)
            #             data_measure['y_samples']['1']['E'] = toFixed(data_measure['y_samples']['1']['E'], 5)
            #             arr_measures.append(data_measure)
            #             i +=1
            #             if i == 4:
            #                  break
            arr_measures.reverse()
            return json.dumps(arr_measures)
        case _:
            print('Неизвестный метод.')


eel.init("ferro_web_v1") #Инициализации запускаемой дериктории проекта
eel.browsers.set_path("ferro_brave", "brave-portable/brave-portable.exe") #Инициализации запускаемой дериктории проекта
eel.start("home.html", mode='chrome', size=(1920,1080),  cmdline_args=[ '--start-fullscreen'])
