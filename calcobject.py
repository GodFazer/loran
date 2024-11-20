import numpy as np


# Функція помилки TDoA
def tdoa_error(params, x1, y1, x2, y2, x3, y3, delta_t12, delta_t13, c):
    x, y = params
    d1 = np.sqrt((x - x1) ** 2 + (y - y1) ** 2)
    d2 = np.sqrt((x - x2) ** 2 + (y - y2) ** 2)
    d3 = np.sqrt((x - x3) ** 2 + (y - y3) ** 2)

    delta_t12_calc = (d1 - d2) / c
    delta_t13_calc = (d1 - d3) / c

    error1 = delta_t12_calc - delta_t12
    error2 = delta_t13_calc - delta_t13

    return [error1, error2]


def loss_function(params, tdoa_error_func, args):
    # Обчислення поточної помилки
    errors = tdoa_error_func(params, *args)
    # Обчислення функції втрат як суми квадратів помилок
    loss = sum(e ** 2 for e in errors)

    return loss


def custom_least_squares(tdoa_error_func, initial_guess, args, learning_rate=0.01, max_iterations=10000,
                         tolerance=1e-12):
    x, y = initial_guess
    iteration = 0
    prev_loss = float('inf')

    while iteration < max_iterations:
        # Обчислення функції втрат
        loss = loss_function([x, y], tdoa_error_func, args)

        # Умова зупинки
        if abs(prev_loss - loss) < tolerance:
            #print("exit", prev_loss - loss)
            break

        prev_loss = loss

        # Обчислення градієнта вручну (часткові похідні за x та y)
        delta = 1e-6  # Крок для обчислення чисельного градієнта

        # Чисельний розрахунок градієнта за методом скінченних різниць
        loss_x = loss_function([x + delta, y], tdoa_error_func, args)
        grad_x = (loss_x - loss) / delta

        loss_y = loss_function([x, y + delta], tdoa_error_func, args)
        grad_y = (loss_y - loss) / delta

        # Оновлення координат за градієнтом
        x -= learning_rate * grad_x
        y -= learning_rate * grad_y

        iteration += 1

    return x, y, iteration


# Початкові дані
x1, y1 = 0, 0
x2, y2 = 100000, 0
x3, y3 = 0, 100000

# Виміряні різниці часу прибуття (у секундах)
delta_t12 = (1727631015326.3884 - 1727631015326.2224)/1000 * 10e8
delta_t13 = (1727631015326.3884 - 1727631015326.3376)/1000 * 10e8
c = 3e8 / 10e8

#print(delta_t12,delta_t13)
# Початкове припущення для координат приймача
initial_guess = [50000, 50000]  # Оцінка десь посередині між трьома джерелами

# Використання власної функції least_squares для знаходження координат приймача
# x_opt, y_opt, iterations = custom_least_squares(tdoa_error, initial_guess,args=(x1, y1, x2, y2, x3, y3, delta_t12, delta_t13, c))

#print(f"Estimated coordinates of the receiver: x = {x_opt:.2f}, y = {y_opt:.2f} after {iterations} iterations")