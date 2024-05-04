import SAR_Crawler_lib
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

texto = """
== Sección 1 ==
Contenido de la sección 1.
-- Subsección 1.1 --
Contenido de la subsección 1.1.
-- Subsección 1.2 --
Contenido de la subsección 1.2.

== Sección 2 ==
Contenido de la sección 2.
-- Subsección 2.1 --
Contenido de la subsección 2.1.
"""
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
        #creamos el diccionario a devolver
        document = {}

        #comprobamos si algun elemento en el documento coincide con el patrón del titulo
        match = self.title_sum_re.match(text).groupdict()
        #en caso negativo se devuelve None
        if not match:
            return None
        #en cualquier otro caso se asigna cada elemento a su respectiva vaiable y se añaden al diccionario
        title = match['title']
        
        summ =  match['summary']

        document={
            "url": url,
            "title": title,
            "summary":summ,
            "sections":[]
        }
        #Miramos el resto del documento
        x = match['rest']

        #Si no tiene secciones se retorna el diccionario actual
        if not match:
            return document
        #Si el documento tiene secciones, se analizaran.
        else:
            all = self.sections_re.findall(x)
            for i in all:
                match = self.section_re.match(i).groupdict()
                name = match['name']
                text = match['text']
                rest = match['rest']
            if document["sections"][i] not in document["sections"]:
                document["sections"][i]={
                    "name" : name,
                    "text" : text,
                    "subsections" : []
                }
                all1 = self.subsections_re.findall(rest)
                for j in all1:
                    match = self.subsection_re.match(j).groupdict()
                    name = match['name']
                    text = match['text']
                    if document["sections"][i][j] not in document["sections"][i]:
                        document["sections"][i][j]={
                            "name":name,
                            "text":text
                        }

                
        # COMPLETAR

        return document

url = "https://es.wikipedia.org/wiki/Videojuego."


parse_wikipedia_textual_content(texto, url) 