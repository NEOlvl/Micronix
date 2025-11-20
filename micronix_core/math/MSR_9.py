# Условие применимости метода:
#          t <= c/(5 * fE * sqrt(E))
# Волна H01p, с нечётным индексом p = 1 или p = 3

import sys
from math import *
from micronix_core.math.res_x import solve_for_x_1, solve_for_x_2


def res_k2():
    return (2 * pi * fE * sqrt(EB)) / c

def res_h2():
    return sqrt(pow(k2, 2) - pow(v11 / a, 2))

def res_E():
    return pow(c / (2 * pi * fE), 2) * (pow(x / t, 2) + pow(v11 / a, 2))

def res_K1E():
    return pow(1 + (Rii * (L0 * F2) / (E * t * F1)), -1)

def res_G():
    return a * (L0 + t) * pow((2 * a - (L0 + t)) * pow((p[0] * c) / (2 * (L0 + t) * f0 * sqrt(EB)), 2) + (L0 + t), -1)

def res_tg0():
    return pow(K1E, -1) * ((1 / Q0E) - (n / Q00))


# Функция вычисления f1, f2 и A0, AE
# A0 и AE - уровень дБ на котором находится резонансный пик (без- и с- образцом)
# f1 и f2 - частоты на графике в точках с отступом от A0 и AE на -3 дБ
def res_GRAPH() -> list:
    pass

# Константы
c = 300 * pow(10, 9) # мм*с^-1
EB = 1.0006
v11 = 3.831706

# Переменные связанные с резонатором
D = 45 # мм
a = 0.5 * D
L0 = 80 # мм
L = L0 / 2
d = 65 # мм

# Импортируемые или вводимые переменные
f0 = 10 * 10**9 # f0 - резонансная частота без образца
fE = 10 * 10**9 # fE - резонансная частота с образцом
p = [1, 3]

t = int(input("Толщина образца: "))


# Условия
if t >= 2.5 or t <= 0.5:
    print("Неправильное значение t")
    sys.exit()

if f0 > 12 * 10**9 or f0 < 8 * 10**9:
    print("Неправильное значение f0")
    sys.exit()

if fE > 12 * 10**9 or fE < 8 * 10**9:
    print("Неправильное значение fE")
    sys.exit()


# Расчёты
fc = c * v11 / (2 * pi * a * sqrt(EB))

if fE >= fc:
    k2 = res_k2()
    h2 = res_h2()
    x = solve_for_x_1(h2, t, L)
    E = res_E()
    f1, f2, A0, AE = res_GRAPH()
    Q0 = f0 / (f2 - f1)
    QE = fE / (f2 - f1)
    Q00 = Q0 / (1 - pow(10, 0.05 * A0))
    Q0E = QE / (1 - pow(10, 0.05 * AE))
    O = atan(tan(h2 * L) * x / (h2 * t))
    Rii = pow(sin(O), 2) / pow(sin(h2 * L), 2)
    F1 = 1 - (sin(2 * (x + O)) - sin(2 * O)) / (2 * x)
    F2 = 1 - sin(2 * h2 * L) / (2 * h2 * L)
    K1E = res_K1E()
    G = res_G()
    n = G * sqrt(f0 / fE) * pow(v11 / (k2 * a), 2) * ((F1 * t) / a + Rii * (2 * pow((h2 * a) / v11, 2) + (L0 * F2) / a)) / ((E * t * F1) + (Rii * L0 * F2))
    tg0 = res_tg0()

elif fE < fc:
    k2 = res_k2()
    h2 = res_h2()
    beta2 = sqrt(pow(v11 / a, 2) - pow(k2, 2))
    x = solve_for_x_2(beta2, t, L)
    E = res_E()
    f1, f2, A0, AE = res_GRAPH()
    Q0 = f0 / (f2 - f1)
    QE = fE / (f2 - f1)
    Q00 = Q0 / (1 - pow(10, 0.05 * A0))
    Q0E = QE / (1 - pow(10, 0.05 * AE))
    O = atan(tanh(beta2 * L) * x / (beta2 * t))
    Rii = pow(sin(O), 2) / pow(sinh(beta2 * L), 2)
    F1 = 1 - (sin(2 * (x + O)) - sin(2 * O)) / (2 * x)
    F2 = 1 - sinh(2 * beta2 * L) / (2 * beta2 * L)
    K1E = res_K1E()
    G = res_G()
    n = G * sqrt(f0 / fE) * pow(v11 / (k2 * a), 2) * ((F1 * t) / a + Rii * (((L0 * F2) / a) - (2 * pow((beta2 * a) / v11, 2)))) / ((E * t * F1) + (Rii * L0 * F2))
    tg0 = res_tg0()

else:
    print("Ошибка в значениях")



if t <= c/(5 * fE * sqrt(E)):
    print("Метод выполняется выполняется правильно")
else:
    print("Этот метод нельзя использовать вычисления этого образца")