import numpy as np

def levenshtein_matriz(x, y, threshold=None):
    # Calcular la distancia de Levenshtein usando una matriz completa
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)  # Crear matriz de tamaño (lenX+1) x (lenY+1)

    # Inicializar primera columna (coste de eliminar caracteres de x)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1

    # Inicializar primera fila (coste de insertar caracteres en y)
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1

        # Calcular el coste mínimo para cada celda de la matriz
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
            )

    return D[lenX, lenY]  # Retornar la distancia final desde la última celda


def levenshtein_edicion(x, y, threshold=None):
    # Inicializar lista de ediciones y matriz de distancias
    edicion = []
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)

    # Rellenar la primera columna (coste de eliminaciones en x)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1

    # Rellenar la primera fila (coste de inserciones en y)
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1

        # Calcular costes para el resto de la matriz
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
            )

    # Retroceder desde la esquina inferior derecha para reconstruir la secuencia de ediciones
    posX, posY = lenX - 1, lenY - 1
    while posX >= 0 and posY >= 0:
        if D[posX][posY + 1] < D[posX + 1][posY + 1]:  # Movimiento a la izquierda
            edicion.append((x[posX], ''))
            posX -= 1
        elif D[posX + 1][posY] < D[posX + 1][posY + 1]:  # Movimiento hacia arriba
            edicion.append(('', y[posY]))
            posY -= 1
        else:  # Movimiento diagonal (sustitución o coincidencia)
            edicion.append((x[posX], y[posY]))
            posX -= 1
            posY -= 1

    # Manejar caracteres restantes en x
    while posX >= 0 and posY < 0:
        edicion.append((x[posX], ''))
        posX -= 1

    # Manejar caracteres restantes en y
    while posY >= 0 and posX < 0:
        edicion.append(('', y[posY]))
        posY -= 1

    return D[lenX][lenY], edicion[::-1]  # Retornar distancia y lista de ediciones

def levenshtein_reduccion(x, y, threshold=None):
    # Inicializar longitudes de las cadenas y vectores de coste
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int)  # Vector actual
    vv = np.zeros(lenX + 1, dtype=int)  # Vector anterior

    # Rellenar el coste inicial para la primera fila (eliminaciones)
    for i in range(1, lenX + 1): 
        v[i] = v[i - 1] + 1

    # Rellenar el coste para las siguientes filas
    for j in range(1, lenY + 1):
        v, vv = vv, v  # Intercambiar los vectores
        v[0] = vv[0] + 1  # Actualizar el primer elemento (inserción)
        for i in range(1, lenX + 1):
            v[i] = min(
                v[i - 1] + 1,  # Inserción
                vv[i] + 1,  # Eliminación
                vv[i - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
            )
     
    return v[lenX]  # Retornar el coste de edición mínimo


def levenshtein(x, y, threshold):
    # Versión con reducción de coste espacial y parada temprana si se supera el threshold
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int)  # Vector actual
    vv = np.zeros(lenX + 1, dtype=int)  # Vector anterior
    v[0] = 0  # Inicializar el primer coste

    # Inicializar la primera fila (eliminaciones)
    for _ in range(1, lenX + 1): 
        v[_] = v[_ - 1] + 1 

    i = 1
    while i < lenY + 1:
        v, vv = vv, v  # Intercambiar vectores
        v[0] = vv[0] + 1  # Actualizar el coste inicial de la fila actual (inserción)
        for j in range(1, lenX + 1):
            v[j] = min(
                v[j - 1] + 1,  # Inserción
                vv[j] + 1,  # Eliminación
                vv[j - 1] + (x[j - 1] != y[i - 1]),  # Sustitución
            )
        i += 1

        # Parar si el mínimo en la fila actual supera el threshold
        if min(v) > threshold:
            return threshold + 1

    # Retornar el coste mínimo o el threshold+1 si se supera
    return min(v[lenX], threshold + 1)


def levenshtein_cota_optimista(x, y, threshold):
    # Calcular una cota optimista para decidir si se llama a Levenshtein completo
    D = {}
    for l in x:  # Contar ocurrencias de cada carácter en x
        if l not in D:
            D[l] = 1
        else: 
            D[l] += 1
    for j in y:  # Restar ocurrencias de caracteres según aparecen en y
        if j not in D:
            D[j] = -1
        else:
            D[j] -= 1

    pos = 0  # Diferencias positivas (faltantes en y)
    neg = 0  # Diferencias negativas (sobrantes en y)
    for v in D.values():
        if v > 0:
            pos += v
        elif v < 0:
            neg += v
    
    # Determinar la cota optimista como el máximo de las diferencias absolutas
    cota = max(abs(pos), abs(neg))
    
    if cota < threshold:
        # Si la cota es menor al threshold, calcular el Levenshtein completo
        res = levenshtein(x, y, threshold)
    else:
        # Si la cota es mayor, devolver threshold + 1 directamente
        res = threshold + 1

    return res


def damerau_restricted_matriz(x, y, threshold=None):
    # Calcula la distancia Damerau-Levenshtein restringida usando una matriz
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)  # Inicializar matriz de distancias

    for i in range(1, lenX + 1):  # Inicializar primera columna
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):  # Inicializar primera fila
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            # Calcular mínimo entre inserción, eliminación, sustitución y transposición
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
                D[i - 2][j - 2] + 1  # Transposición
                if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2]
                else float('inf')  # Ignorar transposición si no se cumple la condición
            )
    return D[lenX, lenY]


def damerau_restricted_edicion(x, y, threshold=None):
    # Versión de Damerau-Levenshtein restringida con recuperación de la secuencia de operaciones
    edicion = []  # Lista para almacenar las operaciones de edición
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)  # Inicializar matriz de distancias

    for i in range(1, lenX + 1):  # Inicializar primera columna
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):  # Inicializar primera fila
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            # Calcular mínimo entre inserción, eliminación, sustitución y transposición
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
                D[i - 2][j - 2] + 1  # Transposición
                if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2]
                else float('inf')  # Ignorar si no aplica
            )

    # Recuperar las operaciones de edición
    posX, posY = lenX - 1, lenY - 1
    while posX >= 0 and posY >= 0:
        if (
            posX - 1 >= 0
            and posY - 1 >= 0
            and D[posX - 1][posY - 1] < D[posX][posY]
            and x[posX] == y[posY - 1]
            and x[posX - 1] == y[posY]
        ):
            # Transposición
            edicion.append((x[posX - 1 : posX + 1], y[posY - 1 : posY + 1]))
            posX -= 2
            posY -= 2
        elif D[posX][posY + 1] < D[posX + 1][posY + 1]:
            # Eliminación
            edicion.append((x[posX], ''))
            posX -= 1
        elif D[posX + 1][posY] < D[posX + 1][posY + 1]:
            # Inserción
            edicion.append(('', y[posY]))
            posY -= 1
        else:
            # Sustitución o coincidencia
            if x[posX] != y[posY]:
                edicion.append((x[posX], y[posY]))
            else:
                edicion.append((x[posX], y[posY]))
            posX -= 1
            posY -= 1

    # Agregar operaciones restantes si hay más caracteres en una de las cadenas
    while posX >= 0 and posY < 0:
        edicion.append((x[posX], ''))
        posX -= 1
    while posY >= 0 and posX < 0:
        edicion.append(('', y[posY]))
        posY -= 1

    return D[lenX][lenY], edicion[::-1]  # Retornar distancia y lista de ediciones


def damerau_restricted(x, y, threshold=None):
    # Inicializar longitudes y vectores para los costos
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int)
    vv = np.zeros(lenX + 1, dtype=int)
    vvv = np.zeros(lenX + 1, dtype=int)

    # Inicializar el primer vector con los costos de inserción
    for _ in range(1, lenX + 1):
        v[_] = v[_ - 1] + 1

    i = 1
    while i < lenY + 1:
        # Rotar los vectores
        v, vv, vvv = vvv, v, vv
        v[0] = vv[0] + 1

        # Calcular los costos de las operaciones
        for j in range(1, lenX + 1):
            v[j] = min(
                v[j - 1] + 1,  # Inserción
                vv[j] + 1,  # Eliminación
                vv[j - 1] + (x[j - 1] != y[i - 1]),  # Sustitución
                vvv[j - 2] + 1 if x[j - 2] == y[i - 1] and x[j - 1] == y[i - 2] and (i > 1 and j > 1) else float('inf')  # Transposición
            )

        i += 1

        # Si el costo mínimo excede el umbral, devolverlo
        if min(v) > threshold:
            return threshold + 1

    # Retornar el costo mínimo o el umbral incrementado
    return min(v[lenX], threshold + 1)


def damerau_intermediate_matriz(x, y, threshold=None):
    # Inicializar dimensiones y matriz de costos
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)

    # Llenar las primeras filas y columnas con costos de inserción y eliminación
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
                D[i - 2][j - 2] + 1 if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] else float('inf'),  # Transposición
                D[i - 3][j - 2] + 2 if i > 2 and j > 1 and x[i - 3] == y[j - 1] else float('inf'),  # Inserción extra
                D[i - 2][j - 3] + 2 if i > 1 and j > 2 and x[i - 1] == y[j - 3] else float('inf')  # Eliminación extra
            )
    
    # Retornar el costo final de la edición
    return D[lenX, lenY]


def damerau_intermediate_edicion(x, y, threshold=None):
    # Inicialización de la matriz de distancias y variables
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    
    # Llenado de la primera columna y fila con los costos de inserción y eliminación
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,  # Eliminación
                D[i][j - 1] + 1,  # Inserción
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),  # Sustitución
                D[i - 2][j - 2] + 1 if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] else float('inf'),  # Transposición
                D[i - 3][j - 2] + 2 if i > 2 and j > 1 and x[i - 3] == y[j - 1] else float('inf'),  # Inserción extra
                D[i - 2][j - 3] + 2 if i > 1 and j > 2 and x[i - 1] == y[j - 3] else float('inf')  # Eliminación extra
            )

    # Recuperación de la secuencia de operaciones de edición
    edicion = []
    posX, posY = lenX - 1, lenY - 1
    while(posX >= 0 and posY >= 0):
        if posX - 1 >= 0 and posY - 1 >= 0 and D[posX - 1][posY - 1] < D[posX][posY] and (x[posX] == y[posY - 1] and x[posX - 1] == y[posY]):
            # Transposición
            edicion.append((x[posX - 1:posX + 1], y[posY - 1:posY + 1]))
            posX -= 2
            posY -= 2
        elif posX - 2 >= 0 and posY - 1 >= 0 and D[posX - 2][posY - 1] < D[posX][posY] and (x[posX] == y[posY - 1] and x[posX - 2] == y[posY]):
            # Inserción extra
            edicion.append((x[posX - 2:posX + 1], y[posY - 1:posY + 1]))
            posX -= 3
            posY -= 2
        elif posX - 1 >= 0 and posY - 2 >= 0 and D[posX - 1][posY - 2] < D[posX][posY] and (x[posX] == y[posY - 2] and x[posX - 1] == y[posY]):
            # Eliminación extra
            edicion.append((x[posX - 1:posX + 1], y[posY - 2:posY + 1]))
            posX -= 2
            posY -= 3
        elif D[posX][posY + 1] < D[posX + 1][posY + 1]:
            # Operación de inserción
            edicion.append((x[posX], ''))
            posX -= 1
        elif D[posX + 1][posY] < D[posX + 1][posY + 1]:
            # Operación de eliminación
            edicion.append(('', y[posY]))
            posY -= 1
        else:
            # Operación de sustitución o igualdad
            if x[posX] != y[posY]:
                edicion.append((x[posX], y[posY]))  # Sustitución
            else:
                edicion.append((x[posX], y[posY]))  # Igualdad
            posX -= 1
            posY -= 1

    # Si quedan caracteres en x o y
    while(posX >= 0 and posY < 0):
        edicion.append((x[posX], ''))
        posX -= 1
    while(posY >= 0 and posX < 0):
        edicion.append(('', y[posY]))
        posY -= 1

    # Retornar la distancia final y las ediciones realizadas
    return D[lenX][lenY], edicion[::-1]

    
def damerau_intermediate(x, y, threshold=None):
    # Inicialización de las matrices para optimizar el coste espacial
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int)
    vv = np.zeros(lenX + 1, dtype=int)
    vvv = np.zeros(lenX + 1, dtype=int)
    vvvv = np.zeros(lenX + 1, dtype=int)
    
    # Inicialización de la primera fila
    v[0] = 0
    for _ in range(1, lenX + 1): 
        v[_] = v[_ - 1] + 1  # Costo de eliminación

    # Bucle principal para calcular la distancia Damerau-Levenshtein
    i = 1
    while i < lenY + 1:
        # Desplazamiento de las matrices
        v, vv, vvv, vvvv = vvvv, v, vv, vvv
        v[0] = vv[0] + 1  # Costo de inserción

        # Cálculo de distancias para cada columna
        for j in range(1, lenX + 1):
            v[j] = min(
                v[j - 1] + 1,  # Eliminar carácter de x
                vv[j] + 1,     # Insertar carácter de y
                vv[j - 1] + (x[j - 1] != y[i - 1]),  # Sustitución
            )
            
            # Comprobación de transposición
            if (j > 1 and i > 1) and (x[j - 2] == y[i - 1] and x[j - 1] == y[i - 2]):
                v[j] = min(v[j], vvv[j - 2] + 1)
            
            # Caso específico para algunas ediciones de 3 caracteres
            if (j > 2 and i > 1) and (x[j - 3] == y[i - 1] and x[j - 1] == y[i - 2]):
                v[j] = min(v[j], vvv[j - 3] + 2)
            
            # Caso específico para ediciones más complejas
            if (j > 1 and i > 2) and (x[j - 2] == y[i - 1] and x[j - 1] == y[i - 3]):
                v[j] = min(v[j], vvvv[j - 2] + 2)

        i += 1

        # Si la distancia mínima excede el umbral, interrumpe y retorna el umbral + 1
        if min(v) > threshold:
            return threshold + 1
        
    # Retorna el valor mínimo de la última fila de la matriz
    return min(v[lenX], threshold + 1)


opcionesSpell = {
    'levenshtein_m': levenshtein_matriz,
    'levenshtein_r': levenshtein_reduccion,
    'levenshtein':   levenshtein,
    'levenshtein_o': levenshtein_cota_optimista,
    'damerau_rm':    damerau_restricted_matriz,
    'damerau_r':     damerau_restricted,
    'damerau_im':    damerau_intermediate_matriz,
    'damerau_i':     damerau_intermediate
}

opcionesEdicion = {
    'levenshtein': levenshtein_edicion,
    'damerau_r':   damerau_restricted_edicion,
    'damerau_i':   damerau_intermediate_edicion
}

