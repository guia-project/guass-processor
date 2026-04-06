from __future__ import annotations

from scrappers.GaussLogableScrapper import GaussLoginScrapper
''' mandatory imports used by eval function '''
from scrappers.subjects_reports.extract_annexes import extract_annexes
from scrappers.subjects_reports.extract_descriptive_data import extract_descriptive_data
from scrappers.subjects_reports.extract_past_improvements import extract_past_improvements
from scrappers.subjects_reports.extract_evaluation import extract_evaluation
from scrappers.subjects_reports.extract_results_kpis import extract_results_kpis
from scrappers.subjects_reports.extract_subjects_coordination import extract_subjects_coordination
from scrappers.subjects_reports.extract_next_improvements import extract_next_improvements
from scrappers.subjects_reports.extract_final_considerations import extract_final_considerations






class GaussDegreeReportsScrapper(GaussLoginScrapper):

    def __init__(self, username, password, extractor_workers=1, debug_html=False, directory="./reports_data", tab_delay=0.5):
        super().__init__(username=username, password=password, extractor_workers=extractor_workers, debug_html=debug_html, directory=directory, tab_delay=tab_delay, suffix="-report-")
        base_uri= "https://www.upm.es/gauss/principal.upm/informes_titulacion/consulta/consulta-informes_titulacion/{year}/{short_code}/anexos"

        self.__uri_annexes = base_uri+"/anexos"
        self.__uri_descriptive_data = base_uri+"/datos-descriptivos"
        self.__uri_academic_assessment = base_uri + "/valoracion-academica"
        self.__uri_general_assessment = base_uri + "/valoracion-general"
        self.__uri_quality_assessment = base_uri + "/calidad"
        self.__uri_previous_improvements = base_uri + "/mejoras-previas"
        self.__uri_strengths_weaknesses = base_uri + "/fortalezas-debilidades"
        self.__uri_next_improvements = base_uri + "/mejoras-siguientes"



    def __build_uri(self, uri,  year, study_plan_code) :
        return uri.replace("{year}", year).replace("{short_code}", study_plan_code)

    '''  Methods Override '''

    def _build_list_uris(self, row):
        year = str(row.academic_year)
        semester = str(row.semester)
        study_plan_code = str(row.study_plan_code)
        code = str(row.subject_code)
        uris = {}
        uris["anexos"] = (self.__build_uri(self.__uri_annexes, year, study_plan_code), 'extract_annexes')
        uris["datos-descriptivos"] = (self.__build_uri(self.__uri_descriptive_data, year, study_plan_code), None )
        uris["valoracion-academica"] = (self.__build_uri(self.__uri_academic_assessment, year, study_plan_code), None )
        uris["valoracion-general"] = (self.__build_uri(self.__uri_general_assessment, year, study_plan_code), None )
        uris["calidad"] = (self.__build_uri(self.__uri_quality_assessment, year, study_plan_code), None )
        uris["mejoras-previas"] = (self.__build_uri(self.__uri_previous_improvements, year, study_plan_code), None )
        uris["fortalezas-debilidades"] = (self.__build_uri(self.__uri_strengths_weaknesses, year, study_plan_code), None )
        uris["mejoras-siguientes"] = (self.__build_uri(self.__uri_next_improvements, year, study_plan_code), None )
        return uris

    def get_file_name(self,  row, extension=".json"):
        print("here we are")
        return  str(row.subject_code) + "-" + str(row.study_plan_code) + "-" + str(row.academic_year) + self.__suffix + extension


    def _invoke_extraction_function(self, extraction_function, html_content):
        return eval(extraction_function)(html_content)




if __name__ == "__main__":
    USERNAME = ""
    PASSWORD = ""


    scraper = GaussDegreeReportsScrapper(
        username=USERNAME,
        password=PASSWORD,
        extractor_workers = 1,
        debug_html = True,
        directory = "../reports_degree_data",
        tab_delay = 0.5
    )
    scraper.extract_structured_json(subject_code=615001015)