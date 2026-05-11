import os

from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor
import copy
from pathlib import Path
import requests
import urllib.request


KG_EXTRACTOR_WORKERS = 8


'''
    ** Methods to index gauss guides
'''

class GaussIndexer:
    
    def __init__(self, username, password):
        self.__login_url = "https://www.upm.es/gauss/login.upm?redirect=/informes_asignatura/gestion/cumplimentacion&failure=12"
        self.__guides_url = "https://www.upm.es/gauss/principal.upm/guias/consulta/consulta-guia"
        self.__study_plans_url = "https://www.upm.es/gauss/includes_ajax/guias/listados/gga_listado_planes.upm"
        self.__subjects_url_template = "https://www.upm.es/gauss/includes_ajax/guias/listados/gga_listado_asignaturas_semestre.upm"
        self.__subject_guide_url_template = "https://www.upm.es/comun_gauss/publico/guias/"
        self.__guide_description_url = "https://www.upm.es/gauss/principal.upm/guias/consulta/consulta-guia/"
        self.__logged = False
        self.username = username
        self.password = password




    '''
        Login methods
    '''

    def login(self):
        try:
            # Navigate to the GAUSS login page
            driver = webdriver.Chrome()
            driver.get(self.__login_url)
            # Wait for the page to load
            time.sleep(1) #2
    
            # Locate the username and password fields
            username_field = driver.find_element(By.NAME, "username")
            password_field = driver.find_element(By.NAME, "upasswd")
    
            # Enter your credentials
            username_field.send_keys(self.username)  # Replace with your username
            password_field.send_keys(self.password)  # Replace with your password
    
            # Submit the login form
            login_button = driver.find_element(By.NAME, "form_login_enviar")
            login_button.click()
    
            # Wait for the next page to load
            time.sleep(1.5) # 3

            # Check if login was successful by looking for a specific element
            if "Su sesión ha expirado" in driver.page_source:
                print("Login failed: Session expired.")
            else:
                #print("Login successful!")
                self.__logged = True
                return driver
        except Exception as e:
            raise Exception(e)


    '''
        Indexing methods
    '''
    def get_list_of_years(self, driver):
        try:
            driver.get(self.__guides_url)
            return driver.find_element(By.ID, "filtro_anio").text.replace(" ", "").replace("\n", "").replace("AñoAcadémico:","").split(";")
        except Exception as e:
            print("Exception occurred [get_list_of_years]: ", e)
    
    def list_study_plans(self, driver):
        try:
            driver.get(self.__study_plans_url)
            return json.loads(driver.find_element(By.XPATH, "/html/body").text)
        except Exception as e:
            print("Exception occurred [list_study_plans]: ", e)
    
    def list_subjects(self, driver, study_plans_code, semester_id, semester_year):
        try:
            built_url = self.__subjects_url_template + "?pla_codalf=" + study_plans_code + "&id_semestre=" + semester_id + "&any_anyaca=" + semester_year
            driver.get(built_url)
            return json.loads(driver.find_element(By.XPATH, "/html/body").text)
        except Exception as e:
            print("Exception occurred [list_subjects]: ", e)
    
    def __build_subject_guide(self, study_plans_code, semester_id, semester_year, subject_code):
        try:
            built_url = self.__subject_guide_url_template + semester_year + "/" + semester_id + "/GA_" + study_plans_code + "_" + subject_code + "_" + semester_id + "_" + semester_year + ".pdf"
            return built_url
        except Exception as e:
            print("Exception occurred [build_subject_guide]: ", e)
    
    def __build_record(self, academic_year, semester, study_plan_type, study_plan_code, study_plan_name, subject_type, subject_code, subject_name, guide_url):
        info_base_url = self.__guide_description_url + academic_year + "/" + semester + "/" + study_plan_code + "/" + subject_code
        info_description_url = info_base_url + "/datos-descriptivos"
        info_professors_url = info_base_url + "/profesorado"
        info_prev_requirements_url = info_base_url +"/requisitos-previos"
        info_competences_and_results_url = info_base_url +"/competencias-y-resultados-aprendizaje"
        info_syllabus_url = info_base_url +"/temario"
        info_schedule_url = info_base_url +"/cronograma"
        info_evaluation_url = info_base_url +"/evaluacion"
        info_resources_url = info_base_url +"/recursos-didacticos"
        info_other_url = info_base_url +"/otra-informacion"
        return { "academic_year": academic_year, "semester": semester,  "study_plan_type": study_plan_type, "study_plan_code": study_plan_code, "study_plan_name": study_plan_name,  "subject_type": subject_type, "subject_code": subject_code, "subject_name": subject_name, "guide_pdf_url": guide_url, "info_description_url" : info_description_url, "info_professors_url" : info_professors_url, "info_prev_requirements_url" : info_prev_requirements_url, "info_competences_and_results_url" : info_competences_and_results_url, "info_syllabus_url" : info_syllabus_url, "info_schedule_url" : info_schedule_url, "info_evaluation_url" : info_evaluation_url, "info_resources_url" : info_resources_url, "info_other_url" : info_other_url  }
    
    def __print_processing_percentage(self, study_plan, study_plans, academic_year):
        processing_status = 100 * round(study_plans.index(study_plan) / len(study_plans), 2)
        if processing_status % 10 == 0:
            print("Indexing gauss (", academic_year, ")...", processing_status, "%")
        
    
    def build_gauss_index(self, only_last_year=False, years=[]):
        driver = self.login()
        available_years = years
        if len(years)==0:
            available_years = self.get_list_of_years(driver=driver)
        study_plans = self.list_study_plans(driver=driver)
        time.sleep(3)
        records = []
        for academic_year in available_years:
            for semester in ["1S", "2S"]:
                for study_plan in study_plans:
                    study_plan['semester'] = semester
                    study_plan_code = study_plan["codigo"]
                    study_plan_name = study_plan["label"]
                    study_plan_type = study_plan["category"]
                    study_plan['asignaturas'] = []
                    self.__print_processing_percentage(study_plan, study_plans, academic_year)
                    try:
                        subjects = self.list_subjects(driver, study_plan_code, semester, academic_year)
                        for subject in subjects:
                            subject_name = subject['label']
                            subject_code = subject['codigo']
                            subject_type = subject['category']
                            guide_url = self.__build_subject_guide(study_plans_code=study_plan_code, semester_id=semester, semester_year=academic_year, subject_code=subject_code)
                            record = self.__build_record(academic_year, semester, study_plan_type, study_plan_code, study_plan_name, subject_type, subject_code, subject_name, guide_url)
                            records.append(record)
                    except Exception as e:
                        print("Exception occurred [build_subject_guide]: ", e)
            if only_last_year and len(years)>1:
                break
        return pd.DataFrame(records)

    '''
        JSON extraction methods
    '''

    def __extract_description(self, driver, url):
        driver.get(url)
        time.sleep(1)
        # Extract data
        data_by_section = {}
        section_titles = driver.find_elements(By.CSS_SELECTOR, "div.vista")

        for title_element in section_titles:
            section_name = title_element.text.strip()
            table_dict = {}

            # Buscar la siguiente tabla_resultado después del título
            parent = title_element.find_element(By.XPATH, "following-sibling::div[contains(@class, 'caja')]")
            table = parent.find_element(By.CSS_SELECTOR, "table.tabla_resultado")

            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) % 2 == 0:
                    for i in range(0, len(cells), 2):
                        key = cells[i].text.strip()
                        value = cells[i + 1].text.strip()
                        if key:
                            table_dict[key] = value

            if section_name and table_dict:
                data_by_section[section_name] = table_dict

        # Mostrar como JSON
        return data_by_section

    def __extract_professors(self, driver, url):
        driver.get(url)
        time.sleep(1)
        # Extraction
        # Diccionario final
        result = {}

        # Extraer secciones y sus tablas
        secciones = driver.find_elements(By.CLASS_NAME, "vista")
        tablas = driver.find_elements(By.CLASS_NAME, "tabla_recursos")
        for seccion, tabla in zip(secciones, tablas):
            titulo = seccion.text.strip()
            datos = []

            filas = tabla.find_elements(By.TAG_NAME, "tr")
            result[titulo] = datos
            if len(filas) > 1:
                # Extract headers
                headers = []
                table_header = filas[0].find_elements(By.TAG_NAME, "th")
                for column_name in table_header:
                    headers.append(column_name.text.strip())

                # Extrac content
                filas = filas[1:]  # Omitimos el encabezado
                for fila in filas:
                    celdas = fila.find_elements(By.TAG_NAME, "td")
                    index = 0
                    professors_json = {}
                    for celda in celdas:
                        clave = headers[index]
                        valor = celda.text.strip()
                        professors_json[clave] = valor
                        index += 1
                    datos.append(professors_json)
            result[titulo] = datos

        return result


    def __extract_requirements(self, driver, url):
        driver.get(url)
        time.sleep(1)
        # Extraer secciones principales
        result = {}
        seccion = driver.find_elements(By.CLASS_NAME, "titulo")
        cajas = driver.find_elements(By.CLASS_NAME, "caja")
        for seccion, caja in zip(seccion, cajas):
            titulos = caja.find_elements(By.CLASS_NAME, "titulo")
            listas = caja.find_elements(By.CLASS_NAME, "fondo_resultado")
            for titulo, contenido in zip(titulos, listas):
                result[seccion.text.strip()] = { titulo.text.strip() : contenido.text.strip() }

        return result



    def __extract_competentences_and_results(self, driver, url):
        driver.get(url)
        time.sleep(1)
        result = {}

        # Extraer secciones principales
        secciones = driver.find_elements(By.CLASS_NAME, "vista")
        cajas = driver.find_elements(By.CLASS_NAME, "caja")

        for seccion, caja in zip(secciones, cajas):
            titulo_seccion = seccion.text.strip()
            ul = caja.find_element(By.CLASS_NAME, "fondo_resultado").find_element(By.TAG_NAME, "ul")
            items = [li.text.strip() for li in ul.find_elements(By.TAG_NAME, "li") if li.text.strip()]
            result[titulo_seccion] = items

        return result

    def __extract_syllabus(self, driver, url):
        driver.get(url)
        time.sleep(1)

        resultado = {}

        # Extraer la descripción de la asignatura
        try:
            titulo_desc = driver.find_element(By.ID, "gga_da_denominacion").text.strip()
            contenido_desc = driver.find_element(By.CLASS_NAME, "fondo_resultado").text.strip()
            resultado[titulo_desc] = contenido_desc
        except Exception:
            resultado["Descripción"] = "No disponible"

        # Extraer temario general y subniveles
        try:
            temario_contenedor = driver.find_element(By.ID, "gga_tem_wrap")
            temario = []
            titulos = temario_contenedor.find_elements(By.CLASS_NAME, "accordion-heading")
            for titulo in titulos:
                # Limpiar textos no deseados como botones
                text_parts = [t for t in titulo.text.strip().split('\n') if
                              t.strip() and not t.lower().startswith("ocultar")]
                if text_parts:
                    temario.append(text_parts[0])
            resultado["Temario"] = temario
        except Exception:
            resultado["Temario"] = []

        return resultado



    def __extract_schedule(self, driver, url):
        driver.get(url)
        time.sleep(1)

        ##
        # Extraer resumen de horas y peso
        data = {}
        try:
            horas_tot = driver.find_element(By.ID, "gga_cr_horas_totales").text.replace("Horas totales: ", "")
            horas_pres = driver.find_element(By.ID, "gga_cr_horas_presenciales").text.replace("Horas presenciales: ", "")

            labels = driver.find_elements(By.XPATH, "//*[starts-with(@id, 'gga_cr_horas_peso_continua_')]")
            peso = labels[0].text.strip().replace("Peso total de actividades de evaluación: ", "")
            data['resumen'] = { 'horas_totales': horas_tot, 'horas_presenciales': horas_pres, 'peso_actividades': peso }
        except Exception as e:
            print("execption ("+str(url)+"): ", e)
            data['resumen_horas'] = {}

        # Extraer tabla de cronograma
        weeks = driver.find_elements(By.CSS_SELECTOR, "tr.semana")

        for week in weeks:
            week_data = {}
            try:
                week_label = week.find_element(By.CSS_SELECTOR, ".head-semana p").text.strip()
                week_data["semana"] = week_label
            except:
                week_data["semana"] = None

            # Iterate over the four columns of activities
            columns = ["A", "L", "O", "E"]
            activity_types = {
                "A": "actividad_tipo_1",
                "L": "actividad_tipo_2",
                "O": "tele_ensenanza",
                "E": "actividades_evaluacion"
            }

            for col in columns:
                col_id = f'gga_cr_{week_label.split()[-1]}_{col}'
                try:
                    container = week.find_element(By.ID, col_id)
                    actividades = []
                    for act in container.find_elements(By.CLASS_NAME, "gga_cr_act"):
                        actividad = {}
                        try:
                            actividad["descripcion"] = act.find_element(By.CLASS_NAME, "gga_cr_desc").text
                        except:
                            actividad["descripcion"] = None
                        try:
                            actividad["modalidad"] = act.find_element(By.CLASS_NAME, "gga_cr_mod").text
                        except:
                            try:
                                actividad["tecnica"] = act.find_element(By.CLASS_NAME, "gga_cr_tec").text
                            except:
                                actividad["tecnica"] = None
                            try:
                                actividad["tipo_eval"] = act.find_element(By.CLASS_NAME, "gga_cr_type").text
                            except:
                                actividad["tipo_eval"] = None
                            try:
                                actividad["presencialidad"] = act.find_element(By.CLASS_NAME, "gga_cr_pres").text
                            except:
                                actividad["presencialidad"] = None
                        try:
                            actividad["duracion"] = act.find_element(By.CLASS_NAME, "gga_cr_dur").text
                        except:
                            actividad["duracion"] = None
                        actividades.append(actividad)
                    week_data[activity_types[col]] = actividades
                except:
                    week_data[activity_types[col]] = []

            if "cronograma" not in data.keys():
                data["cronograma"] = []
            data["cronograma"]  = data["cronograma"] + [week_data]

        return data

    '''TOREMOVE
            def __extract_evaluation(self, driver, url):
                driver.get(url)

                # -------
                tipos_actividad = ["progresiva", "global", "extraordinaria"]
                actividades = []
                caja_actividades = driver.find_elements(By.CLASS_NAME, "caja")[0]
                evaluation_tables = caja_actividades.find_elements(By.TAG_NAME, "table")
                for evaluation_table in evaluation_tables:
                    tipo_actual = tipos_actividad[evaluation_tables.index(evaluation_table)]
                    filas = evaluation_table.find_elements(By.CSS_SELECTOR, "tbody tr")

                    for fila in filas:
                        tds = fila.find_elements(By.TAG_NAME, "td")
                        if not tds:
                            continue
                        actividad = {"tipo_evaluacion": tipo_actual}
                        # Con semana (8 columnas)
                        if len(tds) == 8:
                            self.__extract_evaluation_activities_t1(actividad, tds)
                        # Sin semana (7 columnas)
                        elif len(tds) == 7:
                            self.__extract_evaluation_activities_t2(actividad, tds)
                        else:
                            print("odd case in the __extract_evaluation")
                            continue
                        actividades.append(actividad)
                #-------
                # Extraer criterios
                try:
                    criterios_div = driver.find_element(By.ID, "gga_ce_denominacion").find_element(By.XPATH, "following-sibling::div")
                    criterios_texto = criterios_div.text.strip()
                except:
                    print("error extracting criterion")
                    criterios_texto = ""

                return { "evaluacion" : {  "actividades": actividades, "criterios_evaluacion": criterios_texto  }}

                '''

    def __extract_evaluation_activities_t1(self, actividad, tds):
        actividad["semana"] = tds[0].text.strip()
        actividad["descripcion"] = tds[1].text.strip()
        actividad["modalidad"] = tds[2].text.strip()
        actividad["tipo"] = tds[3].text.strip()
        actividad["duracion"] = tds[4].text.strip()
        actividad["peso"] = tds[5].text.strip()
        actividad["nota_minima"] = tds[6].text.strip()
        actividad["competencias"] = [
            li.text.strip() for li in tds[7].find_elements(By.TAG_NAME, "li")
        ]

    def __extract_evaluation_activities_t2(self, actividad, tds):
        actividad["semana"] = None
        actividad["descripcion"] = tds[0].text.strip()
        actividad["modalidad"] = tds[1].text.strip()
        actividad["tipo"] = tds[2].text.strip()
        actividad["duracion"] = tds[3].text.strip()
        actividad["peso"] = tds[4].text.strip()
        actividad["nota_minima"] = tds[5].text.strip()
        actividad["competencias"] = [
            li.text.strip() for li in tds[6].find_elements(By.TAG_NAME, "li")
        ]

    def __extract_evaluation(self, driver, url):
            driver.get(url)
    
            # -------
            actividades = []
            tipos_actividad = ["progresiva", "global", "extraordinaria"]
            # Solo procesar tablas (las primeras 3 secciones)
            tablas = driver.find_elements(By.CSS_SELECTOR, "table.tabla_recursos")
            for tabla in tablas:
                tipo_actual = tipos_actividad[tablas.index(tabla)]
                filas = tabla.find_elements(By.CSS_SELECTOR, "tbody tr")
    
                for fila in filas:
                    tds = fila.find_elements(By.TAG_NAME, "td")
                    if not tds:
                        continue
                    actividad = { "tipo_evaluacion": tipo_actual  }
                    # Con semana (8 columnas)
                    if len(tds) == 8:
                        self.__extract_evaluation_activities_t1(actividad, tds)
                    # Sin semana (7 columnas)
                    elif len(tds) == 7:
                        self.__extract_evaluation_activities_t2(actividad, tds)
                    else:
                        print("odd case in the __extract_evaluation")
                        continue
                    actividades.append(actividad)
            #-------
            # Extraer criterios
            try:
                criterios_div = driver.find_element(By.ID, "gga_ce_denominacion").find_element(By.XPATH, "following-sibling::div")
                criterios_texto = criterios_div.text.strip()
            except:
                print("error extracting criterion")
                criterios_texto = ""
    
            return { "evaluacion" : {  "actividades": actividades, "criterios_evaluacion": criterios_texto  }}

    def __extract_resource(self, driver, url):
        driver.get(url)
        time.sleep(1)
        # Data extraction
        result = []
        tabla = driver.find_element(By.CLASS_NAME, "tabla_recursos")
        filas = tabla.find_element(By.TAG_NAME, "tbody").find_elements(By.TAG_NAME, "tr")

        for fila in filas:
            columnas = fila.find_elements(By.TAG_NAME, "td")
            if len(columnas) == 3:
                nombre = columnas[0].text.strip()
                tipo = columnas[1].text.strip()
                descripcion = columnas[2].text.strip()
                recurso = {
                    "nombre": nombre,
                    "tipo": tipo,
                    "descripcion": descripcion
                }
                result.append(recurso)
        return { "recursos_didacticos" : result }


    def __extract_other_info(self, driver, url):
        driver.get(url)
        time.sleep(1)
        # Data extraction

        result = {}

        # Extraer secciones principales
        secciones = driver.find_elements(By.CLASS_NAME, "vista")
        cajas = driver.find_elements(By.CLASS_NAME, "caja")

        for seccion, caja in zip(secciones, cajas):
            titulo_seccion = seccion.text.strip()
            contenido = caja.text.strip()
            result[titulo_seccion] = contenido

        return result


    def __save_results(self, row, merged, errors):
        file_name = str(row.subject_code) + "-" + str(row.study_plan_code) + "-" + str(row.academic_year) + ".json"
        with open("./guides_data/" + file_name, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=4)
        with open("./guides_data/errors.csv", "a", encoding="utf-8") as f:
            for line in errors:
                f.write(line + "\n")
            json.dump(errors, f, ensure_ascii=False, indent=4)

    def __new_tab_record_extraction(self, row):

        # DONE: cache, if file exists do not download it again
        file_name = "./guides_data/"+str(row.subject_code) + "-" + str(row.study_plan_code) + "-" + str(row.academic_year) + ".json"
        if os.path.exists(file_name):
            print("Skipping ", file_name)
            return


        driver = self.login()
        subject_code = row.subject_code
        code = str(row.academic_year) + "-" + str(row.study_plan_code) + "-" + str(row.subject_code)
        merged = {}
        errors = []
        description_json = {}
        professors_json = {}
        requirements_json = {}
        competences_and_results_json = {}
        syllabus_json = {}
        schedule_json = {}
        evaluation_json = {}
        resources_json = {}
        other_info = {}
        try:
            description_json = self.__extract_description(driver, row.info_description_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][description_json][" + code + "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            professors_json = self.__extract_professors(driver, row.info_professors_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][professors_json][" +code + "]: ", e)
            errors.append(code+ " : " + str(e))
        try:
            requirements_json = self.__extract_requirements(driver, row.info_prev_requirements_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][requirements_json][" + code+ "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            competences_and_results_json = self.__extract_competentences_and_results(driver, row.info_competences_and_results_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][competences_and_results_json][" + code + "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            syllabus_json = self.__extract_syllabus(driver, row.info_syllabus_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][syllabus_json][" + code + "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            schedule_json = self.__extract_schedule(driver, row.info_schedule_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][schedule_json][" + code + "]: ", e)
            errors.append(code+" : " + str(e))
        try:
            evaluation_json = self.__extract_evaluation(driver, row.info_evaluation_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][evaluation_json][" +code + "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            resources_json = self.__extract_resource(driver, row.info_resources_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][resources_json][" + code + "]: ", e)
            errors.append(code + " : " + str(e))
        try:
            other_info = self.__extract_other_info(driver, row.info_other_url)
        except Exception as e:
            print("Exception occurred [__new_tab_record_extraction][other_info][" +code + "]: ", e)
            errors.append(code + " : " + str(e))
        merged = {**description_json, **professors_json, **requirements_json, **competences_and_results_json, **syllabus_json, **schedule_json, **evaluation_json, **resources_json, **other_info}

        self.__save_results(row, merged, errors)
        driver.quit()


    def extract_structured_json(self, index_file="gauss-index.csv", local_index=True, years=None, study_plan_code=None):
        global KG_EXTRACTOR_WORKERS
        if not local_index:
            print("Please run first the method build_gauss_index()")
        else:
            df = pd.read_csv(index_file)
            if study_plan_code:
                df = df.loc[df['study_plan_code'] == study_plan_code]
            if years:
                df = df.loc[df['academic_year'] == years]
            with ThreadPoolExecutor(max_workers=KG_EXTRACTOR_WORKERS) as executor:
                executor.map(self.__new_tab_record_extraction, df.itertuples(index=False))


    def dowload_pdf(self, row):
        try:
            file_name = "./guides_data/" + str(row.subject_code) + "-" + str(row.study_plan_code) + "-" + str(
                row.academic_year) + ".pdf"

            time.sleep(0.5)

            download_link = "https://www.upm.es/comun_gauss/publico/guias/"+str(row.academic_year)+"/"+str(row.semester)+"/GA_"+str(row.study_plan_code)+"_"+str(row.subject_code)+"_"+str(row.semester)+"_"+str(row.academic_year)+".pdf"
            response = requests.get(download_link)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
            else:
                print('Failed to download file: ', download_link)
        except Exception as e:
            print(e, " -> ", row.guide_pdf_url)



    def download_pdfs(self, index_file ="gauss-index.csv", local_index=True, years=None, study_plan_code=None):
        if not local_index:
            print("Please run first the method build_gauss_index()")
        else:
            df = pd.read_csv(index_file)
            if study_plan_code:
                df = df.loc[df['study_plan_code'] == study_plan_code]
            if years:
                df = df.loc[df['academic_year'] == years]
            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(self.dowload_pdf, df.itertuples(index=False))





if __name__ == '__main__':
    print("Indexing gauss, be sure to be connected to the UPM vpn")
    print("No personal data will be stored anyhow")
    username= input("type gauss username: ")
    password= input("Type gauss password: ")

    indexer = GaussIndexer(username, password)
    #df = indexer.build_gauss_index(only_last_year=False)
    #print("-------")
    #print(df)
    #df.to_csv("./all2-gauss-index.csv", index=False, encoding="utf-8")
    #indexer.extract_structured_json()
    # pdf downloader
    indexer.download_pdfs(years="2025-26")