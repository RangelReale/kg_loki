from typing import Optional, Any, Mapping, Sequence

from kubragen.configfile import ConfigFile
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.option import OptionDef, OptionDefFormat
from kubragen.options import Options


class LokiOptions(Options):
    """
    Options for the Loki builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```loki```
        * - namespace
          - namespace
          - str
          - ```loki```
        * - config |rarr| prometheus_annotation
          - add prometheus annotations
          - bool
          - ```False```
        * - config |rarr| loki_config
          - Loki config file
          - str, ConfigFile
          - :class:`LokiConfigFile`
        * - config |rarr| service_port
          - Service port
          - int
          - 3100
        * - container |rarr| loki
          - loki container image
          - str
          - ```grafana/loki:<version>```
        * - kubernetes |rarr| volumes |rarr| data
          - Kubernetes data volume
          - dict, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - kubernetes |rarr| resources |rarr| statefulset
          - Kubernetes StatefulSet resources
          - dict
          -
    """
    def define_options(self) -> Optional[Any]:
        """
        Declare the options for the Loki Stack builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='loki', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='loki', allowed_types=[str]),
            'config': {
                'prometheus_annotation': OptionDef(required=True, default_value=False, allowed_types=[bool]),
                'loki_config': OptionDef(allowed_types=[str, ConfigFile]),
                'service_port': OptionDef(required=True, default_value=3100, allowed_types=[int]),
                'authorization': {
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                },
            },
            'container': {
                'loki': OptionDef(required=True, default_value='grafana/loki:2.0.0', allowed_types=[str]),
            },
            'kubernetes': {
                'volumes': {
                    'data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                      allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                },
                'resources': {
                    'statefulset': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
