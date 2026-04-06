import os
import json
from jsonpath_ng import jsonpath, parse

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class DenseRetriever:
    """
    Implementa búsqueda densa usando embeddings.
    """
    def __init__(self):
        # Cargar modelo de embeddings multilingüe
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

    def buscar(self, document_1, document_2) :
        # Generar y almacenar embeddings
        try:
            embeddings_1 = self.model.encode(document_1, show_progress_bar=False)
            embeddings_2 = self.model.encode(document_2, show_progress_bar=False)
            return cosine_similarity(embeddings_1, embeddings_2)[0][0]

        except Exception as a:
            print("An exception ocurred while processing "+str(document_1)+"\n and \n"+str(document_2)+"\n", a)
        return 0.0

'''
    IO functions
'''

def list_files(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def read_json(file_dir):
    with open(file_dir, 'r', encoding='utf-8') as f:
        return json.load(f)

'''
    Util functions
'''


def read_subjects(files):
    subjects = {}
    for file in files:
        subject_code = file.split("-")[0]
        if subject_code in subjects.keys():
            subjects[subject_code] = subjects[subject_code] + 1
        else:
            subjects[subject_code] = 1
    return subjects


'''
    Similarity functions
'''

def jsonpath_filter(json_data, jsonpath):
    jsonpath_expr = parse(jsonpath)
    return [match.value for match in jsonpath_expr.find(json_data)]

def jsonpath_similarity(filter, json_1, json_2):
    global dense_retriever
    filtered_json_1 = [ str(value) for value in jsonpath_filter(json_1, filter) ]
    filtered_json_2 = [ str(value) for value in jsonpath_filter(json_2, filter) ]

    return { "equals" :  (filtered_json_1 == filtered_json_2), "semantic_cosine" :  dense_retriever.buscar(filtered_json_1, filtered_json_2)}

def show_analysis(filter, scores):
    is_equals = scores["equals"]
    cosine = scores["semantic_cosine"]
    if not is_equals and cosine < 0.90:
        print("\t- ", filter, " : ", cosine)
        return True
    return False


if __name__ == '__main__':
    # Setup
    debug = False
    directory = "./guides_data/"
    files = list_files(directory)
    suffix_file_1 = "-61CD-2025-26.json"
    suffix_file_2 = "-61CD-2024-25.json"
    dense_retriever = DenseRetriever()
    # Compare 2 by 2 guides
    subjects = read_subjects(files)
    [ print("check subject with code: ", subject_code) for subject_code in subjects.keys() if subjects[subject_code] != 2]
    for subject_code, count  in subjects.items():
        if count < 2:
            continue
        guide_1 = read_json(directory + subject_code + suffix_file_1)
        guide_2 = read_json(directory + subject_code + suffix_file_2)
        dirty = False
        filters = ["$.['Asignaturas Previas Requeridas']",
                   "$.['Otros Requisitos']",
                   "$.['RD 1393 - Competencias / RD 822 - Resultados de Aprendizaje']",
                   "$.['RD 1393 - Resultados de Aprendizaje']",
                   "$.['Descripción de la Asignatura']",
                   "$.['Temario']",
                   "$.['resumen']",
                   "$.['cronograma']",
                   "$.['evaluacion']['actividades']",
                   "$.['evaluacion']['criterios_evaluacion']",
                   "$.['Otra información reseñable']",
                   "$.['recursos_didacticos']"
                   ]
        for filter in filters:
            try:
                scores = jsonpath_similarity(filter, guide_1, guide_2)
                if debug:
                    print(filter, " : ", scores)
                dirty = dirty or show_analysis(filter, scores)
            except Exception as a:
                print("error happened with ", filter, " : ", a)
        if dirty:
            print("Building similarity report for (", subject_code, ")   ",
                  guide_1["Datos descriptivos"]["Nombre de la Asignatura"])

            print("\t************", subject_code, " : ", guide_1["Datos descriptivos"]["Nombre de la Asignatura"], " must be reviewed: ", dirty)
        print("---------------------------------------")