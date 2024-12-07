import numpy as np

def levenshtein_matriz(x, y, threshold=None):
    # esta versión no utiliza threshold, se pone porque se puede
    # invocar con él, en cuyo caso se ignora
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
            )
    return D[lenX, lenY]

def levenshtein_edicion(x, y, threshold=None):
    edicion = []
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
            )

    posX, posY = lenX-1, lenY-1
    while(posX >= 0 or posY >= 0):
        #print(f'posX: {posX} | posY: {posY}\n{x[:posX]}{str.upper(x[posX])}{x[posX+1:]} | {y[:posY]}{str.upper(y[posY])}{y[posY+1:]}')
        if D[posX][posY+1] < D[posX+1][posY+1]:
            # arriba
            edicion.append((x[posX], y[posY]))
            posX -= 1
        elif D[posX+1][posY] < D[posX+1][posY+1]:
            # izquierda
            edicion.append((x[posX], y[posY]))
            posY -= 1
        else:
            # diag
            if (x[posX] != y[posY]):
                edicion.append((x[posX], ' '))
            else:
                edicion.append((x[posX],y[posY]))
            posX -= 1
            posY -= 1
    return D[lenX][lenY], edicion[::-1]

def levenshtein_reduccion(x, y, threshold=None):
    # completar versión reducción coste espacial y parada por threshold
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int) # Current
    vv = np.zeros(lenX + 1, dtype=int) # Previous
    v[0] = 0

    for i in range(1, lenX + 1): 
        v[i] = v[i - 1] + 1

    for j in range(1, lenY + 1):
        v, vv = vv, v
        v[0] = vv[0] + 1
        for i in range(1, lenX + 1):
            v[i] = min(
                v[i - 1] + 1,
                vv[i] + 1,
                vv[i - 1] + (x[i - 1] != y[j - 1]),
                )
     
    return v[lenX] # COMPLETAR Y REEMPLAZAR ESTA PARTE

def levenshtein(x, y, threshold):
    # completar versiÃ³n reducciÃ³n coste espacial y parada por threshold
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenX + 1, dtype=int)
    vv = np.zeros(lenX + 1, dtype=int)
    v[0] = 0
    
    for _ in range(1, lenX + 1): v[_] = v[_ - 1] + 1 

    i = 1
    while(i < lenY + 1):
        v, vv = vv, v
        v[0] = vv[0] + 1
        for j in range(1, lenX + 1):
            v[j] = min(
                    v[j - 1] + 1,
                    vv[j] + 1,
                    vv[j - 1] + (x[j - 1] != y[i - 1]),
                )
        i += 1   
        if min(v) > threshold:
            return threshold+1
        
    return min(v[lenX],threshold+1) # COMPLETAR Y REEMPLAZAR ESTA PARTE

def levenshtein_cota_optimista(x, y, threshold):
    D = {}
    for l in x:
        if l not in D:
            D[l] = 1
        else: 
            D[l] += 1
    for j in y:
        if j not in D:
            D[j] = - 1
        else:
            D[j] -= 1
    
    pos = 0
    neg = 0
    for v in D.values():
        if v > 0:
            pos += v
        elif v < 0:
            neg += 0
    cota = max(abs(pos), abs(neg))
    if cota < threshold:
        res = levenshtein(x, y, threshold) # si cota optimista < threshold => llamamos levenshtein
    else: res = threshold + 1

    return res # COMPLETAR Y REEMPLAZAR ESTA PARTE

def damerau_restricted_matriz(x, y, threshold=None):
    # completar versión Damerau-Levenstein restringida con matriz
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
                D[i - 2][j - 2] + 1 if x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] and (i > 1 and j > 1) else float('inf'),
            )
    return D[lenX, lenY]

def damerau_restricted_edicion(x, y, threshold=None):
    # partiendo de damerau_restricted_matriz añadir recuperar
    # secuencia de operaciones de edición
    edicion = []
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
                D[i - 2][j - 2] + 1 if x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] and (i > 1 and j > 1) else float('inf'),
            )
    posX, posY = lenX-1, lenY-1
    while(posX >= 0 or posY >= 0):
        #print(f'posX: {posX} | posY: {posY}\n{x[:posX]}{str.upper(x[posX])}{x[posX+1:]} | {y[:posY]}{str.upper(y[posY])}{y[posY+1:]}')
        if posX-1 > 0 and posY-1 > 0 and D[posX-1][posY-1] < D[posX+1][posY+1]:
            edicion.append((x[posX-1:posX+1], y[posY-1:posY+1]))
            posX-=2
            posY-=2
        elif D[posX][posY+1] < D[posX+1][posY+1]:
            # arriba
            edicion.append((x[posX], y[posY]))
            posX -= 1
        elif D[posX+1][posY] < D[posX+1][posY+1]:
            # izquierda
            edicion.append((x[posX], y[posY]))
            posY -= 1
        else:
            # diag
            if (x[posX] != y[posY]):
                edicion.append((x[posX], ' '))
            else:
                edicion.append((x[posX],y[posY]))
            posX -= 1
            posY -= 1
    return D[lenX][lenY], edicion[::-1]

def damerau_restricted(x, y, threshold=None):
    # versión con reducción coste espacial y parada por threshold
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenY + 1, dtype=int)
    vv = np.zeros(lenY + 1, dtype=int)
    vvv = np.zeros(lenY + 1, dtype=int)
    for _ in range(0, lenY + 1): v[_] = _ 
    
    i = 1
    while(i < lenX + 1):
        vv[0] = i
        for j in range(1, lenY + 1):
            vv[j] = min(
                    v[j] + 1,
                    vv[j - 1] + 1,
                    v[j - 1] + (x[i - 1] != y[j - 1]),
                    vvv[j - 2] + 1 if x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] and (i > 1 and j > 1) else float('inf')
                )
            if min(vv) > threshold:
                return threshold+1
        i += 1
        vvv = v.copy()
        v = vv.copy()
    return min(v[-1],threshold+1) # COMPLETAR Y REEMPLAZAR ESTA PARTE

def damerau_intermediate_matriz(x, y, threshold=None):
    # completar versión Damerau-Levenstein intermedia con matriz
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
                D[i - 2][j - 2] + 1 if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] else float('inf'),
                D[i - 3][j - 2] + 2 if x[i - 3] == y[j - 1] and i > 2 and j > 1 else float('inf'),
                D[i - 2][j - 3] + 2 if x[i - 1] == y[j - 3] and i > 1 and j > 2 else float('inf'),
            )
    return D[lenX, lenY]

def damerau_intermediate_edicion(x, y, threshold=None):
    # partiendo de matrix_intermediate_damerau añadir recuperar
    # secuencia de operaciones de edición
    # completar versión Damerau-Levenstein intermedia con matriz
    
    # NO ESTA BIEN
    
    lenX, lenY = len(x), len(y)
    D = np.zeros((lenX + 1, lenY + 1), dtype=int)
    for i in range(1, lenX + 1):
        D[i][0] = D[i - 1][0] + 1
    for j in range(1, lenY + 1):
        D[0][j] = D[0][j - 1] + 1
        for i in range(1, lenX + 1):
            D[i][j] = min(
                D[i - 1][j] + 1,
                D[i][j - 1] + 1,
                D[i - 1][j - 1] + (x[i - 1] != y[j - 1]),
                D[i - 2][j - 2] + 1 if i > 1 and j > 1 and x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] else float('inf'),
                D[i - 3][j - 2] + 2 if x[i - 3] == y[j - 1] and i > 2 and j > 1 else float('inf'),
                D[i - 2][j - 3] + 2 if x[i - 1] == y[j - 3] and i > 1 and j > 2 else float('inf'),
            )
    edicion = []
    posX, posY = lenX-1, lenY-1
    while(posX >= 0 or posY >= 0):
        #print(f'posX: {posX} | posY: {posY}\n{x[:posX]}{str.upper(x[posX])}{x[posX+1:]} | {y[:posY]}{str.upper(y[posY])}{y[posY+1:]}')
        if posX-2 >= 0 and posY-1 >= 0 and D[posX-2][posY-1] < D[posX+1][posY+1]:
            edicion.append(f'posX: {posX} | posY: {posY} {x[:posX]}{str.upper(x[posX])}{x[posX+1:]} | {y[:posY]}{str.upper(y[posY])}{y[posY+1:]}')
            edicion.append((x[posX-1:posX+1],y[posY-2:posY+1]))
            
            posX-=3
            posY-=2
        elif posX-1 >= 0 and posY-2 >= 0 and D[posX-1][posY-2] < D[posX+1][posY+1]:
            edicion.append((x[posX-1:posX+1],y[posY-2:posY+1]))
            posX-=2
            posY-=3
        elif posX-1 >= 0 and posY-1 >= 0 and D[posX-1][posY-1] < D[posX+1][posY+1]:
            edicion.append((x[posX-1:posX+1], y[posY-1:posY+1]))
            posX-=2
            posY-=2
        elif D[posX][posY+1] < D[posX+1][posY+1]:
            # arriba
            edicion.append((x[posX], y[posY]))
            posX -= 1
        elif D[posX+1][posY] < D[posX+1][posY+1]:
            # izquierda
            edicion.append((x[posX], y[posY]))
            posY -= 1
        else:
            # diag
            if (x[posX] != y[posY]):
                edicion.append((x[posX], ' '))
            else:
                edicion.append((x[posX],y[posY]))
            posX -= 1
            posY -= 1
    return D[lenX][lenY], edicion[::-1]
    
def damerau_intermediate(x, y, threshold=None):
    # versión con reducción coste espacial y parada por threshold
    
    lenX, lenY = len(x), len(y)
    v = np.zeros(lenY + 1, dtype=int)
    vv = np.zeros(lenY + 1, dtype=int)
    vvv = np.zeros(lenY + 1, dtype=int)
    vvvv = np.zeros(lenY + 1, dtype=int)
    for _ in range(0, lenY + 1): v[_] = _ 
    
    i = 1
    while(i < lenX + 1):
        vv[0] = i
        for j in range(1, lenY + 1):
            vv[j] = min(
                    v[j] + 1,
                    vv[j - 1] + 1,
                    v[j - 1] + (x[i - 1] != y[j - 1]),
                    vvv[j - 2] + 1 if x[i - 2] == y[j - 1] and x[i - 1] == y[j - 2] and (i > 1 and j > 1) else float('inf'),
                    vvvv[j - 2] + 2 if x[i - 3] == y[j - 1] and (i > 2 and j > 1) else float('inf'),
                    vvv[j - 3] + 2 if x[i - 1] == y[j - 3] and (i > 1 and j > 2) else float('inf')
                )
            if min(vv) > threshold:
                return threshold+1
        i += 1
        vvvv = vvv.copy()
        vvv = v.copy()
        v = vv.copy()
        
    return min(v[-1],threshold+1) # COMPLETAR Y REEMPLAZAR ESTA PARTE

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

