from __future__ import annotations

from scrappers.GaussLogableScrapper import GaussLoginScrapper
''' mandatory imports used by eval function '''



class GaussReportsScrapper(GaussLoginScrapper):

    def __init__(self, username, password, extractor_workers=1, debug_html=False, directory="./reports_data", tab_delay=0.5):
        super().__init__(username=username, password=password, extractor_workers=extractor_workers, debug_html=debug_html, directory=directory, tab_delay=tab_delay)
        base_uri= "https://www.upm.es/gauss/principal.upm/informes_asignatura/consulta/consulta-informes_asignatura/{year}/{semester}/{short_code}/{code}/2"
        self.__uri_annexes = base_uri+"/anexos"
        self.__uri_descriptive_data = base_uri+"/datos-descriptivos"
        self.__uri_improvements = base_uri + "/mejoras-previas"
        self.__uri_evaluation_description = base_uri + "/evaluacion"
        self.__uri_results_kpis = base_uri + "/tasas"
        self.__uri_coordination = base_uri + "/coordinacion-asignaturas"
        self.__uri_next_improvements = base_uri + "/mejoras"
        self.__uri_final_considerations = base_uri + "/consideraciones"



    def __build_uri(self,uri,  year, semester, study_plan_code, code) :
        return uri.replace("{year}", year).replace("{semester}", semester).replace("{short_code}", study_plan_code).replace("{code}", code)

    '''  Methods Override '''

    def _build_list_uris(self, year, semester, study_plan_code, code):
        uris = {}
        uris["anexos"] = (self.__build_uri(self.__uri_annexes, year, semester, study_plan_code, code), 'extract_annexes')
        uris["datos-descriptivos"] = (self.__build_uri(self.__uri_descriptive_data, year, semester, study_plan_code, code), 'extract_descriptive_data' )
        uris["mejoras-previas"] = (self.__build_uri(self.__uri_improvements, year, semester, study_plan_code, code), 'extract_past_improvements' )
        uris["evaluacion"] = (self.__build_uri(self.__uri_evaluation_description, year, semester, study_plan_code, code), 'extract_evaluation' )
        uris["tasas"] = (self.__build_uri(self.__uri_results_kpis, year, semester, study_plan_code, code), 'extract_results_kpis' )
        uris["coordinacion-asignaturas"] = (self.__build_uri(self.__uri_coordination, year, semester, study_plan_code, code), 'extract_subjects_coordination' )
        uris["mejoras"] = (self.__build_uri(self.__uri_next_improvements, year, semester, study_plan_code, code), 'extract_next_improvements' )
        uris["consideraciones"] = (self.__build_uri(self.__uri_final_considerations, year, semester, study_plan_code, code), 'extract_final_considerations' )
        return uris

    def _invoke_extraction_function(self, extraction_function, html_content):
        return eval(extraction_function)(html_content)




if __name__ == "__main__":
    USERNAME = ""
    PASSWORD = ""


    scraper = GaussReportsScrapper(
        username=USERNAME,
        password=PASSWORD,
        extractor_workers = 1,
        debug_html = True,
        directory = "../reports_data",
        tab_delay = 0.5
    )
    scraper.extract_structured_json(years="2024-25")#subject_code=615001015)