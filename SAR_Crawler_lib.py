#! -*- encoding: utf8 -*-
import heapq as hq

from typing import Tuple, List, Optional, Dict, Union

import requests
import bs4
import re
from urllib.parse import urljoin
import json
import math
import os

class SAR_Wiki_Crawler:

    def __init__(self):
        # Expresión regular para detectar si es un enlace de la Wikipedia
        self.wiki_re = re.compile(r"(http(s)?:\/\/(es)\.wikipedia\.org)?\/wiki\/[\w\/_\(\)\%]+")
        # Expresión regular para limpiar anclas de editar
        self.edit_re = re.compile(r"\[(editar)\]")
        # Formato para cada nivel de sección
        self.section_format = {
            "h1": "##{}##",
            "h2": "=={}==",
            "h3": "--{}--"
        }

        # Expresiones regulares útiles para el parseo del documento
        self.title_sum_re = re.compile(r"##(?P<title>.+)##\n(?P<summary>((?!==.+==).+|\n)+)(?P<rest>(.+|\n)*)")
        self.sections_re = re.compile(r"==.+==\n")
        self.section_re = re.compile(r"==(?P<name>.+)==\n(?P<text>((?!--.+--).+|\n)*)(?P<rest>(.+|\n)*)")
        self.subsections_re = re.compile(r"--.+--\n")
        self.subsection_re = re.compile(r"--(?P<name>.+)--\n(?P<text>(.+|\n)*)")


    def is_valid_url(self, url: str) -> bool:
        """Verifica si es una dirección válida para indexar

        Args:
            url (str): Dirección a verificar

        Returns:
            bool: True si es valida, en caso contrario False
        """
        return self.wiki_re.fullmatch(url) is not None


    def get_wikipedia_entry_content(self, url: str) -> Optional[Tuple[str, List[str]]]:
        """Devuelve el texto en crudo y los enlaces de un artículo de la wikipedia

        Args:
            url (str): Enlace a un artículo de la Wikipedia

        Returns:
            Optional[Tuple[str, List[str]]]: Si es un enlace correcto a un artículo
                de la Wikipedia en inglés o castellano, devolverá el texto y los
                enlaces que contiene la página.

        Raises:
            ValueError: En caso de que no sea un enlace a un artículo de la Wikipedia
                en inglés o español
        """
        if not self.is_valid_url(url):
            #raise ValueError((
                f"El enlace '{url}' no es un artículo de la Wikipedia en español"
            #))
        else:
            try:
                req = requests.get(url)
            except Exception as ex:
                print(f"ERROR: - {url} - {ex}")
                return None


            # Solo devolvemos el resultado si la petición ha sido correcta
            if req.status_code == 200:
                soup = bs4.BeautifulSoup(req.text, "lxml")
                urls = set()

                for ele in soup.select((
                    'div#catlinks, div.printfooter, div.mw-authority-control'
                )):
                    ele.decompose()

                # Recogemos todos los enlaces del contenido del artículo
                for a in soup.select("div#bodyContent a", href=True):
                    href = a.get("href")
                    if href is not None:
                        urls.add(href)

                # Contenido del artículo
                content = soup.select((
                    "h1.firstHeading,"
                    "div#mw-content-text h2,"
                    "div#mw-content-text h3,"
                    "div#mw-content-text h4,"
                    "div#mw-content-text p,"
                    "div#mw-content-text ul,"
                    "div#mw-content-text li,"
                    "div#mw-content-text span"
                ))

                dedup_content = []
                seen = set()

                for element in content:
                    if element in seen:
                        continue

                    dedup_content.append(element)

                    # Añadimos a vistos, tanto el elemento como sus descendientes
                    for desc in element.descendants:
                        seen.add(desc)

                    seen.add(element)

                text = "\n".join(
                    self.section_format.get(element.name, "{}").format(element.text)
                    for element in dedup_content
                )

                # Eliminamos el texto de las anclas de editar
                text = self.edit_re.sub('', text)

                return text, sorted(list(urls))

        return None


    def parse_wikipedia_textual_content(self, text: str, url: str) -> Optional[Dict[str, Union[str,List]]]:
        """Devuelve una estructura tipo artículo a partir del text en crudo

        Args:
            text (str): Texto en crudo del artículo de la Wikipedia
            url (str): url del artículo, para añadirlo como un campo

        Returns:

            Optional[Dict[str, Union[str,List[Dict[str,Union[str,List[str,str]]]]]]]:
            #el diccionario tiene claves del tipo str, y sus contenidos pueden ser del tipo str o lista de diccionarios

            devuelve un diccionario con las claves 'url', 'title', 'summary', 'sections':
                Los valores asociados a 'url', 'title' y 'summary' son cadenas,
                el valor asociado a 'sections' es una lista de posibles secciones.
                    Cada sección es un diccionario con 'name', 'text' y 'subsections',
                        los valores asociados a 'name' y 'text' son cadenas y,
                        el valor asociado a 'subsections' es una lista de posibles subsecciones
                        en forma de diccionario con 'name' y 'text'.

            en caso de no encontrar título o resúmen del artículo, devolverá None

        self.title_sum_re = re.compile(r"##(?P<title>.+)##\n(?P<summary>((?!==.+==).+|\n)+)(?P<rest>(.+|\n)*)")
        self.sections_re = re.compile(r"==.+==\n")
        self.section_re = re.compile(r"==(?P<name>.+)==\n(?P<text>((?!--.+--).+|\n)*)(?P<rest>(.+|\n)*)")
        self.subsections_re = re.compile(r"--.+--\n")
        self.subsection_re = re.compile(r"--(?P<name>.+)--\n(?P<text>(.+|\n)*)")
        """
        def clean_text(txt):
            return '\n'.join(l for l in txt.split('\n') if len(l) > 0)
        
        # COMPLETAR
        # IVAN
        #creamos el diccionario a devolver
        document = {}
        if text is None:
            return None
        
        match = None
        #comprobamos si algun elemento en el documento coincide con el patrón del titulo
        try:
            match = self.title_sum_re.match(text).groupdict()
        except:
            return None
        
        #en caso negativo se devuelve None
        if not match:
            return None
        #en cualquier otro caso se asigna cada elemento a su respectiva vaiable y se añaden al diccionario
        title = match['title']
        
        summ =  match['summary']

        document = {
            "url": url,
            "title": title,
            "summary": summ,
            "sections": []
        }
        # Miramos el resto del documento
        x = match['rest']
        # Si no tiene secciones se retorna el diccionario actual
        if not x:
            return document
        # Si el documento tiene secciones, se analizaran.
        else:
            sectionsname = self.sections_re.findall(x)
            sectionscontent = self.sections_re.split(x)
            sectionscontent.pop(0) # Elimina el primer elemento que esta vacío

            for i in range(len(sectionsname)):
                s = {
                    "name": sectionsname[i].strip()[2:-2],
                    "text": "",
                    "subsections": []
                }
                subsectionsname = self.subsections_re.findall(sectionscontent[i])
                if len(subsectionsname) == 0:
                    # No hay subsecciones
                    s['text'] = sectionscontent[i]
                else:
                    subsectionscontent = self.subsections_re.split(sectionscontent[i])
                    s['text'] = subsectionscontent.pop(0) # Guarda el primer elemento (el texto antes de las subsecciones)
                    for j in range(len(subsectionsname)):
                        ss = {
                            "name": subsectionsname[j].strip()[2:-2],
                            "text": subsectionscontent[j]
                        }
                        s["subsections"].append(ss)
                document['sections'].append(s)

        # FIX SUBSECTIONS ADE

        # FIN IVAN

        return document


    def save_documents(self,
        documents: List[dict], base_filename: str,
        num_file: Optional[int] = None, total_files: Optional[int] = None
    ):
        """Guarda una lista de documentos (text, url) en un fichero tipo json lines
        (.json). El nombre del fichero se autogenera en base al base_filename,
        el num_file y total_files. Si num_file o total_files es None, entonces el
        fichero de salida es el base_filename.

        Args:
            documents (List[dict]): Lista de documentos.
            base_filename (str): Nombre base del fichero de guardado.
            num_file (Optional[int], optional):
                Posición numérica del fichero a escribir. (None por defecto)
            total_files (Optional[int], optional):
                Cantidad de ficheros que se espera escribir. (None por defecto)
        """
        assert base_filename.endswith(".json")

        if num_file is not None and total_files is not None:
            # Separamos el nombre del fichero y la extensión
            base, ext = os.path.splitext(base_filename)
            # Padding que vamos a tener en los números
            padding = len(str(total_files))

            out_filename = f"{base}_{num_file:0{padding}d}_{total_files}{ext}"

        else:
            out_filename = base_filename

        with open(out_filename, "w", encoding="utf-8", newline="\n") as ofile:
            for doc in documents:
                print(json.dumps(doc, ensure_ascii=True), file=ofile)


    def start_crawling(self, 
                    initial_urls: List[str], document_limit: int,
                    base_filename: str, batch_size: Optional[int], max_depth_level: int,
                    ):        
         

        """Comienza la captura de entradas de la Wikipedia a partir de una lista de urls válidas, 
            termina cuando no hay urls en la cola o llega al máximo de documentos a capturar.
        
        Args:
            initial_urls: Direcciones a artículos de la Wikipedia
            document_limit (int): Máximo número de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.
            max_depth_level (int): Profundidad máxima de captura.
        """
        base_filename = base_filename.rsplit('.')[0] # Elimno el .json ya que lo añado despues
        # URLs válidas, ya visitadas (se hayan procesado, o no, correctamente)
        visited = set()
        # URLs en cola
        to_process = set(initial_urls)
        # Direcciones a visitar
        queue = [(0, "", url) for url in to_process]
        hq.heapify(queue)
        # Buffer de documentos capturados
        documents: List[dict] = []
        # Contador del número de documentos capturados
        total_documents_captured = 0
        # Contador del número de ficheros escritos
        files_count = 0

        # En caso de que no utilicemos bach_size, asignamos None a total_files
        # así el guardado no modificará el nombre del fichero base
        if batch_size is None:
            total_files = None
        else:
            # Suponemos que vamos a poder alcanzar el límite para la nomenclatura
            # de guardado
            total_files = math.ceil(document_limit / batch_size)

        # COMPLETAR
        ### ADE
        batch_text = ''
        batch_count = 0
        finished = False

        if total_documents_captured >= document_limit:
            finished = True
        if total_files and total_files >= document_limit:
            finished = True

        # Itero mientras la cola no este vacia
        while len(queue) > 0 and not finished:
            # Obtengo el primer elemento de la cola y lo elimino
            q = queue.pop(0)
            
            # De dicho elemento obtengo la URL a visitar y la profundidad
            depth = q[0]
            url = f'{q[1]}{q[2]}'

            '''
            Las URL de Wikipedia apuntan de manera local, es decir, al vincular otra pagina de wikipedia, ahorran poner la direccion del servidor
            (https://es.wikipedia.org) y apuntan directamente al contenedor correspondiente (p.e /wiki/Python).
            De esta forma tratamos este caso antes de llamar a la funcion que obtiene la información de la página.
            Cualquier página que no apunte a Wikipedia no se vera afectada porque SI empezara con la direccion al servidor.
            '''
            
            # Obtengo el contenido plano en texto y las URL de la URL a visitar
            wikientrycontent = self.get_wikipedia_entry_content(url)
            if wikientrycontent:
                text, list = wikientrycontent
                # Itero cada URL obtenida de la pagina
                for l in list:
                    # Si la URL es valida y la profundidad es menor que la profundidad maxima, añado los hijos a la cola
                    if self.is_valid_url(l) & (depth < max_depth_level) & (url not in visited):
                        queue.append((depth+1,url,l))
                hq.heapify(queue)

                # Añado la URL a la lista de URLs visitadas
                if url not in visited:
                    visited.add(url) # FIX append() -> add() [SET NO TIENE METODO APPEND]
                ### FIN ADE

                # ALVARO
                # Llamar a conversor texto -> JSON
                if not batch_size:
                    batch_text += json.dumps(self.parse_wikipedia_textual_content(text,url))
                    batch_text += '\n'
                else:
                    if batch_count < batch_size:
                        # Mientras el batch no este completo, añado una fila por cada artículo
                        batch_text += json.dumps(self.parse_wikipedia_textual_content(text,url))
                        batch_text += '\n'
                        batch_count += 1
                    else:
                        # Hago batches en funcion a formato de nombres dado y batch actual
                        files_count += 1
                        with open(f'{base_filename}_{files_count}_{document_limit}.json','w',encoding='utf-8') as batch:
                            batch.write(batch_text)
                        batch_text = json.dumps(self.parse_wikipedia_textual_content(text,url))
                        batch_text += '\n'
                        batch_count = 1
                        print(f'Escrito un batch ({base_filename}_{files_count}_{document_limit}.json)')
                total_documents_captured += 1
            if total_documents_captured >= document_limit:
                finished = True
            if total_files and total_files >= document_limit:
                finished = True
            print(f'Remaining: {len(queue)} - URL: {url}\nDepth: {depth} - Files count: {files_count} - Total documents captured: {total_documents_captured}\nBatch size: {batch_size} - Batch count: {batch_count}\n')

        if not batch_size:
            with open(f'{base_filename}.json','w',encoding='utf-8') as batch:
                batch.write(batch_text)
            print(f'Escrito un batch {base_filename}.json')
        else:
            # Cuando llegues al cupo del batch o no queden mas docs por ver, creas el file y lo escribes
            if batch_count != 0:
                # Hago batch con el texto lo restante
                files_count += 1
                with open(f'{base_filename}_{files_count}.json','w',encoding='utf-8') as batch:
                    batch.write(batch_text)
                print(f'Escrito un batch ({base_filename}_{files_count}.json)')
        # FIN ALVARO
        # FIX ADE


    def wikipedia_crawling_from_url(self,
        initial_url: str, document_limit: int, base_filename: str,
        batch_size: Optional[int], max_depth_level: int
    ):
        """Captura un conjunto de entradas de la Wikipedia, hasta terminar
        o llegar al máximo de documentos a capturar.
        
        Args:
            initial_url (str): Dirección a un artículo de la Wikipedia
            document_limit (int): Máximo número de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.
            max_depth_level (int): Profundidad máxima de captura.
        """
        if not self.is_valid_url(initial_url) and not initial_url.startswith("/wiki/"):
            raise ValueError(
                "Es necesario partir de un artículo de la Wikipedia en español"
            )

        self.start_crawling(initial_urls=[initial_url], document_limit=document_limit, base_filename=base_filename,
                            batch_size=batch_size, max_depth_level=max_depth_level)



    def wikipedia_crawling_from_url_list(self,
        urls_filename: str, document_limit: int, base_filename: str,
        batch_size: Optional[int]
    ):
        """A partir de un fichero de direcciones, captura todas aquellas que sean
        artículos de la Wikipedia válidos

        Args:
            urls_filename (str): Lista de direcciones
            document_limit (int): Límite máximo de documentos a capturar
            base_filename (str): Nombre base del fichero de guardado.
            batch_size (Optional[int]): Cada cuantos documentos se guardan en
                fichero. Si se asigna None, se guardará al finalizar la captura.

        """

        urls = []
        with open(urls_filename, "r", encoding="utf-8") as ifile:
            for url in ifile:
                url = url.strip()

                # Comprobamos si es una dirección a un artículo de la Wikipedia
                if self.is_valid_url(url):
                    if not url.startswith("http"):
                        raise ValueError(
                            "El fichero debe contener URLs absolutas"
                        )

                    urls.append(url)

        urls = list(set(urls)) # eliminamos posibles duplicados

        self.start_crawling(initial_urls=urls, document_limit=document_limit, base_filename=base_filename,
                            batch_size=batch_size, max_depth_level=0)





if __name__ == "__main__":
    raise Exception(
        "Esto es una librería y no se puede usar como fichero ejecutable"
    )
