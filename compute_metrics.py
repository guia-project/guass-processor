from rdflib import Graph
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score
from typing import Set, Tuple, List, Optional, Dict, Any

Triple = Tuple[str, str, str]

queries = [
    { 'eval' : 'ont', 'name' : 'O# T', 'query' : 'SELECT DISTINCT ?type WHERE { ?subject a ?type }'}, # types
    { 'eval' : 'ont', 'name' : 'O# DP', 'query' : 'SELECT DISTINCT ?predicate WHERE { ?subject ?predicate ?value . FILTER(isLiteral(?value)) .}'}, #DP
    {'eval'  : 'ont', 'name' : 'O# OP', 'query': 'SELECT DISTINCT ?predicate WHERE { ?subject ?predicate ?value . FILTER(!isLiteral(?value)) .}'},  # DP
    { 'eval' : 'evaluate_count', 'name' : 'N# T', 'query' : 'SELECT ?type (COUNT (DISTINCT ?subject) AS ?number) WHERE { ?subject a ?type } GROUP BY ?type'}, # types
    { 'eval' : 'evaluate_count', 'name' : 'N# DP', 'query' : 'SELECT ?predicate (COUNT (DISTINCT ?subject) AS ?number) WHERE { ?subject ?predicate ?value .} GROUP BY ?predicate'}, # predicates
    { 'eval' : '', 'name'  : 'N# TOPT (relations)', 'query': 'SELECT ?type_1 ?op ?type_2 WHERE { ?subject_1 a ?type_1 . ?subject_2 a ?type_2 . ?subject_1 ?op ?subject_2 }'}, # correct relationships materialized between types
    { 'eval' : '', 'name' : 'N# DPL (values)', 'query' : 'SELECT ?predicate ?raw_value WHERE { ?subject ?predicate ?value . FILTER(isLiteral(?value)) . BIND( str(?value) AS ?raw_value)}'}, # correct values (not checking lang or xsd)
    { 'eval' : '', 'name' : 'N# DPLExact (exact values)', 'query' : 'SELECT ?predicate ?value WHERE { ?subject ?predicate ?value . FILTER(isLiteral(?value)) . }'}, # correct exact values (checking lang or xsd)
    { 'eval' : '', 'name' : 'N# Exact Triplets', 'query' : 'SELECT DISTINCT * WHERE { ?subject ?predicate ?value . }'} # correct exact triples
]

def load_rdf_triples(path, rdf_format = None) :
    """
    Carga un fichero RDF y devuelve un conjunto de tripletas normalizadas como strings.
    """
    read_graph = Graph()
    read_graph.parse(path, format=rdf_format)
    return read_graph

def run_query(graph, query):
    query_results = graph.query(query)
    results = set()
    for row in query_results:
        results.add(row)
    return results

def compute_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

def evaluate_exact_match(gold: Set[Triple], pred: Set[Triple]) -> Dict[str, Any]:
    """
    Evalúa predicciones RDF frente al gold standard usando matching exacto.
    """
    tp_set = gold & pred
    fp_set = pred - gold
    fn_set = gold - pred

    tp = len(tp_set)
    fp = len(fp_set)
    fn = len(fn_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": tp_set,
        "false_positives": fp_set,
        "false_negatives": fn_set,
    }


def find(uri_set, uri):
    for uri_elem, uri_count in uri_set:
        if uri_elem == uri:
            return int(uri_count)
    return None

def evaluate_count(gold_qr, pred_qr):
    tp = 0
    fp = 0
    fn = 0
    fp_inst = []
    fn_inst = []
    # TP
    for grouping_item, count in gold_qr:
        gold_value = int(count)
        pred_value = find(pred_qr, grouping_item)
        if pred_value is None:
            # FN: meas exist in gold but does not exist in predicted
            fn += gold_value
            fn_inst.append((grouping_item, int(gold_value), 0))
        if pred_value is not None:
            if gold_value > pred_value:
                # False negative: there are more tp that generated
                tp += pred_value
                fn += gold_value - pred_value
                fn_inst.append((grouping_item, gold_value , pred_value))
            elif gold_value < pred_value:
                # False positive: more than in the gold where generated
                tp += gold_value
                fp += pred_value - gold_value
                fp_inst.append((grouping_item, gold_value, pred_value))
            else:
                # If equals generation and gold are perfect
                tp += gold_value

    for grouping_item_pred, count_pred in pred_qr:
        result = find(gold_qr, grouping_item_pred)
        if result is None:
            # means is generated in pred but does not exist in gold
            fp += int(count_pred)
            fp_inst.append((grouping_item_pred, 0, int(count_pred)))


    local_metrics = compute_metrics(tp, fp, fn)
    local_metrics["false_positives"] = fp_inst
    local_metrics["false_negatives"] = fn_inst
    return local_metrics

if __name__ == "__main__":
    gold_file = "./guides_data/615001065-61IW-2025-26.ttl"
    pred_file = "/Users/andreacimmino/Desktop/course_graph.ttl"

    ontology = load_rdf_triples("/Users/andreacimmino/Downloads/guia.owl", rdf_format="turtle")
    gold_graph = load_rdf_triples(gold_file, rdf_format="turtle")
    pred_graph = load_rdf_triples(pred_file, rdf_format="turtle")

    metrics = {}
    for query_entry in queries:
        name = query_entry['name']
        query = query_entry['query']
        evaluation = query_entry['eval']

        gold_results  = run_query(gold_graph, query)
        predicted_results = run_query(pred_graph, query)
        if evaluation == 'evaluate_count':
            metrics[name] = evaluate_count(gold_results, predicted_results)

        elif evaluation == 'ont':
            gold_results  = run_query(ontology, query)
            metrics[name] = evaluate_exact_match(gold_results, predicted_results)
        else:
            metrics[name] = evaluate_exact_match(gold_results, predicted_results)

    for name, metric in metrics.items():
        print(name)
        print("tp: ",metric['tp']," fp: ", metric['fp'], " fn: ", metric['fn']," P: ",  metric['precision'], " R: ", metric['recall'], " F: ", metric['f1'])
        print(metric['false_positives'])
        print("-------------")
