from cmath import log10

import math
import numpy as np
from scipy.special import jv, yn
import scipy.optimize as opt
from scipy.optimize import fsolve

EB = 1.0006
v11 = 3.831706
c = 299.792458 * 10**9
p = 2


def Methot_Vlad(t, D, f0, f1, f2, fE, L0, delL, A0, AE):

    data_mass_error = ["Error"]
    status_error = False

    if not (8 * 10 ** 9 <= f0 <= 12 * 10 ** 9):
        status_error = True
        data_mass_error.append(f"Неподходящая частота без образца f0 = {f0}")

    if not (D > t):
        status_error = True
        data_mass_error.append(f"Неподходящее значние D = {D} или t = {t}")

    a = 0.5 * D
    k2 = 2 * math.pi * f0 * pow(EB, 0.5) / c
    h2 = pow(pow(k2, 2) - pow(v11 / a, 2), 0.5)

    drob = (math.tan(h2*(delL + t)))/(h2 * t)

    def equationVlad(x):
        return np.tan(x) / x + drob

    x = fsolve(equationVlad, 1)[0]
    print(f"x = {x}")

    E = pow(c / (2 * math.pi * f0), 2) * (pow(x / t, 2) + pow(v11 / a, 2))

    if not (1.2 <= E <= 200):
        status_error = True
        data_mass_error.append(f"Неподходящая диэлектрическая проницаемость E = {E}")

    LE = L0 - delL
    F1 = 1 - (math.sin(2 * x) / (2 * x))
    F2 = 1 - ((math.sin(2 * h2 * (LE - t))) / (2 * h2 * (LE - t)))
    ksi = pow(math.sin(x), 2) / pow(math.sin(h2 * (LE - t)), 2)
    K1E = pow(1 + (ksi * (LE - t) * F2) / (E * t * F1), -1)

    G = a * L0 * pow((2 * a - L0) * pow((p * c) / (2 * L0 * f0 * pow(EB, 0.5)), 2) + L0, -1)
    nu = G * pow(v11 / k2 * a, 2) * (pow(x / v11, 2) * pow(a / t, 2) + ((F1 * t) / a) + ksi * (pow((h2 * a) / v11, 2) + ((LE - t) * F2) / a) / E * t * F1 + ksi * (LE - t) * F2)

    Q0 = f0 / (f2 - f1)
    QE = fE / (f2 - f1)
    Q00 = Q0 / (1 - pow(10, 0.05 * A0))
    Q0E = QE / (1 - pow(10, 0.05 * AE))

    tgo = pow(K1E, -1) * ((1 / Q0E) - (nu / Q00))

    if not (5 * 10**-5 <= tgo <= 10**-2):
        status_error = True
        data_mass_error.append(f"Неподходящий тангенс угла диэлектрических потерь tgo = {tgo}")

    # data_mass_ok = ["Ok", f"Диэлектрическая проницаемость = {float(E)}", f"Тангенс угла диэлектрических потерь = {float(tgo) * 10 ** 4} * 10^-4"]
    data_mass_ok = {"status": "ok", "E": float(E), "tgo": float(tgo)}

    return data_mass_ok

def Methot_Nikita(t, D, L0, f0, f1, f2, fE, A0, AE):

    data_mass_error = ["Error"]
    status_error = False

    if not (8 * 10**9 <= f0 <= 12 * 10**9):
        status_error = True
        data_mass_error.append(f"Неподходящая частота без образца f0 = {f0}")

    if not (D > t):
        status_error = True
        data_mass_error.append(f"Неподходящее значние D = {D} или t = {t}")

    a = 0.5 * D
    k2 = 2 * math.pi * fE * pow(EB, 0.5) / c
    h2 = pow(pow(k2, 2) - pow(v11 / a, 2), 0.5)

    drob = (math.tan(h2 * (L0 + t))) / (h2 * t)

    def equationVlad(x):
        return np.tan(x) / x + drob

    x = fsolve(equationVlad, 1)[0]

    E = pow(c / (2 * math.pi * fE), 2) * (pow(x / t, 2) + pow(v11 / a, 2))

    if not (1.2 <= E <= 200):
        status_error = True
        data_mass_error.append(f"Неподходящая диэлектрическая проницаемость E = {E}")

    Q0 = f0 / (f2 - f1)
    QE = fE / (f2 - f1)
    Q00 = Q0 / (1 - pow(10, 0.05 * A0))
    Q0E = QE / (1 - pow(10, 0.05 * AE))
    ksi = pow(math.sin(x), 2) / pow(math.sin(h2 * (L0 - t)), 2)
    F1 = 1 - math.sin(2 * x) / (2 * x)
    F2 = 1 - math.sin(2 * h2 * (L0 - t)) / (2 * h2 * (L0 - t))
    K1E = pow(1 + (ksi * (L0 - t) * F2) / (E * t * F1), -1)
    G = a * L0 * pow((2 * a - L0) * pow((p * c) / (2 * L0 * f0 * pow(EB, 0.5)), 2) + L0, -1)

    nu1 = G * pow(f0 / fE, 0.5) * pow(v11 / (k2 * a), 2)
    nu2 = pow(x / v11, 2) * pow(a / t, 2) + (t * F1) / a + ksi * (pow(h2 * a / v11, 2) + ((L0 - t) * F2) / a)
    nu3 = E * t * F1 + ksi * (L0 - t) * F2
    nu = nu1 * nu2 / nu3
    tgo = pow(K1E, -1) * (1 / Q0E - nu / Q00)

    if not (5 * 10 ** -5 <= tgo <= 10 ** -2):
        status_error = True
        data_mass_error.append(f"Неподходящий тангенс угла диэлектрических потерь tgo = {tgo}")

    # data_mass_ok = ["Ok", f"Диэлектрическая проницаемость = {float(E)}",
    #                 f"Тангенс угла диэлектрических потерь = {float(tgo) * 10 ** 4} * 10^-4"]
    data_mass_ok = {"status": "ok", "E": float(E), "tgo": float(tgo)}
    print(data_mass_ok)
    # return data_mass_ok if not status_error else data_mass_error
    return data_mass_ok

def Methot_Marina(a, f0, f1, f2, fE, R0, L, A0, AE, Q0, QE ):
     # print(a, f0, f1, f2, fE, R0, L, A0, AE, Q0, QE)

    data_mass_error = ["Error"]
    status_error = False

    D = 2 * R0
    d = 2 * a
    if not (3 <= d <= 13):
        status_error = True
        data_mass_error = f"Неподходящий деаметр d = {d}"


    if not (8 * 10 ** 9 <= f0 <= 12 * 10 ** 9):
        status_error = True
        data_mass_error = f"Неподходящая частота без образца f0 = {f0}"

    k2 = (2 * math.pi * fE * np.sqrt(EB)) / c
    h = (p * math.pi) / L
    y = pow(pow(k2 * a, 2) - pow(h * a, 2), 0.5)
    b = D / d

    J0_y = jv(0, y)
    J1_y = jv(1, y)
    J1_yb = jv(1, y*b)

    N0_y = yn(0, y)
    N1_y = yn(1, y)
    N1_yb = yn(1, y*b)

    Z0_y = J0_y - (J1_yb / N1_yb) * N0_y
    Z1_y = J1_y - (J1_yb / N1_yb) * N1_y

    drobZ = Z1_y / (y * Z0_y)

    def equationMarina(x):
        return (jv(1, x) / (x * jv(0, x))) - drobZ

    x = opt.fsolve(equationMarina, 2)[0]

    E = (pow(x, 2) + pow(h * a, 2)) / pow(k2 * a, 2)
    E_NEW = E / 3.2

    if not (1.2 <= E_NEW <= 20):
        status_error = True
        data_mass_error = f"Неподходящее значение E = {E_NEW}"

    k1 = (2 * math.pi * fE * pow(E, 0.5)) / c
    # Q0 = f0 / (f2 - f1)
    # QE = fE / (f2 - f1)
    Q00 = Q0 / (1 - pow(10, 0.05 * A0))
    Q0E = QE / (1 - pow(10, 0.05 * AE))

    J0_x = jv(0, x)
    J1_x = jv(1, x)

    J0_yb = jv(0, y*b)
    J1_ybb = jv(0, y*b**2)
    N0_yb = yn(0, y*b)
    N1_ybb = yn(0, y*b**2)
    Z0_yb = J0_yb - (J1_ybb / N1_ybb) * N0_yb

    J2_y = jv(2, y)
    N2_y = yn(2, y)
    Z2_y = J2_y - (J1_yb / N1_yb) * N2_y

    J2_x = jv(2, x)

    chisl_K1E = pow((k2 * a) / y, 2) * (pow(J0_x / Z0_y, 2) * (pow(b, 2) * pow(Z0_yb, 2) - pow(Z1_y, 2) + Z0_y * Z2_y))
    znam_K1E = pow((k1 * a) / x, 2) * (pow(J1_x, 2) - J0_x * J2_x)
    drob_K1E = chisl_K1E / znam_K1E
    K1E = pow(1 + drob_K1E, -1)

    Jx = pow(J1_x, 2) - J0_x * J2_x
    Zy = pow(Z1_y, 2) - Z0_y * Z2_y

    chisl_n = pow(f0 / fE, 1.5) * ((pow(D, 2) * L) / pow(a, 2)) * pow(J0_x / Z0_y, 2) * pow(Z0_yb, 2) + pow((h * a) / x, 2) * Jx + pow((h * a) / y, 2) * pow(J0_x/Z0_y, 2) * (pow(b, 2) * pow(Z0_yb, 2) - Zy)
    znam_n = 4 * ((D - L) * pow((p * c) / (2 * L * f0 * pow(EB, 0.5)), 2) + L) * (pow((k1 * a) / x, 2) * Jx + pow((k2 * a) / y, 2) * pow(J0_x / Z0_y, 2) * (pow(b, 2) * pow(Z0_yb, 2) - Zy))
    n = chisl_n / znam_n

    tgo = pow(K1E, -1) * ((1 / Q0E) - (n / Q00))
    tgo_NEW = tgo
    if not (5 * 10 ** -5 <= tgo_NEW <= 10 ** -2):
        status_error = True
        data_mass_error = f"Неподходящее значение tgo = {tgo_NEW}"

    data_mass_ok = {"status": "ok", "E": float(E_NEW), "tgo" : float(tgo_NEW)}
    return  data_mass_ok
    # return data_mass_ok if not status_error else {'status': 'error', 'text_error': data_mass_error}

def Methot_Egor(a, b, r, R, f1, f1sh, deld, Ms, form):

    delf0 = (f1 - f1sh)/f1
    ushT = 0.000216666 * Ms + 1.03
    K1 = 0.535 * math.pi * pow(R, 2)

    # 0 - Круг
    # 1 - Квадрат

    # Для круга
    if form == 0:
        Esh = (1.085 * (1 + ((0.539*pow(R, 2)*delf0)/pow(r, 2)/(1 - delf0))+(1.7 - 2.5 * delf0)*delf0))/(1 + (1.7 - 2.5*delf0)*delf0 + 0.39*ushT*delf0*(1 - delf0))
        Esh2 = ((0.2726 * (pow(R, 2) / pow(r, 2)) * deld) / (pow(1 - delf0, 2) * pow(1 + delf0 * (0.486 + 1.56 * math.log(R / (2.14 * r))), 2) * (1 + Esh * ushT * 1.55 * (pow(r, 2) / pow(R, 2)) * (1 - 1.53 * delf0)))) + ((deld * (Esh * 1.56 * (pow(r, 2) / pow(R, 2)) * (1 - 1.53 * delf0) * (ushT - 1) + Esh - 1)) / (1 + Esh * ushT * 1.55 * (pow(r, 2) / pow(R, 2)) * (1 - 1.53 * delf0)))

    # Для квадрата
    if form == 1:
        Esh = (1.135 * (1 + ((K1 * delf0) / (1 - delf0)) + (2.1 - 2.5 * delf0) * delf0)) / (1 + (2.1 - 2.5 * delf0) * delf0 + 0.39 * ushT * delf0 * (1 - delf0))
        Esh2 = ((0.2726 * ((math.pi * pow(R, 2)) / (a * b)) * deld) / (pow(1 - delf0, 2) * pow(1 + delf0 * (0.486 + 1.56 * math.log((R * math.sqrt(math.pi)) / (2.14 * math.sqrt(a*b)))), 2) * (1 + Esh * ushT * 1.55 * ((a*b) / (math.pi * pow(R, 2))) * (1 - 1.53 * delf0)))) + ((deld * (Esh * 1.56 * ((a*b) / (math.pi * pow(R, 2))) * (1 - 1.53 * delf0) * (ushT - 1))) / (1 + Esh * ushT * 1.55 * ((a*b) / (math.pi * pow(R, 2))) * (1 - 1.53 * delf0)))

    tgdelE = Esh2 / Esh
    arr_data = [Esh, Esh2, tgdelE]
    # return arr_data

    return f"Значение tgdelE = {tgdelE}"

def Methot_Egor_st(fe, f0, f10, f20, f1e, f2e, R, r):
    E = 1+(0.539*(pow((R/r),2)))*((f0-fe)/f0)
    Q0 = f0/(f20 - f10)
    QE = fe/(f2e - f1e)
    tgo = (0.269/E)*(pow((R/r), 2))*((1/QE)-(1/Q0))

    data_mass_ok = {"status": "ok", "E": float(E), "tgo": float(tgo)}
    return data_mass_ok

# print(Methot_Egor(1.12, 1.12, 0.81, 11, 10.145, 10.155, 0.000564469, 0, 0))

def Method_real(fe, f0, f10, f20, f1e, f2e, R, r):
    print(fe, f0, f10, f20, f1e, f2e, R, r)
    delF0 = (f0 - fe)/f0
    #delF0 = 0.06801379990142928
    print(delF0)
    mu = 1.05
    e_real = 1.085*(1+(((0.539*(pow(R,2)/pow(r,2))*delF0)/1-delF0)+(1.7-2.5*delF0)*delF0)/(1+ (1.7-2.5*delF0)*delF0 + 0.39*mu*delF0*(1-delF0)))
    K = 1.5
    d0 = (2*abs(f10 - f20))/(f10 + f20)

    dx = (2*abs(f1e - f2e))/(f1e + f2e)
    d0s = d0/(1+K)
    delD = dx - d0s
    # print(delD)
    e_image = ((0.2726*(pow(R,2)/pow(r,2))*delD)/(pow(1 - delF0, 2)*pow(1+delF0*(0.486+1.56*math.log(R/(2.14*r))), 2))*(1 + e_real*mu*1.55*(pow(r,2)/pow(R,2))*(1 - 1.53*delF0)))+((e_real*1.56*(pow(r,2)/pow(R,2))*(1-1.53*delF0)*(mu -1)+e_real -1)/(1+e_real*mu*1.55*(pow(r,2)/pow(R,2))*(1 - 1.53*delF0)))*delD
    tgo = e_image/e_real
    data_mass_ok = {"status": "ok", "E": float(e_real), "tgo": tgo}
    return data_mass_ok


# print(Methot_Egor_st(9460000000, 10150000000, 10145000000, 10155000000, 9455000000, 9465000000, 11, 0.81))
# print(Method_real(9460000000, 10150000000, 10145000000, 10155000000, 9455000000, 9465000000, 11, 0.81))
#
#
# print(Methot_Egor_st(12143750000.0, 12300000000.0, 12281250000.0, 12318750000.0, 12131250000.0, 12156250000.0, 11.0, 0.81))
# print(Method_real(12143750000.0, 12300000000.0, 12281250000.0, 12318750000.0, 12131250000.0, 12156250000.0, 11.0, 0.81))
