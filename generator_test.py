import generator
import generator_utils
import operator


def test_extract_variables():
    query = 'select distinct(?x) ?y where { ?x a C . ?x a ?y }'
    query2 = 'select distinct ?a where'

    result = generator_utils.extract_variables(query)
    result2 = generator_utils.extract_variables(query2)

    assert result == ['x', 'y']
    assert result2 == ['a']


def test_single_resource_sort():
    matches = [{'usages': [17]}, {'usages': [0]}, {'usages': [3]}, {'usages': [2]}, {'usages': [1]}]

    result = sorted(matches, key=generator.prioritize_usage)

    assert map(operator.itemgetter(0), map(operator.itemgetter('usages'), result)) == [17, 3, 2, 1, 0 ]


def test_couple_resource_sort():
    matches = [{'usages': [17, 2]}, {'usages': [0, 0]}, {'usages': [3, 2]}, {'usages': [2, 2]}, {'usages': [1, 2]}]

    result = sorted(matches, key=generator.prioritize_usage)

    assert map(operator.itemgetter('usages'), result) == [[17, 2], [3, 2], [2, 2], [1, 2], [0, 0] ]


def test_samplify_query():
    query = 'select distinct ?a, ?b, ?c where { ?b <http://dbpedia.org/property/debutteam> ?uri . ?a <http://dbpedia.org/property/debutteam> ?uri . \
               ?c <http://dbpedia.org/property/debutteam> ?uri }'
    variables = ['a', 'b', 'c']

    result = generator.use_sample(query, variables)

    assert result ==  'select ?a, SAMPLE(?b), SAMPLE(?c) where { ?b <http://dbpedia.org/property/debutteam> ?uri . ?a <http://dbpedia.org/property/debutteam> ?uri . \
               ?c <http://dbpedia.org/property/debutteam> ?uri } GROUP BY ?a'