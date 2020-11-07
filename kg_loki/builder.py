from typing import Optional, Sequence

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.configfile import ConfigFileRenderMulti, ConfigFileRender_Yaml, ConfigFileRender_RawStr
from kubragen.data import ValueData
from kubragen.exception import InvalidNameError
from kubragen.helper import QuotedStr
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem

from .configfile import LokiConfigFile
from .option import LokiOptions


class LokiBuilder(Builder):
    """
    Loki builder.

    Based on `Install Loki with Helm <https://grafana.com/docs/loki/latest/installation/helm/>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_CONFIG
          - creates Secret
        * - BUILD_SERVICE
          - creates deployments and services

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_CONFIG_SECRET
          - Secret
        * - BUILDITEM_SERVICE_HEADLESS
          - Service Headless
        * - BUILDITEM_SERVICE
          - Service
        * - BUILDITEM_STATEFULSET
          - StatefulSet

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - config-secret
          - Secret
          - ```<basename>-config-secret```
        * - service-headless
          - Service headless
          - ```<basename>-headless```
        * - service
          - Service
          - ```<basename>```
        * - statefulset
          - StatefulSet
          - ```<basename>```
        * - pod-label-app
          - label *app* to be used by selection
          - ```<basename>```
    """
    options: LokiOptions
    configfile: Optional[str]
    _namespace: str

    SOURCE_NAME = 'kg_Loki'

    BUILD_CONFIG: TBuild = 'config'
    BUILD_SERVICE: TBuild = 'service'

    BUILDITEM_CONFIG_SECRET: TBuildItem = 'config-secret'
    BUILDITEM_SERVICE_HEADLESS: TBuildItem = 'service-headless'
    BUILDITEM_SERVICE: TBuildItem = 'service'
    BUILDITEM_STATEFULSET: TBuildItem = 'statefulset'

    def __init__(self, kubragen: KubraGen, options: Optional[LokiOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = LokiOptions()
        self.options = options
        self.configfile = None

        self._namespace = self.option_get('namespace')

        self.object_names_update({
            'config-secret': self.basename('-config-secret'),
            'service-headless': self.basename('-headless'),
            'service': self.basename(),
            'statefulset': self.basename(),
            'pod-label-app': self.basename(),
        })

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> Sequence[TBuild]:
        return [self.BUILD_CONFIG, self.BUILD_SERVICE]

    def build_names_required(self) -> Sequence[TBuild]:
        return [self.BUILD_CONFIG, self.BUILD_SERVICE]

    def builditem_names(self) -> Sequence[TBuildItem]:
        return [
            self.BUILDITEM_CONFIG_SECRET,
            self.BUILDITEM_SERVICE_HEADLESS,
            self.BUILDITEM_SERVICE,
            self.BUILDITEM_STATEFULSET,
        ]

    def internal_build(self, buildname: TBuild) -> Sequence[ObjectItem]:
        if buildname == self.BUILD_CONFIG:
            return self.internal_build_config()
        elif buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_config(self) -> Sequence[ObjectItem]:
        ret = []

        ret.append(Object({
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': self.object_name('config-secret'),
                'namespace': self.namespace(),
            },
            'type': 'Opaque',
            'data': {
                'loki.yaml': self.kubragen.secret_data_encode(self.loki_configfile_get()),
            }
        }, name=self.BUILDITEM_CONFIG_SECRET, source=self.SOURCE_NAME, instance=self.basename()))

        return ret

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret = []

        ret.extend([
            Object({
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.object_name('service-headless'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('pod-label-app'),
                    }
                },
                'spec': {
                    'clusterIP': 'None',
                    'ports': [{
                        'port': self.option_get('config.service_port'),
                        'protocol': 'TCP',
                        'name': 'http-metrics',
                        'targetPort': 'http-metrics'
                    }],
                    'selector': {
                        'app': self.object_name('pod-label-app'),
                    }
                }
            }, name=self.BUILDITEM_SERVICE_HEADLESS, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': self.object_name('service'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('pod-label-app'),
                    },
                },
                'spec': {
                    'type': 'ClusterIP',
                    'ports': [{
                        'port': self.option_get('config.service_port'),
                        'protocol': 'TCP',
                        'name': 'http-metrics',
                        'targetPort': 'http-metrics'
                    }],
                    'selector': {
                        'app': self.object_name('pod-label-app'),
                    },
                }
            }, name=self.BUILDITEM_SERVICE, source=self.SOURCE_NAME, instance=self.basename()),
            Object({
                'apiVersion': 'apps/v1',
                'kind': 'StatefulSet',
                'metadata': {
                    'name': self.object_name('statefulset'),
                    'namespace': self.namespace(),
                    'labels': {
                        'app': self.object_name('pod-label-app'),
                    },
                },
                'spec': {
                    'podManagementPolicy': 'OrderedReady',
                    'replicas': 1,
                    'selector': {
                        'matchLabels': {
                            'app': self.object_name('pod-label-app'),
                        }
                    },
                    'serviceName': self.object_name('service-headless'),
                    'updateStrategy': {
                        'type': 'RollingUpdate'
                    },
                    'template': {
                        'metadata': {
                            'labels': {
                                'app': self.object_name('pod-label-app'),
                            },
                            'annotations': ValueData({
                                'prometheus.io/scrape': QuotedStr('true'),
                                'prometheus.io/port': QuotedStr('http-metrics'),
                            }, enabled=self.option_get('config.prometheus_annotation') is not False),
                        },
                        'spec': {
                            'serviceAccountName': ValueData(self.option_get('config.authorization.serviceaccount_use'),
                                                            disabled_if_none=True),
                            'securityContext': {
                                'fsGroup': 10001,
                                'runAsGroup': 10001,
                                'runAsNonRoot': True,
                                'runAsUser': 10001
                            },
                            'containers': [{
                                'name': 'loki',
                                'image': self.option_get('container.loki'),
                                'args': [
                                    '-config.file=/etc/loki/loki.yaml'
                                ],
                                'volumeMounts': [{
                                    'name': 'config',
                                    'mountPath': '/etc/loki'
                                },
                                {
                                    'name': 'storage',
                                    'mountPath': '/data',
                                    'subPath': None
                                }],
                                'ports': [{
                                    'name': 'http-metrics',
                                    'containerPort': 3100,
                                    'protocol': 'TCP'
                                }],
                                'livenessProbe': {
                                    'httpGet': {
                                        'path': '/ready',
                                        'port': 'http-metrics'
                                    },
                                    'initialDelaySeconds': 45
                                },
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/ready',
                                        'port': 'http-metrics'
                                    },
                                    'initialDelaySeconds': 45
                                },
                                'securityContext': {
                                    'readOnlyRootFilesystem': True
                                },
                                'resources': ValueData(value=self.option_get('kubernetes.resources.statefulset'),
                                                       disabled_if_none=True),
                            }],
                            'terminationGracePeriodSeconds': 4800,
                            'volumes': [{
                                'name': 'config',
                                'secret': {
                                    'secretName': self.object_name('config-secret'),
                                    'items': [{
                                        'key': 'loki.yaml',
                                        'path': 'loki.yaml',
                                    }]
                                }
                            },
                            KDataHelper_Volume.info(base_value={
                                'name': 'storage',
                            }, value=self.option_get('kubernetes.volumes.data'))]
                        }
                    }
                }
            }, name=self.BUILDITEM_STATEFULSET, source=self.SOURCE_NAME, instance=self.basename()),
        ])

        return ret

    def loki_configfile_get(self) -> str:
        if self.configfile is None:
            configfile = self.option_get('config.loki_config')
            if configfile is None:
                configfile = LokiConfigFile()
            if isinstance(configfile, str):
                self.configfile = configfile
            else:
                configfilerender = ConfigFileRenderMulti([
                    ConfigFileRender_Yaml(),
                    ConfigFileRender_RawStr()
                ])
                self.configfile = configfilerender.render(configfile.get_value(self))
        return self.configfile
