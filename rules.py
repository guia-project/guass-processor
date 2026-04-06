import os
import json
from jsonpath_ng import jsonpath, parse

'''
    IO functions
'''

def list_files(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def read_json(file_dir):
    with open(file_dir, 'r', encoding='utf-8') as f:
        return json.load(f)

def jsonpath_filter(json_data, jsonpath):
    jsonpath_expr = parse(jsonpath)
    return [match.value for match in jsonpath_expr.find(json_data)]

'''
    Util functions
'''


def read_subjects(files):
    subjects = []
    for file in files:
        if file.endswith('.json'):
            subject = file.split("-")[0]
            if subject not in subjects:
                subjects.append(subject)
    return subjects

'''
    Rules
'''

# Rule 1: En el cronograma deben aparecer repetidas en la columna 1 o 2, según corresponda,
# las actividades de evaluación progresiva realizadas dentro del curso (las que se realizan de la semana 1 a la 15).
def rule_1(json_document):
    evaluation_activities = json_document['cronograma']
    for activity in evaluation_activities:
        #print(activity)
        continue

# Rule 2: La semana 11 del primer semestre y la 7 del segundo semestre no pueden tener clases ni pruebas de evaluación.

def __rule_2(index, evaluation_activities):
    empty_week = evaluation_activities[index]
    week_is_empty = 0 == len(empty_week['actividad_tipo_1']) + len(empty_week['actividad_tipo_2']) + len(
        empty_week['tele_ensenanza']) + len(empty_week['actividades_evaluacion'])
    if not week_is_empty:
        semester = "1S"
        if index == 7:
            semester = "2S"
        print("\tRule 2: No empty week ", index + 1, " which is mandatory for ", semester, " semestre.")


def rule_2(json_document):
    semesters = {"Primer semestre" : 10, "Tercer semestre" : 10, "Quinto semestre": 10, "Séptimo semestre": 10,
                 "Segundo semestre" : 6, "Cuarto semestre" : 6, "Sexto semestre": 6, "Octavo semestre": 6}
    evaluation_activities = json_document['cronograma']
    semester_key = json_document['Datos descriptivos']['Semestre/s de impartición']
    if "\n" in semester_key:
        first_key = semester_key.split("\n")[0]
        semester_index = semesters[first_key]
        __rule_2(semester_index, evaluation_activities)
        second_key = semester_key.split("\n")[1]
        semester_index = semesters[second_key]
        __rule_2(semester_index, evaluation_activities)
    else:
        first_key = semester_key.split("\n")[0]
        semester_index = semesters[first_key]
        __rule_2(semester_index, evaluation_activities)

# Rule 3: Si existe la semana 17, se dejará en blanco la semana 16 y los exámenes se reflejarán en
# la semana 17. Si no existe la semana 17, se pondrán los exámenes en la 16.
def rule_3(json_document):
    evaluation_activities = json_document['cronograma']
    if len(evaluation_activities) == 16:
        globals_week = evaluation_activities[15]
        globals_week_is_correct = 0 == len(globals_week['actividad_tipo_1']) + len(globals_week['actividad_tipo_2']) + len(
            globals_week['tele_ensenanza']) and 0 != len(globals_week['actividades_evaluacion'])
        if not globals_week_is_correct:
            print("\tRule 3: Week 16/16 has either lecturing activities or does not contain global examns")
    elif len(evaluation_activities) == 17:
        empty_week = evaluation_activities[15]
        week_is_empty = 0 == len(empty_week['actividad_tipo_1']) + len(empty_week['actividad_tipo_2']) + len(
            empty_week['tele_ensenanza']) + len(empty_week['actividades_evaluacion'])
        globals_week = evaluation_activities[16]
        globals_week_is_correct = 0 == len(globals_week['actividad_tipo_1']) + len(globals_week['actividad_tipo_2']) + len(
            globals_week['tele_ensenanza']) and 0!= len(globals_week['actividades_evaluacion'])
        if not week_is_empty:
            print("\tRule 3: Week 16/17 is not empty")
        if not globals_week_is_correct:
            print("\tRule 3: Week 17/17 has either lecturing activities or does not contain global examns")
    else:
        print("error in the cronograme, it has less than 16 activities")

# Rule 4: El peso total de la evaluación progresiva/ordinaria/extraordinaria debe ser el 100%.
def rule_4(json_document, evaluation_type):
    evaluation_activities = json_document['evaluacion']['actividades']
    total_weight = 0
    for activity in evaluation_activities:
        if evaluation_type in activity["tipo_evaluacion"]:
            test_weight = activity["peso"]
            if len(test_weight) == 0:
                test_weight = 0.0
            else:
                test_weight = float(test_weight.replace("%", ""))
            total_weight += test_weight

            test_week = activity["semana"]
            test_min_grade = activity["nota_minima"]
            if len(test_min_grade) == 0:
                test_min_grade = None
            if test_weight == 0:
                print("\t\t[WARNING] Rule 4 ( evaluation '",evaluation_type.strip(),"'): ", test_week, " has a test with weight 0.0% and minimum grade of ", test_min_grade)
    if total_weight != 100.0:
        print("\tRule 4 (evaluation '",evaluation_type.strip(),"'): evaluation activities exceed/receed 100% percentage, in particular: ", total_weight)


'''
    Main code
'''

if __name__ == '__main__':
    directory = "./guides_data/"
    files = list_files(directory)
    suffix_file_1 = "-61CD-2025-26.json"


    for subject_code in read_subjects(files):
        #if str(subject_code) in "615001054":#str(subject_code) in "615001015" or str(subject_code) in "615001001":
        guide = read_json(directory + subject_code + suffix_file_1)
        print("Report for (",subject_code,") ",guide['Datos descriptivos']['Nombre de la Asignatura'])
        rule_2(guide)
        rule_3(guide)
        rule_4(guide, "progresiva")
        rule_4(guide, "global")
        rule_4(guide, "extraordinaria")
