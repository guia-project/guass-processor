# Notas para el white paper de GUIA

En lugar de trabajar sobre gauss, vamos a asumir un sistema federado y distribuido de vocabularios para cada universidad.  Se puede hablar de calidad del dato donde 0 es tener solo los PDFs, 1 tener datos estructurtados (no completos, hay cosas en los pdfs que no estan en el estructurado), 2 tener datos estructurados completos, 3 tener datos interoperables (RDF+Vocabulario), 4 tener los datos accesbiles, 5 accesibles publicos, 6 datos con licencia, etc. 

De cara a la interoperabilidad, vamos a definir una ontologia comun de consenso para que si las universidades tuvieran una ontologia en lugar de hacer pares entre ellas de equivalencia se usa esta ontologia core nuestra para hacer un traverse equivalence entre ellas. UNa universidad tiene el termino Asignatura y otra Materia y ambas se mapean al cepto Subject de la ontologia core como equivalentes. Por transitividad por tanto Asignatura y Materia son equivalentes.

Por otro lado, la plataforma guia no se si tiene sentido que sea un CKAN con los PDFs ya que no aportan tanto, quizas es mejor una plataforma orientada a servicios de utilidad.
Por ejemplo, uno para rellenar las guias con el vocabulario que se ofrece y que permita exportar a PDF y a RDF (para poder trabajar con los servicios de IA). 

Si una universidad ya posee las guias en PDF (basico) se puede crear un servicio que usando la ontologia auto-rellena en la plataforma de las guias los datos y un humano luego los valida (obteniendo el RDF). Alternativamente se puede trabjar con una version no supervisada.

## Propuestas

* Web para rellenar guias anotado con RDFa y la ontología común. La web debe permitir generar un PDF y dar la posibilidad de personalizar la plantilla de salida.

## Problemas

* Detectar si existe un cambio (relevante) de un año a otro en una guia
* Comparación de similitud en:
  * Syllabus (temario)
  * Compentencias
  * Resultados de aprendizaje