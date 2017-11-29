import argparse
import collections
import re
import sys

from pyparsing import ParseException
from rdflib.plugins.sparql import parser

from generator_utils import decode, extract_entities


def analyse( translation ):
    result = {}
    for test in TESTS:
        result[test] = TESTS[test](translation)
    return result


def validate( translation ):
    _, query = translation
    # rdflib parser does not accept parantheses in URIs
    rdflib_parser_valid_parentheses_open = '\('
    rdflib_parser_valid_parentheses_close = '\)'
    query = query.replace('(', rdflib_parser_valid_parentheses_open)
    query = query.replace(')', rdflib_parser_valid_parentheses_close)
    try:
        parser.parseQuery(query)
    except ParseException as exception:
        print '{} in "{}", loc: {}'.format(exception.msg, exception.line, exception.loc)
        details['parse_exception'].update([exception.msg])
        return False
    else:
        return True


def check_type( translation ):
    target, generated = translation
    target_type = extract_type(target)
    return target_type == extract_type(generated) and target_type is not None


def extract_type( query ):
    result_description = extract_result_description(query)
    types = ['ask', 'describe', 'select']
    for query_type in types:
        match = re.search(query_type, result_description, re.IGNORECASE)
        if match:
            return query_type
    return None


def extract_result_description (sparqlQuery):
    selectStatementPattern = r'(.*?)\swhere'
    selectStatementMatch = re.search(selectStatementPattern, sparqlQuery, re.IGNORECASE)
    if selectStatementMatch:
        return selectStatementMatch.group(1)
    return ''


def check_entities ( translation ):
    target, generated = translation
    entities = extract_entities(target)
    entities_detected = map(lambda entity : entity in generated, entities)
    if all(entities_detected):
        return True

    if any(entities_detected):
        details['partly_detected_entities'].update([True])

    details['undetected_entity'].update(map(lambda (entity, detected) : entity, filter(lambda (entity, detected) : not detected, zip(entities, entities_detected))))
    return False


def summarise( summary, current_evaluation ):
    for test in TESTS:
        test_result = current_evaluation[test]
        summary[test].update([test_result])
    return summary


def log_summary( summary, details, org_file, ask_output_file ):
    print '\n\nSummary\n'
    print 'Analysis based on {} and {}'.format(org_file, ask_output_file)
    for test in TESTS:
        print '{:30}: {:6d} True / {:6d} False'.format(test, summary[test][True], summary[test][False])
    print '\n\nDetails\n'
    for detail in details:
        for key in details[detail]:
            print '{:30}: {:6d} {}'.format(detail, details[detail][key], key)


def read( file_name ):
    with open(file_name) as file:
        questions = file.readlines()
    return questions


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    requiredNamed = arg_parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('--target', dest='target', metavar='test.sparql', help='encoded sparql queries', required=True)
    requiredNamed.add_argument('--generated', dest='generated', metavar='nmt/output.txt', help='direct (encoded) NSpM output', required=True)
    args = arg_parser.parse_args()

    targets_file = args.target
    ask_output_file = args.generated

    reload(sys)
    sys.setdefaultencoding("utf-8")

    TESTS = {
        'valid_sparql': validate,
        'correct_query_type': check_type,
        'entities_detected': check_entities
    }

    details = {
        'parse_exception': collections.Counter(),
        'undetected_entity': collections.Counter(),
        'partly_detected_entities': collections.Counter()
    }

    encoded_targets = read(targets_file)
    encoded_generated = read(ask_output_file)

    if len(encoded_targets) != len(encoded_generated):
        print 'Some translations are missing'
        sys.exit(1)

    targets = map(decode, encoded_targets)
    generated = map(decode, encoded_generated)
    translations = zip(targets, generated)
    evaluation = map(analyse, translations)
    summary_obj = {}
    for test in TESTS:
        summary_obj[test] = collections.Counter()

    summary = reduce(summarise, evaluation, summary_obj)
    log_summary(summary, details, targets_file, ask_output_file)