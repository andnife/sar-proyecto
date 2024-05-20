import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import sys
import math
from pathlib import Path
from typing import Optional, List, Union, Dict
import pickle

class SAR_Indexer:
    """
    Prototipo de la clase para realizar la indexacion y la recuperacion de artículos de Wikipedia
        
        Preparada para todas las ampliaciones:
          parentesis + multiples indices + posicionales + stemming + permuterm

    Se deben completar los metodos que se indica.
    Se pueden añadir nuevas variables y nuevos metodos
    Los metodos que se añadan se deberan documentar en el codigo y explicar en la memoria
    """

    # lista de campos, el booleano indica si se debe tokenizar el campo
    # NECESARIO PARA LA AMPLIACION MULTIFIELD
    fields = [
        ("all", True), ("title", True), ("summary", True), ("section-name", True), ('url', False),
    ]
    def_field = 'all'
    PAR_MARK = '%'
    # numero maximo de documento a mostrar cuando self.show_all es False
    SHOW_MAX = 10

    all_atribs = ['urls', 'index', 'sindex', 'ptindex', 'docs', 'weight', 'articles',
                  'tokenizer', 'stemmer', 'show_all', 'use_stemming']

    def __init__(self):
        """
        Constructor de la classe SAR_Indexer.
        NECESARIO PARA LA VERSION MINIMA

        Incluye todas las variables necesaria para todas las ampliaciones.
        Puedes añadir más variables si las necesitas 

        """
        self.urls = set() # hash para las urls procesadas,
        self.index = {} # hash para el indice invertido de terminos --> clave: termino, valor: posting list
        self.sindex = {} # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {} # hash para el indice permuterm.
        self.posindex = {} # hash para el indice posicional.
        self.docs = {} # diccionario de terminos --> clave: entero(docid),  valor: ruta del fichero.
        self.weight = {} # hash de terminos para el pesado, ranking de resultados.
        self.articles = {} # hash de articulos --> clave entero (artid), valor: la info necesaria para diferencia los artículos dentro de su fichero
        self.tokenizer = re.compile("\W+") # expresion regular para hacer la tokenizacion
        self.stemmer = SnowballStemmer('spanish') # stemmer en castellano
        self.show_all = False # valor por defecto, se cambia con self.set_showall()
        self.show_snippet = False # valor por defecto, se cambia con self.set_snippet()
        self.use_stemming = False # valor por defecto, se cambia con self.set_stemming()
        self.use_ranking = False  # valor por defecto, se cambia con self.set_ranking()


    ###############################
    ###                         ###
    ###      CONFIGURACION      ###
    ###                         ###
    ###############################


    def set_showall(self, v:bool):
        """

        Cambia el modo de mostrar los resultados.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_all es True se mostraran todos los resultados el lugar de un maximo de self.SHOW_MAX, no aplicable a la opcion -C

        """
        self.show_all = v


    def set_snippet(self, v:bool):
        """

        Cambia el modo de mostrar snippet.
        
        input: "v" booleano.

        UTIL PARA TODAS LAS VERSIONES

        si self.show_snippet es True se mostrara un snippet de cada noticia, no aplicable a la opcion -C

        """
        self.show_snippet = v


    def set_stemming(self, v:bool):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v



    #############################################
    ###                                       ###
    ###      CARGA Y GUARDADO DEL INDICE      ###
    ###                                       ###
    #############################################


    def save_info(self, filename:str):
        """
        Guarda la información del índice en un fichero en formato binario
        
        """
        info = [self.all_atribs] + [getattr(self, atr) for atr in self.all_atribs]
        with open(filename, 'wb') as fh:
            pickle.dump(info, fh)

    def load_info(self, filename:str):
        """
        Carga la información del índice desde un fichero en formato binario
        
        """
        #info = [self.all_atribs] + [getattr(self, atr) for atr in self.all_atribs]
        with open(filename, 'rb') as fh:
            info = pickle.load(fh)
        atrs = info[0]
        for name, val in zip(atrs, info[1:]):
            setattr(self, name, val)

    ###############################
    ###                         ###
    ###   PARTE 1: INDEXACION   ###
    ###                         ###
    ###############################

    def already_in_index(self, article:Dict) -> bool:
        """

        Args:
            article (Dict): diccionario con la información de un artículo

        Returns:
            bool: True si el artículo ya está indexado, False en caso contrario
        """
        return article['url'] in self.urls


    def index_dir(self, root:str, **args):
        """
        
        Recorre recursivamente el directorio o fichero "root" 
        NECESARIO PARA TODAS LAS VERSIONES
        
        Recorre recursivamente el directorio "root"  y indexa su contenido
        los argumentos adicionales "**args" solo son necesarios para las funcionalidades ampliadas

        """
        self.multifield = args['multifield']
        self.positional = args['positional']
        self.stemming = args['stem']
        self.permuterm = args['permuterm']

        file_or_dir = Path(root)
        
        if file_or_dir.is_file():
            # is a file
            self.index_file(root)
        elif file_or_dir.is_dir():
            # is a directory
            for d, _, files in os.walk(root): #explora la ruta del directorio
                for filename in sorted(files):
                    if filename.endswith('.json'):
                        fullname = os.path.join(d, filename) #crea la ruta del archivo
                        self.index_file(fullname) #indexa el archivo con la ruta obtenida anteriormente
        else:
            print(f"ERROR:{root} is not a file nor directory!", file=sys.stderr)
            sys.exit(-1)

        ##########################################
        ## COMPLETAR PARA FUNCIONALIDADES EXTRA ##
        ##########################################
        
        
    def parse_article(self, raw_line:str) -> Dict[str, str]:
        """
        Crea un diccionario a partir de una linea que representa un artículo del crawler

        Args:
            raw_line: una linea del fichero generado por el crawler

        Returns:
            Dict[str, str]: claves: 'url', 'title', 'summary', 'all', 'section-name'
        """
        
        article = json.loads(raw_line)
        sec_names = []
        txt_secs = ''
        for sec in article['sections']:
            txt_secs += sec['name'] + '\n' + sec['text'] + '\n'
            txt_secs += '\n'.join(subsec['name'] + '\n' + subsec['text'] + '\n' for subsec in sec['subsections']) + '\n\n'
            sec_names.append(sec['name'])
            sec_names.extend(subsec['name'] for subsec in sec['subsections'])
        article.pop('sections') # no la necesitamos 
        article['all'] = article['title'] + '\n\n' + article['summary'] + '\n\n' + txt_secs
        article['section-name'] = '\n'.join(sec_names)

        return article
                
    
    def index_file(self, filename:str):
        """

        Indexa el contenido de un fichero.
        
        input: "filename" es el nombre de un fichero generado por el Crawler cada línea es un objeto json
            con la información de un artículo de la Wikipedia

        NECESARIO PARA TODAS LAS VERSIONES

        dependiendo del valor de self.multifield y self.positional se debe ampliar el indexado


        """

        #BLANCA

        docId = len(self.docs) + 1
        self.docs[docId] = filename

        for line in open(filename, encoding='utf-8', errors='replace'): # Enumerate no necesario
            j = self.parse_article(line.strip())
            if self.already_in_index(j):
                continue
            artId = len(self.articles) + 1
            self.articles[artId] = (j['url'], j['title'], j['all'])

            content = j['all']
            tokens = self.tokenize(content)
            
            for token in tokens:
                term = token.lower()
                if term not in self.index:
                    self.index[term] = []
                if artId not in self.index[term]:
                    self.index[term].append(artId)
                if self.positional: # ADE
                    temppos = 0
                    positions = []
                    while temppos != -1:
                        temppos = content.find(term, temppos)
                        if temppos != -1:
                            positions.append(temppos)
                    if term not in self.posindex:
                        self.posindex[term] = []
                    if artId not in self.posindex[term]:
                        self.posindex[term][artId] = positions
                    
                    
                
            self.urls.add(j['url'])
            
        # Invert index convertion
        terms = sorted(self.index.keys())
        invertedIndex = {}
        for t in terms:
            invertedIndex[t] = self.index[t]
            
        self.index = invertedIndex

    def set_stemming(self, v:bool):
        """

        Cambia el modo de stemming por defecto.
        
        input: "v" booleano.

        UTIL PARA LA VERSION CON STEMMING

        si self.use_stemming es True las consultas se resolveran aplicando stemming por defecto.

        """
        self.use_stemming = v


    def tokenize(self, text:str):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Tokeniza la cadena "texto" eliminando simbolos no alfanumericos y dividientola por espacios.
        Puedes utilizar la expresion regular 'self.tokenizer'.

        params: 'text': texto a tokenizar

        return: lista de tokens

        """
        return self.tokenizer.sub(' ', text.lower()).split()


    def make_stemming(self):
        """

        Crea el indice de stemming (self.sindex) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE STEMMING.

        "self.stemmer.stem(token) devuelve el stem del token"


        """
        #BLANCA

        terms = list(self.index.keys())
        for term in terms:
            stemmed = self.stemmer.stem(term)
            if stemmed not in self.sindex:
                self.sindex[stemmed] = [term]
            else:
                self.sindex[stemmed].append(term)


    
    def make_permuterm(self):
        """

        Crea el indice permuterm (self.ptindex) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        """
        # ADE
        
        ####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE STEMMING ##
        ####################################################
        
        # Itero cada termino de los indexados
        for term in list(self.index.keys()):
            # Añado el comodin al final y guardo la modificacion a la posting list del permuterm
            termmod = term + '*'
            self.ptindex[termmod] = self.index[term]
            
            # Voy a ir rotando el comodin y almacenando en la posting list del permuterm
            for i in range(len(termmod)):
                termmod = termmod[i:] + termmod[:i]
                self.ptindex[termmod] = self.index[term]
        #pass

    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        pass
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################

        



    #################################
    ###                           ###
    ###   PARTE 2: RECUPERACION   ###
    ###                           ###
    #################################

    ###################################
    ###                             ###
    ###   PARTE 2.1: RECUPERACION   ###
    ###                             ###
    ###################################


    def solve_query(self, query:str, prev:Dict={}):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen


        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.


        return: posting list con el resultado de la query

        """
        #IVAN

        if not query  or len(query) == 0:
            return []
        
        terminos = self.tokenize(query)
        # falta tratar query
        res = []

        for x in terminos:
            if x in self.index:
                docs = self.index[x]
                for doc in docs:
                    if doc not in res:
                        res.append(doc)
        return res            
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################




    def get_posting(self, term:str, field:Optional[str]=None):
        """

        Devuelve la posting list asociada a un termino. 
        Dependiendo de las ampliaciones implementadas "get_posting" puede llamar a:
            - self.get_positionals: para la ampliacion de posicionales
            - self.get_permuterm: para la ampliacion de permuterms
            - self.get_stemming: para la amplaicion de stemming


        param:  "term": termino del que se debe recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario si se hace la ampliacion de multiples indices

        return: posting list
        
        NECESARIO PARA TODAS LAS VERSIONES

        """
        #IVAN

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        x = self.index

        if term in x:
            return self.index[term]
        else:
            return[]

        #ampliar el metodo para aplicar las funcionalidades extra


    def get_positionals(self, terms:str, index):
        """

        Devuelve la posting list asociada a una secuencia de terminos consecutivos.
        NECESARIO PARA LA AMPLIACION DE POSICIONALES

        param:  "terms": lista con los terminos consecutivos para recuperar la posting list.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        
        # ADE
        
        ########################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE POSICIONALES ##
        ########################################################
        
        # Copio a un diccionario auxiliar las entradas de posting posicional de los terminos solicitados
        dict = {}
        list = terms.split()
        for t in list:
            if t not in dict:
                dict[t] = {}
            dict[t] = self.posindex[t]
        
        # Obtengo los documentos en los que aparecen todos los terminos solicitadoss
        docs = dict[list[0]]
        for t in list[1:]:
            docs &= self.posindex[t]
        
        # Elimino las entradas de documentos no compartidos del diccionario auxiliar 
        for t in list:
            for d in list(self.posindex[t].keys()):
                if d not in docs:
                    del dict[t][d]
        
        # Miro en cada documento comun las posiciones de los terminos solicitados para ver si son consecutivas
        
        pass


    def get_stemming(self, term:str, field: Optional[str]=None):
        """

        Devuelve la posting list asociada al stem de un termino.
        NECESARIO PARA LA AMPLIACION DE STEMMING

        param:  "term": termino para recuperar la posting list de su stem.
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        #BLANCA
        
        stem = self.stemmer.stem(term)
        res = []

        if stem not in self.sindex:
            return res
        terms = list(self.sindex[stem])

        for t in range(len(terms)):
            terms[t] = self.index[terms[t]]

        for t in range(len(terms)):
            res = self.or_posting(res, terms[t])
        
        return res

    def get_permuterm(self, term:str, field:Optional[str]=None):
        """

        Devuelve la posting list asociada a un termino utilizando el indice permuterm.
        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        param:  "term": termino para recuperar la posting list, "term" incluye un comodin (* o ?).
                "field": campo sobre el que se debe recuperar la posting list, solo necesario se se hace la ampliacion de multiples indices

        return: posting list

        """
        # ADE
        
        ##################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA PERMUTERM ##
        ##################################################
        
        # Compruebo que no se use mas de un comodin por palabra
        if (term.count('*') + term.count('?') > 1):
            print('No se permite mas de un comodin por palabra.')
            return None
        
        # Obtengo la parte de antes y despues del comodin
        twoterms = re.split(r'[?*]', term)
        
        # Aqui almacenare la posting list de buscar la parte delantera y trasera al comodin
        firsttermlist = []
        secondtermlist = []
        
        # Itero cada termino
        for term in list(self.ptindex.keys()):
            # Si el termino obtenido de la lista de permuterm termina por la parte delantera
            # al comodin, añado la posting list
            if term.endswith(twoterms[0]):
                secondtermlist.append(self.ptindex[term])
                
            # Si el termino obtenido de la lista de permuterm empieza por la parte trasera
            # al comodin, añado la posting list
            if term.startswith(twoterms[1]):
                firsttermlist.append(self.ptindex[term])
        
        # Devuelvo la interseccion de las posting list obtenidas
        return self.and_posting(firsttermlist, secondtermlist)
        

    def reverse_posting(self, p:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Devuelve una posting list con todas las noticias excepto las contenidas en p.
        Util para resolver las queries con NOT.


        param:  "p": posting list


        return: posting list con todos los artid exceptos los contenidos en p

        """
        #IVAN
        #creamos una variable con todos los documentos
        x = self.index

        #creamos otra variable con los documentos a eliminar
        y= p.sort()

        #recorremos ambas listas elminando los elementos de x que esten en p
        for t in x:
            for z in y:
                if y[z] == x[t]:
                    del x[t]
        return x 
        
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def and_posting(self, p1:list, p2:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el AND de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos en p1 y p2

        """
        #IVAN

        #creamos lista resultado y variables para iterar las listas
        res = []
        i=0
        j=0
        #recorremos las listas hasta que se acabe una de las dos
        while i< len(p1) & j< len(p2):
            #si los elementos coinciden los añadimos al resultado y aumentamos el valor
            #de las variables para iterar
            if p1[i] == p2[j]:
                res.append[p1[i]]
                i+=1
                j+=1
            #si los elementos no son iguales, se aumenta el valor de la variable iteradora
            #del elemento mas pequeño    
            elif p1[i] < p2[j]:
                i+=1
            else:
                j+=1
        return res        

        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################



    def or_posting(self, p1:list, p2:list):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Calcula el OR de dos posting list de forma EFICIENTE

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos de p1 o p2

        """
        #IVAN
        #creamos lista resultado y variables para iterar las listas
        res = []
        i=0
        j=0
        #recorremos las listas hasta que se acabe una de las dos
        while i< len(p1) & j< len(p2):
            #si los elementos coinciden los añadimos al resultado y aumentamos el valor
            #de las variables para iterar
            if p1[i] == p2[j]:
                res.append[p1[i]]
                i+=1
                j+=1
            #si no coinciden los valores añadimos a la lista resultado el elemento mas pequeño
            elif p1[i] < p2[j]:
                res.append[p1[i]]
                i+=1
            else:
                res.append[p2[j]]
                j+=1
        #para comprobar que no se queda ningun elemento de la lista por añadir, se recorre
        #los elementos restantes y se añaden a la lista resultado        
        while i<len(p1):
            res.append[p1[i]]
            i+=1
        while j<len(p2):
            res.append[p2[j]]
            j+=1            
        return res       
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################


    def minus_posting(self, p1, p2):
        """
        OPCIONAL PARA TODAS LAS VERSIONES

        Calcula el except de dos posting list de forma EFICIENTE.
        Esta funcion se incluye por si es util, no es necesario utilizarla.

        param:  "p1", "p2": posting lists sobre las que calcular


        return: posting list con los artid incluidos de p1 y no en p2

        """
        #IVAN   
        i = 0
        j = 0
        res = []
        while i < len(p1) & j < len(p2):
            if p1[i]==p2[j]:
                i+=1
                j+=1
            elif p1[i]<p2[j]:
                res.append(p1[i])
                i+=1
            else:
                j+=1
        while i<len(p1):
            res.append(p1[i])
            i+=1
        return res                    
    
        ########################################################
        ## COMPLETAR PARA TODAS LAS VERSIONES SI ES NECESARIO ##
        ########################################################





    #####################################
    ###                               ###
    ### PARTE 2.2: MOSTRAR RESULTADOS ###
    ###                               ###
    #####################################

    def solve_and_count(self, ql:List[str], verbose:bool=True) -> List:
        results = []
        for query in ql:
            if len(query) > 0 and query[0] != '#':
                r = self.solve_query(query)
                results.append(len(r))
                if verbose:
                    print(f'{query}\t{len(r)}')
            else:
                results.append(0)
                if verbose:
                    print(query)
        return results


    def solve_and_test(self, ql:List[str]) -> bool:
        errors = False
        for line in ql:
            if len(line) > 0 and line[0] != '#':
                query, ref = line.split('\t')
                reference = int(ref)
                result = len(self.solve_query(query))
                if reference == result:
                    print(f'{query}\t{result}')
                else:
                    print(f'>>>>{query}\t{reference} != {result}<<<<')
                    errors = True                    
            else:
                print(query)
        return not errors


    def solve_and_show(self, query:str):
        """
        NECESARIO PARA TODAS LAS VERSIONES

        Resuelve una consulta y la muestra junto al numero de resultados 

        param:  "query": query que se debe resolver.

        return: el numero de artículo recuperadas, para la opcion -T

        """
        #IVAN

        print("========================================")
        q = self.solve_query(query)
        res = len(q)
        for i in q:
            tit= self.articles[i]
            print(f"({i}): {tit[1]} -> {tit[0]}")
        print("========================================")
        print(f"Query:{query}\n Nº de articulos recuperados:{res}")
        

        ################
        ## COMPLETAR  ##
        ################






        

