

import json
import os
from typing import Dict, Any
from rdflib import Graph, URIRef, Namespace, RDF, Literal, XSD
from urllib.parse import quote
import re

SCH = Namespace("https://schema.org/")
GUIA = Namespace("https://guia.org/")
DATA = Namespace("https://guia-kg.skai.etsisi.upm.es/resource/")
OM = Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")

SUMMARY_PREFIX = "resumen/"
EVALUATION_PREFIX = "evaluacion/actividades/"
BIBLIOGRAPHY_PREFIX = "recursos_didacticos/"

CONTEXT = {
    # ------- Course
    'Nombre de la Asignatura' : { 'term' : SCH.name,  'lang' : 'es' },
    'Nombre en inglés' : { 'term' : SCH.name,  'lang' : 'en' },
    'Código UPM' : { 'term' : SCH.courseCode,  'xsd' : XSD.integer },
    'Semestre/s de impartición': {'term': GUIA.semester, 'lang': 'es'},
    'Carácter': {'term': GUIA.courseType, 'lang': 'es'}, # caracter: basic/mandatory, etc.
    'Titulación' : None, # Used to build op in rdf_course()
    'Centro responsable de la titulación' : None, # Used to build op in rdf_course()
    # ------- Course Instance
    'Idioma de impartición' : { 'term' : SCH.inLanguage,  'lang' : 'es' },
    'Otros idiomas de impartición' : { 'term' : SCH.inLanguage,  'lang' : 'es' },
    'No Créditos': {'term': GUIA.numberOfCredits, 'xsd': XSD.decimal },
    'Curso Académico': {'term': GUIA.teachingPeriod },
    'Período de impartición': {'term': GUIA.teachingPeriodMonths, 'lang': 'es'},
    'Curso': None,  # Transformation made manually in rdf_course_instance() for enriching course
    'resumen/horas_totales' : { 'term' : GUIA.totalHours,  'lang' : 'es' }, #owl:equivalentProperty SCH.courseWorkload
    'resumen/horas_presenciales' : { 'term' : GUIA.inpersonHours,  'lang' : 'es' },
    'resumen/peso_actividades' : { 'term' : SCH.activitiesWorkload,  'lang' : 'es' }, # owl:equivalentProperty SCH.activitiesWorkload
    # -------  Professors
    'Despacho': {'term': GUIA.office, 'lang': 'es'},
    'e-mail': {'term': SCH.email},
    'Tutorías': {'term': GUIA.tutorshipsSchedule, 'lang': 'es'},
    'Nombre' : {'term': SCH.name, 'value_processing': 're.sub(r"\\([^)]+\\)", "", "###").strip()'},
    # -------  Activities
    'duracion' : { 'term' :  GUIA.activityDuration, 'additional_triplets' : [(GUIA.activityDurationUnit, OM.hour)], 'value_processing' : '"###".split(" ")[1].strip()'},
    'modalidad' : { 'term' : GUIA.activityFormat, 'lang' : 'es' },
    'descripcion' : { 'term' : GUIA.activityDescription, 'lang' : 'es' },
    'tecnica' : { 'term' : GUIA.activityFormat,  'lang' : 'es' },
    'tipo_eval' : { 'term' : GUIA.evaluationType,  'lang' : 'es' },
    'presencialidad' : { 'term' : GUIA.attendanceType,  'lang' : 'es' },
    # -------- EvaluationSystem
    'criterios_evaluacion' : { 'term' : GUIA.evaluationDescription,  'lang' : 'es' },
    'evaluacion/actividades/tipo_evaluacion': { 'term' : GUIA.evaluationType,  'lang' : 'es' },
    'evaluacion/actividades/semana': { 'term' : GUIA.trialWeek,  'lang' : 'es' },
    'evaluacion/actividades/descripcion': { 'term' : GUIA.trialDescription,  'lang' : 'es' },
    'evaluacion/actividades/modalidad': { 'term' : GUIA.trialMode,  'lang' : 'es' },
    'evaluacion/actividades/tipo': { 'term' : GUIA.trialType,  'lang' : 'es' },
    'evaluacion/actividades/duracion': { 'term' : GUIA.evaluationDuration,  'lang' : 'es' },
    'evaluacion/actividades/peso': { 'term' : GUIA.gradePercentage,  'lang' : 'es' },
    'evaluacion/actividades/nota_minima': { 'term' : GUIA.minimumScore,  'lang' : 'es' },
    'evaluacion/actividades/competencias' : None, # Transformation made manually in rdf_evaluation()
    'actividades' : None, # Transformation made manually in rdf_evaluation()
    # -------- Biliography
    'recursos_didacticos/nombre': {'term': GUIA.bibliographyTitle, 'lang': 'es'},
    'recursos_didacticos/tipo': {'term': GUIA.bibliographyType, 'lang': 'es'},
    'recursos_didacticos/descripcion': {'term': GUIA.bibliographyDescription, 'lang': 'es'},
}

def get_value(json_document, key):
    value = None
    if key in json_document:
        value = json_document[key]
    return value

def get_json_term(key):
    if key in CONTEXT.keys():
        json_term = CONTEXT[key]
        if json_term is None:
            return None, None, None, None, None
    else:
        raise Exception("Term :'"+str(key)+"' not found in context.")
    return (json_term['term'],
            get_value(json_term, 'lang'),
            get_value(json_term, 'xsd'),
            get_value(json_term, 'additional_triplets'), get_value(json_term,'value_processing'))


def build_rdf_from_json(json_fragment, subject_uri, term_prefix=""):
    graph = Graph()
    for key, value in json_fragment.items():
        try:
            term, lang, xsd, additional_triplets, value_processing = get_json_term(term_prefix+key)
            if term is not None:
                if value_processing:
                    value = eval(value_processing.replace("###", value))
                if additional_triplets:
                    for additional_triplet in additional_triplets:
                        graph.add((subject_uri, additional_triplet[0], additional_triplet[1]))
                if value is not None and len(value)>0:
                    graph.add((subject_uri, term, Literal(value, datatype=xsd, lang=lang, normalize=True)))
        except Exception as e:
            print(">", e, "when working with: ",key, " - ", value)

    return graph

def buildURIRef(domain, *args):
    new_uri = ""
    for arg in args:
        new_uri += str(arg)
    return URIRef(domain+quote(new_uri))


def rdf_course(course_data):
    course_graph = Graph()
    # ---- COURSE RDF
    course_uri = buildURIRef(DATA,course_data['Código UPM'])
    # RDF type
    course_graph.add((course_uri, RDF.type, GUIA.Course))
    # Triplets translation
    course_graph += build_rdf_from_json(course_data, course_uri)

    # ---- DEGREE RDF
    degree = buildURIRef(DATA, course_data["Titulación"])
    #course_graph.add((degree, RDF.type, GUIA.Degree))  # type
    # Type specialization
    degree_name = course_data["Titulación"].lower().replace("á", "a")
    if "master universitario" in degree_name or " master " in degree_name:
        course_graph.add((degree, RDF.type, GUIA.MasterDegree))
    else:
        course_graph.add((degree, RDF.type, GUIA.BachelorDegree))
    # Triplets translation
    title_elements = course_data["Titulación"].split("-")
    course_graph.add((degree, SCH.name, Literal(' '.join(title_elements[1:].strip()), lang="es"))) # name
    course_graph.add((degree, GUIA.degreeCode, Literal(title_elements[0].strip(), lang="es"))) # name
    course_graph.add((degree, GUIA.hasCourse, course_uri))  # type
    # ---- Organisation RDF
    organisation = buildURIRef(DATA, course_data["Centro responsable de la titulación"].split("-")[1].strip())
    course_graph.add((organisation, RDF.type, GUIA.UniversityCenter))  # type
    course_graph.add((organisation, SCH.name, Literal(course_data["Centro responsable de la titulación"].split("-")[1].strip())))  # name
    course_graph.add((organisation, GUIA.offers, degree))  # op

    return course_graph, course_uri

def rdf_course_instance(full_data, course_uri):
    ''' "Datos Generales", "Descripción de la Asignatura", "resumen" "Otra información reseñable" '''
    course_inst_graph = Graph()
    data = full_data['Datos Generales']
    course_inst_uri = buildURIRef(course_uri+"/", data['Curso Académico'])

    # ---- Enrich course
    if len(data['No Créditos'].strip()) > 0:
        course_inst_graph.add((course_uri, SCH.numberOfCredits, Literal(data['No Créditos'], datatype=XSD.decimal, normalize=True)))
    if len(data['Curso'].strip())>0:
        course_inst_graph.add((course_uri, DATA.courseYear, Literal(data['Curso'], datatype=XSD.integer, normalize=True)))

    # link with course instance
    course_inst_graph.add((course_uri, SCH.hasCourseInstance, course_inst_uri))
    # ---- Course instance
    # Type
    course_inst_graph.add((course_inst_uri, RDF.type, GUIA.CourseGuide))

    # Triplets translation
    course_inst_graph += build_rdf_from_json(data, course_inst_uri)
    course_inst_graph.add((course_inst_uri, SCH.name,Literal(full_data['Datos descriptivos']['Nombre de la Asignatura'], lang="es", normalize=True)))
    course_inst_graph.add((course_inst_uri, GUIA.periodStaringtMonth,
                           Literal(data['Período de impartición'].split("-")[0].strip(), lang="es", normalize=True)))
    course_inst_graph.add((course_inst_uri, GUIA.periodEndingMonth,
                           Literal(data['Período de impartición'].split("-")[1].strip(), lang="es", normalize=True)))

    # Keyword "Descripción de la Asignatura"
    if 'Descripción de la Asignatura' in full_data.keys():
        course_inst_graph.add((course_inst_uri, SCH.description, Literal(full_data['Descripción de la Asignatura'], lang="es")))

    # Keyword: "resumen"
    if 'resumen' in full_data.keys():
        course_inst_summary_json = full_data['resumen']
        course_inst_graph += build_rdf_from_json(course_inst_summary_json, course_inst_uri, term_prefix=SUMMARY_PREFIX)

    # Keyword: ""
    if 'Otra información reseñable' in full_data.keys():
        course_inst_graph.add((course_inst_uri, GUIA.otherInformation, Literal(full_data['Otra información reseñable'], lang="es", normalize=True)))

    return course_inst_graph, course_inst_uri

def rdf_lecturers(full_data, course_inst_uri):
    ''' "Profesorado"  '''
    professor_graph = Graph()
    data_list = full_data['Profesorado']

    for data in data_list:
        professor_uri = buildURIRef(DATA, data['e-mail'])
        # RDF type
        professor_graph.add((professor_uri, RDF.type, GUIA.Lecturer))  # type
        professor_graph += build_rdf_from_json(data, professor_uri)
        # Triplets translation
        professor_graph.add((course_inst_uri, SCH.instructor, professor_uri))  # type
        if "coordinador" in data['Nombre'].lower():
            professor_graph.add((course_inst_uri, SCH.director, professor_uri))  # type

    # TODO: find a guide that contains this data first
    if len(full_data['Personal Investigador en Formación o Similar'])>0:
        print("TODO ('Personal Investigador en Formación o Similar'):",full_data['Personal Investigador en Formación o Similar'])

    if len(full_data['Profesorado Externo'])>0:
        print("TODO ('Profesorado Externo'):",full_data['Profesorado Externo'])

    return professor_graph


def rdf_previous_knowledge_or_skills(data, course_inst_uri):
    graph  = Graph()
    previous_courses_uri = buildURIRef(course_inst_uri+"/", "previous_courses" )
    graph.add((previous_courses_uri, RDF.type, GUIA.RequiredKnowledge))
    if 'Asignaturas Previas Requeridas' in data.keys():
        prev_courses = data['Asignaturas Previas Requeridas']['Otros Requisitos']
        graph.add((previous_courses_uri, GUIA.previousCourses, Literal(prev_courses, lang="es", normalize=True)))
        if len(data['Asignaturas Previas Requeridas'].keys())>1:
            print("TODO: check 'Asignaturas Previas Requeridas': ", data['Asignaturas Previas Requeridas'])
    if 'Otros Requisitos' in data.keys():
        prev_other = data['Otros Requisitos']['Otros Conocimientos Previos Recomendados']
        graph.add((previous_courses_uri, GUIA.previousKnowledge, Literal(prev_other, lang="es", normalize=True)))
        if len(data['Otros Requisitos'].keys()) > 1:
            print("TODO: check 'Otros Requisitos': ", data['Otros Requisitos'])

    return graph

def rdf_competencies_leraningres(data, course_inst_uri):
    comp_learres_graph = Graph()
    competencies_key = 'RD 1393 - Competencias / RD 822 - Resultados de Aprendizaje'
    learning_result_key = 'RD 1393 - Resultados de Aprendizaje'
    document_keys = data.keys()

    if competencies_key in document_keys:
        for line in data[competencies_key]:
            elems = line.split("-")
            compentency_uri = buildURIRef(course_inst_uri+"/", elems[0].strip())
            comp_learres_graph.add((compentency_uri, RDF.type, GUIA.Competency))  # type
            comp_learres_graph.add((compentency_uri, GUIA.competencyDescription, Literal(elems[1].strip(),lang="es", normalize=True)))  # type
            comp_learres_graph.add((compentency_uri, GUIA.competencyCode, Literal(elems[0].strip())))  # type
            comp_learres_graph.add((course_inst_uri, GUIA.hasCompetency, compentency_uri))  # type
    if learning_result_key in document_keys:
        for line in data[learning_result_key]:
            elems = line.split("-")
            learning_res_uri = buildURIRef(course_inst_uri+"/", elems[0].strip())
            comp_learres_graph.add((learning_res_uri, RDF.type, GUIA.LearningResult))  # type
            comp_learres_graph.add((learning_res_uri, GUIA.learningResultDescription, Literal(elems[1].strip(),lang="es", normalize=True)))  # type
            comp_learres_graph.add((learning_res_uri, GUIA.learningResultCode, Literal(elems[0].strip(), normalize=True)))  # type
            comp_learres_graph.add((course_inst_uri, GUIA.hasLearningResult, learning_res_uri))  # type

    return comp_learres_graph

def rdf_syllabus(full_data, course_inst_uri):
    syllabus_graph = Graph()

    syllabus_uri = buildURIRef(course_inst_uri+"/", 'syllabus')
    syllabus_graph.add((course_inst_uri, GUIA.hasSyllabus, syllabus_uri))
    syllabus_graph.add((syllabus_uri, RDF.type, GUIA.Syllabus))

    for text in full_data['Temario']:
        index = full_data['Temario'].index(text)
        syllabus_item_uri = buildURIRef(syllabus_uri+"/", index)

        syllabus_graph.add((syllabus_uri, GUIA.hasItem, syllabus_item_uri))

        syllabus_graph.add((syllabus_item_uri, RDF.type, GUIA.SyllabusItem))
        syllabus_graph.add((syllabus_item_uri, GUIA.itemIndex, Literal(index, normalize=True) ))
        syllabus_graph.add((syllabus_item_uri, GUIA.syllabusDescription, Literal(text, lang="es", normalize=True)))

    return syllabus_graph

def rdf_bibliography(full_data, course_inst_uri):
    bibliography_graph = Graph()
    json_keyword = "recursos_didacticos"
    bib_index = 0
    if json_keyword in full_data.keys():
        for bib_entry in full_data[json_keyword]:
            bib_index += 1
            bibliography_entry_uri = buildURIRef(course_inst_uri + "/didactic_resource/",bib_index )
            bibliography_graph.add((course_inst_uri, GUIA.hasDidacticResource, bibliography_entry_uri)) # op
            bibliography_graph.add((bibliography_entry_uri, RDF.type, GUIA.DidacticResource)) # type
            # Triplets translation
            bibliography_graph += build_rdf_from_json(bib_entry, bibliography_entry_uri, term_prefix=BIBLIOGRAPHY_PREFIX)

    return bibliography_graph

def rdf_actividad(activities, schedule_event_uri, activity_type):
    activity_graph = Graph()
    index = 0
    for activity in activities:
        index += 1
        activity_uri = buildURIRef(schedule_event_uri + "/activity/T"+str(activity_type)+"/", index)
        activity_graph.add((schedule_event_uri, GUIA.hasActivity, activity_uri))  # op

        #activity_graph.add((activity_uri, RDF.type, GUIA.Activity))  # type
        activity_type_uri = buildURIRef(GUIA, str(activity_type))
        activity_graph.add((activity_uri, RDF.type, activity_type_uri))  # type
        # Triplets translation
        activity_graph += build_rdf_from_json(activity, activity_uri)

    return activity_graph




def rdf_chronogram(data, course_inst_uri):
    ''' "cronograma" '''
    chronogram_graph = Graph()
    week_index=0
    schedule_uri = buildURIRef(course_inst_uri + "/eventSchedule","")
    chronogram_graph.add((course_inst_uri, SCH.courseSchedule, schedule_uri))  # type
    chronogram_graph.add((schedule_uri, RDF.type, GUIA.Schedule))
    if 'cronograma' in data.keys():
        for week in data["cronograma"]:
            week_index += 1

            schedule_event_uri = buildURIRef(course_inst_uri+"/eventSchedule/", week_index)
            chronogram_graph.add((schedule_uri, SCH.eventSchedule, schedule_event_uri))
            chronogram_graph.add((schedule_event_uri, RDF.type, GUIA.ScheduleEvent))  # type
            chronogram_graph.add((schedule_event_uri, GUIA.eventIndex,  Literal(week_index)))
            chronogram_graph.add((schedule_event_uri, GUIA.eventWeek, Literal(week['semana'], lang="es")))

            if week['actividad_tipo_1']:
                chronogram_graph += rdf_actividad(week['actividad_tipo_1'], schedule_event_uri, "ActivityType1")
            if week['actividad_tipo_2']:
                chronogram_graph += rdf_actividad(week['actividad_tipo_2'], schedule_event_uri, "ActivityType2")
            if week['tele_ensenanza']:
                chronogram_graph += rdf_actividad(week['tele_ensenanza'], schedule_event_uri, "RemoteActivity")
            if week['actividades_evaluacion']:
                chronogram_graph += rdf_actividad(week['actividades_evaluacion'], schedule_event_uri, "EvaluationActivity")

    return chronogram_graph

def rdf_evaluation(evaluation_json, course_inst_uri):
    evaluation_graph = Graph()

    evaluation_uri = buildURIRef(course_inst_uri + "/evaluation", "")
    evaluation_graph.add((course_inst_uri, GUIA.hasEvaluation, evaluation_uri))
    evaluation_graph.add((evaluation_uri, RDF.type, GUIA.EvaluationSystem))
    evaluation_graph += build_rdf_from_json(evaluation_json, evaluation_uri)

    evaluation_index = 0
    for evaluation_activity in evaluation_json["actividades"]:
        evaluation_index += 1
        eval_activity_uri = buildURIRef(course_inst_uri + "/evaluation/trial", str(evaluation_index))
        evaluation_graph.add((evaluation_uri, GUIA.hasEvaluationTrial, eval_activity_uri))
        evaluation_graph.add((eval_activity_uri, RDF.type, GUIA.EvaluationTrial))

        evaluation_graph += build_rdf_from_json(evaluation_activity, eval_activity_uri, term_prefix=EVALUATION_PREFIX)

        # Linkage to syllabus
        if "semana" in evaluation_activity.keys() and evaluation_activity["semana"] is not None:
            week_number = evaluation_activity["semana"]
            syllabus_activity_uri = buildURIRef(course_inst_uri+ "/eventSchedule/", str(week_number))
            evaluation_graph.add((eval_activity_uri, GUIA.hasScheduleEvent, syllabus_activity_uri))

        if "competencias" in evaluation_activity.keys():
            for competencia in evaluation_activity["competencias"]:
                competency_uri = buildURIRef(DATA, competencia)
                evaluation_graph.add((eval_activity_uri, GUIA.involvesCompetency, competency_uri))

    return evaluation_graph



def extract_kg(data):
    final_graph = Graph()

    graph, course_uri = rdf_course(data['Datos descriptivos'])
    final_graph += graph
    graph, course_inst_uri = rdf_course_instance(data, course_uri)
    final_graph += graph
    final_graph += rdf_lecturers(data, course_inst_uri)
    final_graph += rdf_previous_knowledge_or_skills(data, course_inst_uri)
    final_graph += rdf_competencies_leraningres(data, course_inst_uri)
    final_graph += rdf_syllabus(data, course_inst_uri)
    final_graph += rdf_chronogram(data, course_inst_uri)
    final_graph += rdf_evaluation(data["evaluacion"], course_inst_uri)
    final_graph += rdf_bibliography(data, course_inst_uri)

    #print(final_graph.serialize())

    return final_graph


'''
    Main functions
'''

'''
    Creates the KG from a given json file
'''
def kg_from_file(file_path, store_file=True):
    graph = Graph()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            graph = extract_kg(data)
            rdf_file_name = file_path.replace(".json", ".ttl")
            if store_file:
                graph.serialize(destination=rdf_file_name)
                print("Processed {}".format(file_path), " graph size: ", len(graph))
            return graph
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return graph

'''
    Creates the guides availability
'''
import os
def kg_of_pdf_availability_file(file_path, graph):
    if os.path.exists(file_path):
        pdf_file_name = file_path.split("/")[-1].replace(".pdf", "")
        name_elements = pdf_file_name.split("-")
        academic_year = name_elements[2]+"-"+name_elements[3]
        course_identifier= name_elements[0]+"/"+academic_year
        course_uri = buildURIRef(DATA, course_identifier)

        semester = "1S"
        query = """ PREFIX guia: <https://guia.org/> SELECT ?semester WHERE { ?course_uri guia:teachingPeriodMonths ?semester . } """
        qres = graph.query(
            query,
            initBindings={"course_uri": course_uri}
        )
        for row in qres:
            if "Febrero-Junio" in row.semester:
                semester = "2S"

        available_url = "https://www.upm.es/comun_gauss/publico/guias/" + academic_year + "/" + semester + "/GA_" + name_elements[1] + "_" + name_elements[0] + "_" + semester + "_" + academic_year + ".pdf"
        graph.add((course_uri, GUIA.publishedAt, URIRef(available_url)))

    return graph

'''
    Creates the KG from a given directory filled with json files
'''
def kg_from_directory(directory_path, dump_file="/dump.ttl", store_dump=True, store_fragments=True):
    graph = Graph()
    for filename in os.listdir(directory_path):
        # Generate RDF from Json
        if filename.lower().endswith(".json"):
            file_path = os.path.join(directory_path, filename)
            graph += kg_from_file(file_path, store_fragments)

            file_pdf = file_path.replace(".json", ".pdf")
            # Generate PDF linkage
            kg_of_pdf_availability_file(file_pdf, graph)

    if store_dump:
        graph.serialize(destination=directory_path + dump_file)

    print("Final graph size: ", len(graph))



if __name__ == "__main__":
    directory_path = "./guides_data"  # change this
    kg_from_directory(directory_path, dump_file="/dump.ttl", store_dump=True, store_fragments=True)


