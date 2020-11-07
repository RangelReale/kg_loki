import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_loki import LokiBuilder, LokiOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        loki_config = LokiBuilder(kubragen=self.kg)
        self.assertEqual(loki_config.object_name('config-secret'), 'loki-config-secret')
        self.assertEqual(loki_config.object_name('statefulset'), 'loki')

    def test_basedata(self):
        loki_config = LokiBuilder(kubragen=self.kg, options=LokiOptions({
            'namespace': 'myns',
            'basename': 'myloki',
            'kubernetes': {
                'volumes': {
                    'data': {
                        'emptyDir': {},
                    }
                }
            }
        }))
        self.assertEqual(loki_config.object_name('config-secret'), 'myloki-config-secret')
        self.assertEqual(loki_config.object_name('statefulset'), 'myloki')

        FilterJSONPatches_Apply(items=loki_config.build(loki_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[loki_config.BUILDITEM_SERVICE]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'myloki'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
