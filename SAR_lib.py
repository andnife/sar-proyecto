import json
from nltk.stem.snowball import SnowballStemmer
import os
import re
import sys
import math
from pathlib import Path
from typing import Optional, List, Union, Dict
import pickle
import distancias
import spellsuggester
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
        ('all', True), ('title', True), ('summary', True), ('section-name', True), ('url', False),
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
        self.index = {
            'all': {},
            'title': {},
            'summary': {},
            'section-name': {}
        } # hash para el indice invertido de terminos --> clave: termino, valor: posting list
        self.title = {}
        self.sectionname = {}
        self.summary = {}
        self.sindex = {
            'all': {},
            'title': {},
            'summary': {},
            'section-name': {}
        } # hash para el indice invertido de stems --> clave: stem, valor: lista con los terminos que tienen ese stem
        self.ptindex = {
            'all': {},
            'title': {},
            'summary': {},
            'section-name': {},
            'url': {}
        } # hash para el indice permuterm.
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
        self.use_spelling = False
        self.speller = None


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
        
        if self.stemming:
            self.set_stemming(True)
        
        if self.use_stemming:
            self.make_stemming
        
        if self.permuterm:
            self.make_permuterm
        
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

        for line in open(filename, encoding='utf-8', errors='replace'):
            j = self.parse_article(line.strip())
            if self.already_in_index(j):
                continue
            artId = len(self.articles) + 1
            self.articles[artId] = (j['url'], j['title'], j['all'])
            
            content = j['all']
            tokens = self.tokenize(content)
            
            for token in tokens:
                term = token.lower()
                if term not in self.index['all']:
                    self.index['all'][term] = []
                if artId not in self.index['all'][term]:
                    self.index['all'][term].append(artId)
                if self.positional: # ADE
                    if term not in self.posindex:
                        self.posindex[term] = []
                    if artId not in self.posindex[term]:
                        positions = []
                        for i in re.finditer(rf'\b[{term}]\b', content):
                            positions.append(i.start())
                        self.posindex[term] = {artId: positions}
            
            if self.stemming:
                self.make_stemming()
            if self.permuterm:
                self.make_permuterm()

            self.urls.add(j['url']) #ALV
            if self.multifield:
                title = j['title']
                titletokens = self.tokenize(title)
                for token in titletokens: 
                        term = token.lower()
                        if term not in self.title:
                            self.index['title'][term] = []
                        if artId not in self.index['title'][term]:
                            self.index['title'][term].append(artId)
                summary = j['summary']
                summarytokens = self.tokenize(summary)
                for token in summarytokens: 
                        term = token.lower()
                        if term not in self.summary:
                            self.index['summary'][term] = []
                        if artId not in self.index['summary'][term]:
                            self.index['summary'][term].append(artId)            
                section = j['section-name']
                sectiontokens = self.tokenize(section)
                for token in sectiontokens: 
                        term = token.lower()
                        if term not in self.sectionname:
                            self.index['section-name'][term] = []
                        if artId not in self.index['section-name'][term]:
                            self.index['section-name'][term].append(artId)
            
        # Invert index convertion
        terms = sorted(self.index['all'].keys())
        invertedIndex = {}
        for t in terms:
            invertedIndex[t] = self.index['all'][t]
            
        self.index['all'] = invertedIndex
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

        Crea el indice de stemming (self.sindex['all']) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE STEMMING.

        "self.stemmer.stem(token) devuelve el stem del token"


        """
        #BLANCA

        terms = list(self.index['all'].keys())
        for term in terms:
            stemmed = self.stemmer.stem(term)
            if stemmed not in self.sindex['all']:
                self.sindex['all'][stemmed] = [term]
            else:
                self.sindex['all'][stemmed].append(term)
        
        if self.multifield:
            terms = list(self.index['title'].keys())
            for term in terms:
                stemmed = self.stemmer.stem(term)
                if stemmed not in self.sindex['title']:
                    self.sindex['title'][stemmed] = [term]
                else:
                    self.sindex['title'][stemmed].append(term)
                    
            terms = list(self.index['summary'].keys())
            for term in terms:
                stemmed = self.stemmer.stem(term)
                if stemmed not in self.sindex['summary']:
                    self.sindex['summary'][stemmed] = [term]
                else:
                    self.sindex['summary'][stemmed].append(term)
                    
            terms = list(self.index['section-name'].keys())
            for term in terms:
                stemmed = self.stemmer.stem(term)
                if stemmed not in self.sindex['section-name']:
                    self.sindex['section-name'][stemmed] = [term]
                else:
                    self.sindex['section-name'][stemmed].append(term)


    
    def make_permuterm(self):
        """

        Crea el indice permuterm (self.ptindex['all']) para los terminos de todos los indices.

        NECESARIO PARA LA AMPLIACION DE PERMUTERM

        """
        # ADE

        #####################################################
        ## COMPLETAR PARA FUNCIONALIDAD EXTRA DE PERMUTERM ##
        #####################################################
        
        # Itero cada termino de los indexados
        for term in list(self.index['all'].keys()):
            # Añado el comodin al final y guardo la modificacion a la posting list del permuterm
            termmod = term + '*'
            self.ptindex['all'][termmod] = self.index['all'][term]
            
            # Voy a ir rotando el comodin y almacenando en la posting list del permuterm
            for i in range(len(termmod)):
                termmod = termmod[i:] + termmod[:i]
                self.ptindex['all'][termmod] = self.index['all'][term]
        
        if self.multifield:
            # Itero cada termino de los indexados
            for term in list(self.index['title'].keys()):
                # Añado el comodin al final y guardo la modificacion a la posting list del permuterm
                termmod = term + '*'
                self.ptindex['title'][termmod] = self.index['title'][term]
                
                # Voy a ir rotando el comodin y almacenando en la posting list del permuterm
                for i in range(len(termmod)):
                    termmod = termmod[i:] + termmod[:i]
                    self.ptindex['title'][termmod] = self.index['title'][term]
            
            # Itero cada termino de los indexados
            for term in list(self.index['summary'].keys()):
                # Añado el comodin al final y guardo la modificacion a la posting list del permuterm
                termmod = term + '*'
                self.ptindex['summary'][termmod] = self.index['summary'][term]
                
                # Voy a ir rotando el comodin y almacenando en la posting list del permuterm
                for i in range(len(termmod)):
                    termmod = termmod[i:] + termmod[:i]
                    self.ptindex['summary'][termmod] = self.index['summary'][term]
                    
            # Itero cada termino de los indexados
            for term in list(self.index['section-name'].keys()):
                # Añado el comodin al final y guardo la modificacion a la posting list del permuterm
                termmod = term + '*'
                self.ptindex['section-name'][termmod] = self.index['section-name'][term]
                
                # Voy a ir rotando el comodin y almacenando en la posting list del permuterm
                for i in range(len(termmod)):
                    termmod = termmod[i:] + termmod[:i]
                    self.ptindex['section-name'][termmod] = self.index['section-name'][term]
                    


    def show_stats(self):
        """
        NECESARIO PARA TODAS LAS VERSIONES
        
        Muestra estadisticas de los indices
        
        """
        print('========================================')

        # Indexed files
        print(f'Number of indexed files: {len(self.docs)}')
        print('----------------------------------------')

        #Indexed articles
        print(f'Number of indexed articles: {len(self.articles)}')
        print('----------------------------------------')

        #Tokens

        print(f'TOKENS:')
        if not self.multifield:
                print(f'\t# of tokens in \'all\': {len(self.index["all"])}')
        else:
                print(f'\t# of tokens in \'all\': {len(self.index["all"])}')
                print(f'\t# of tokens in \'title\': {len(self.index["title"])}')
                print(f'\t# of tokens in \'summary\': {len(self.index["summary"])}')
                print(f'\t# of tokens in \'section-name\': {len(self.index["section-name"])}')
                print(f'\t# of tokens in \'url\': {len(self.urls)}')
        print('----------------------------------------')

        #Permuterm
        if (self.permuterm):
            print(f'PERMUTERM:')
            if not self.multifield:
                    print(f'\t# of tokens in \'all\': {len(self.ptindex["all"])}')
            else:
                    print(f'\t# of tokens in \'all\': {len(self.ptindex["all"])}')
                    print(f'\t# of tokens in \'title\': {len(self.ptindex["title"])}')
                    print(f'\t# of tokens in \'summary\': {len(self.ptindex["summary"])}')
                    print(f'\t# of tokens in \'section-name\': {len(self.ptindex["section-name"])}')
                    print(f'\t# of tokens in \'url\': {len(self.urls)}')
            print('----------------------------------------')

        #Stemming
        if (self.stemming):
            print(f'STEMS:')
            if not self.multifield:
                    print(f'\t# of tokens in \'all\': {len(self.sindex["all"])}')
            else:
                    print(f'\t# of tokens in \'all\': {len(self.sindex["all"])}')
                    print(f'\t# of tokens in \'title\': {len(self.sindex["title"])}')
                    print(f'\t# of tokens in \'summary\': {len(self.sindex["summary"])}')
                    print(f'\t# of tokens in \'section-name\': {len(self.sindex["section-name"])}')
                    print(f'\t# of tokens in \'url\': {len(self.urls)}')
            print('----------------------------------------')

        #Positional
        if (self.positional):
            print("Positional queries are allowed.")
        else:
            print("Positional queries are NOT allowed.")
        print('========================================')



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


    def solve_query(self, query: str, prev: Dict = {}) -> List:
        """
        NECESARIO PARA TODAS LAS VERSIONES
        Resuelve una query.
        Debe realizar el parsing de consulta que sera mas o menos complicado en funcion de la ampliacion que se implementen

        param:  "query": cadena con la query
                "prev": incluido por si se quiere hacer una version recursiva. No es necesario utilizarlo.

        return: posting list con el resultado de la query
        """
        query = self._normalize_query(query)
        terminos = query.split()
        if not terminos:
            return None

        result = self._parse_expression(terminos)
        return result

    def _normalize_query(self, query: str) -> str:
        """Separa los paréntesis de los demás elementos en la consulta."""
        query = re.sub(r'(\()(\S)', r'\1 \2', query)
        query = re.sub(r'(\S)(\))', r'\1 \2', query)
        query = re.sub(r'(\))(\S)', r'\1 \2', query)
        query = re.sub(r'(\S)(\()', r'\1 \2', query)
        return query

    def _parse_expression(self, terminos: List[str]) -> List:
        """Parses and evaluates the given list of terms."""
        if not terminos:
            return []

        aux = terminos.pop(0)
        if aux == '(':
            aux = self._parse_subquery(terminos)
        elif aux.upper() == 'NOT':
            aux = self.reverse_posting(self._parse_term(terminos))
        else:
            aux = self.get_posting(aux)

        while terminos:
            op = terminos.pop(0)
            if op == ')':
                break
            t = self._parse_term(terminos)
            if op.upper() == 'AND':
                aux = self.and_posting(aux, t)
            elif op.upper() == 'OR':
                aux = self.or_posting(aux, t)

        return aux

    def _parse_subquery(self, terminos: List[str]) -> List:
        """Parses a subquery enclosed in parentheses."""
        subquery = []
        balance = 1
        while terminos and balance > 0:
            token = terminos.pop(0)
            if token == '(':
                balance += 1
            elif token == ')':
                balance -= 1
            if balance > 0:
                subquery.append(token)
        return self.solve_query(' '.join(subquery))

    def _parse_term(self, terminos: List[str]) -> List:
        """Parses and evaluates a term which can be a simple term, NOT term, or a subquery."""
        term = terminos.pop(0)
        if term == '(':
            return self._parse_subquery(terminos)
        elif term.upper() == 'NOT':
            return self.reverse_posting(self._parse_term(terminos))
        else:
            return self.get_posting(term)


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
        #BLANCA

        #For stemming argument
        if self.use_stemming:
            return self.get_stemming(term)
        #IVAN
        if self.use_spelling and term not in self.speller.vocabulary:
            suggestion = self.speller.suggest(term=term)
            if suggestion != []:
                res = []
                for t in suggestion:
                    if t in self.speller.vocabulary:
                        res = self.or_posting(res, self.index[t])  
                return res
            return suggestion
        ########################################
        ## COMPLETAR PARA TODAS LAS VERSIONES ##
        ########################################
        x = self.index['all']

        if term in x:
            return self.index['all'][term]
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
        print(dict)
        exit()
        
        return dict


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

        if stem not in self.sindex['all']:
            return res
        terms = list(self.sindex['all'][stem])

        for t in range(len(terms)):
            terms[t] = self.index['all'][terms[t]]

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
        for term in list(self.ptindex['all'].keys()):
            # Si el termino obtenido de la lista de permuterm termina por la parte delantera
            # al comodin, añado la posting list
            if term.endswith(twoterms[0]):
                secondtermlist.append(self.ptindex['all'][term])
                
            # Si el termino obtenido de la lista de permuterm empieza por la parte trasera
            # al comodin, añado la posting list
            if term.startswith(twoterms[1]):
                firsttermlist.append(self.ptindex['all'][term])
        
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
        # Creo una lista con todos los indices de documentos
        alldocs = list(range(1,len(self.articles)+1))

        # Creo una lista vacia de los indices a devolver
        resdocs = []
        
        # Guardo una lista con los documentos a eliminar
        removedocs = p

        # Itero cada documento de los originales
        for doc in alldocs:
            if doc not in removedocs: # Si el documento no esta dentro de los documentos a eliminar lo añado
                resdocs.append(doc)

        return resdocs
        
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
        while i< len(p1) and j< len(p2):
            #si los elementos coinciden los añadimos al resultado y aumentamos el valor
            #de las variables para iterar
            if p1[i] == p2[j]:
                res.append(p1[i])
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
        while i< len(p1) and j< len(p2):
            #si los elementos coinciden los añadimos al resultado y aumentamos el valor
            #de las variables para iterar
            if p1[i] == p2[j]:
                res.append(p1[i])
                i+=1
                j+=1
            #si no coinciden los valores añadimos a la lista resultado el elemento mas pequeño
            elif p1[i] < p2[j]:
                res.append(p1[i])
                i+=1
            else:
                res.append(p2[j])
                j+=1
        #para comprobar que no se queda ningun elemento de la lista por añadir, se recorre
        #los elementos restantes y se añaden a la lista resultado        
        while i<len(p1):
            res.append(p1[i])
            i+=1
        while j<len(p2):
            res.append(p2[j])
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
    
    def snippets(self, text:str, query:str) -> List[str]:
        #IVAN
        #obtenemos todas la spalabras del texto en una lista y lo imso con las palabras de la query
        words = self.tokenize(text)

        #limpiamos los signos de la query
        quer = query.replace('(', '')
        quer = quer.replace(')', '')
        quer = self.tokenize(quer)
        
        #creamos la base del snippet
        snp = '"'
        #iteramos cada palabra de la query, si es un operador se ignora
        for word in quer:
            if word not in ['AND','OR','NOT','and','or','not']:
                w = words
                #si la palabra esta en el texto, se guarda la primera posicion
                if word in w:
                    pos = w.index(word)
                    #si la palabra estuviera repetida, se busca la siguiente ocurrencia
                    if word in snp:
        
                        try:
                            n_pos = w[pos+1:].index(word)
                            n_pos += pos+1
                        except ValueError:
                            n_pos = -1
                        #en caso de que no hubieran mas ocurrencias se devuelve el snipet
                        if n_pos == -1:
                            return snp
                        else: 
                            #si el termino no esta repetido en el snippet
                            #se cogen los 4 primeros elementos anteriores y los cinco siguientes    
                            min_p = n_pos - 4
                            #comprobamos que no se haya salido fuera de la lista, y en caso afirmativo el minimo es 0
                            if min_p < 0:
                                min_p = 0
                            max_p = n_pos+5
                            #lo mismo en el caso contrario
                            if max_p > len(words)-1:
                                max_p = len(words)-1     
                            s_aux = ''
                            #si no estamos al principio del documento monemos puntos suspensivos
                            #y añadimos el snippet creado a la variable resultado
                            if min_p >0:
                                s_aux+= '...' 
                                s_aux += " ".join(w[min_p:max_p+1])  
                    else:
                        #la misma ejecucion pero cambia n_pos -> pos         
                        min_p = pos - 4
                        if min_p < 0:
                            min_p = 0
                        max_p = pos+5
                        if max_p > len(words)-1:
                            max_p = len(words)-1     
                        s_aux = ''
                        if min_p >0:
                            s_aux+= '...'
                        s_aux += " ".join(w[min_p:max_p+1])    
                    
                    #si no estamos al final del documento monemos puntos suspensivos
                    if max_p < len(w) - 1:
                        s_aux += '...'    
                    snp += s_aux  
                      
        return snp + '"'



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
        if self.show_snippet and self.show_all:
                q = self.solve_query(query)
                print(q)
                res = len(q)
                
                for i in q:
                    tit = self.articles[i]
                    txt = self.articles[i][2]
                    snp = self.snippets(txt,query)
                    print(f"({i}): {tit[0]}\n{tit[1]} \n\n{snp}\n")
                    print(snp)     

        elif self.show_snippet and not self.show_all:
                q = self.solve_query(query)
                print(q)
                res = len(q)
                
                for i in q[:9]:
                    tit = self.articles[i]
                    txt = self.articles[i][2]
                    snp = self.snippets(txt,query)
                    print(f"({i}): {tit[0]}\n{tit[1]} \n\n{snp}\n")
    

        elif self.show_all:
            q = self.solve_query(query)
            print(q)
            res = len(q)

            for i in q:
                tit = self.articles[i]
                print(f"({i}): {tit[0]}\n{tit[1]} \n\n{snp}\n")

        else :
            q = self.solve_query(query)
            print(q)
            res = len(q)

            for i in q[:9]:
                tit = self.articles[i]
                print(f"({i}): {tit[0]}\n{tit[1]} \n\n{snp}\n")
        print("========================================")
        print(f"Query:{query}\n Nº de articulos recuperados:{res}\n")    
        

        ################
        ## COMPLETAR  ##
        ################


    def set_spelling(self, use_spelling:bool, distance:str=None, threshold:int=None):
        """
        self.use_spelling a True activa la corrección ortográfica
        EN LAS PALABRAS NO ENCONTRADAS, en caso contrario NO utilizará
        corrección ortográfica

        input: "use_spell" booleano, determina el uso del corrector.
                "distance" cadena, nombre de la función de distancia.
                "threshold" entero, umbral del corrector
        """
        #IVAN
        self.use_spelling = use_spelling
        if use_spelling:
            vocabulary = list(self.index.keys())
            self.speller = spellsuggester.SpellSuggester(dist_functions=distancias.opcionesSpell, vocab = vocabulary, default_distance = distance, default_threshold=threshold)
        else:
            self.speller = None




        

