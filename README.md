# KubraGen Builder: Loki

[![PyPI version](https://img.shields.io/pypi/v/kg_loki.svg)](https://pypi.python.org/pypi/kg_loki/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_loki.svg)](https://pypi.python.org/pypi/kg_loki/)

kg_loki is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [Grafana Loki](https://grafana.com/oss/loki/) service in Kubernetes.

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

* Website: https://github.com/RangelReale/kg_loki
* Repository: https://github.com/RangelReale/kg_loki.git
* Documentation: https://kg_loki.readthedocs.org/
* PyPI: https://pypi.python.org/pypi/kg_loki

## Example

```python
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_ShellScript, OutputFile_Kubernetes, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_loki import LokiBuilder, LokiOptions, LokiConfigFile, LokiConfigFileOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: loki
#
lokiconfigfile = LokiConfigFile(options=LokiConfigFileOptions({
}))

loki_config = LokiBuilder(kubragen=kg, options=LokiOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'myloki',
    'config': {
        'loki_config': lokiconfigfile,
    },
    'kubernetes': {
        'volumes': {
            'data': {
                'persistentVolumeClaim': {
                    'claimName': 'loki-storage-claim'
                }
            }
        },
        'resources': {
            'statefulset': {
                'requests': {
                    'cpu': '150m',
                    'memory': '300Mi'
                },
                'limits': {
                    'cpu': '300m',
                    'memory': '450Mi'
                },
            },
        },
    }
}))

loki_config.ensure_build_names(loki_config.BUILD_CONFIG, loki_config.BUILD_SERVICE)

#
# OUTPUTFILE: loki-config.yaml
#
file = OutputFile_Kubernetes('loki-config.yaml')
out.append(file)

file.append(loki_config.build(loki_config.BUILD_CONFIG))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: loki.yaml
#
file = OutputFile_Kubernetes('loki.yaml')
out.append(file)

file.append(loki_config.build(loki_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-loki-config.yaml ********
apiVersion: v1
kind: Secret
metadata:
  name: myloki-config-secret
  namespace: app-monitoring
type: Opaque
data:
  loki.yaml: YXV0aF9lbmFibGVkOiBmYWxzZQppbmdlc3RlcjoKICBjaHVua19pZGxlX3BlcmlvZDogM20KICBjaHVua19ibG9ja19zaXplOiAyNjIxNDQKICBjaHVua19yZXRhaW5fcGVyaW9kOiAxbQogIG1heF90cmFuc2Zlcl9yZXRyaWVzOiAwCiAgbGlmZWN5Y2xlcjoKICAgIHJpbmc6CiAgICAgIGt2c3RvcmU6IHtzdG9yZTogaW5tZW1vcnl9CiAgICAgIHJlcGxpY2F0aW9uX2ZhY3RvcjogMQpsaW1pdHNfY29uZmlnOiB7ZW5mb3JjZV9tZXRyaWNfbmFtZTogZmFsc2UsIHJlamVjdF9vbGRfc2FtcGxlczogdHJ1ZSwgcmVqZWN0X29sZF9zYW1wbGVzX21heF9hZ2U6IDE2OGh9CnNjaGVtYV9jb25maWc6CiAgY29uZmlnczoKICAtIGZyb206IDIwMjAtMTAtMjQKICAgIHN0b3JlOiBib2x0ZGItc2hpcHBlcgogICAgb2JqZWN0X3N0b3JlOiBmaWxlc3lzdGVtCiAgICBzY2hlbWE6IHYxMQogICAgaW5kZXg6IHtwcmVmaXg6IGluZGV4XywgcGVyaW9kOiAyNGh9CnNlcnZlcjoge2h0dHBfbGlzdGVuX3BvcnQ6IDMxMDB9CnN0b3JhZ2VfY29uZmlnOgogIGJvbHRkYl9zaGlwcGVyOiB7YWN0aXZlX2luZGV4X2RpcmVjdG9yeTogL2RhdGEvbG9raS9ib2x0ZGItc2hpcHBlci1hY3RpdmUsIGNhY2hlX2xvY2F0aW9uOiAvZGF0YS9sb2tpL2JvbHRkYi1zaGlwcGVyLWNhY2hlLAogICAgY2FjaGVfdHRsOiAyNGgsIHNoYXJlZF9zdG9yZTogZmlsZXN5c3RlbX0KICBmaWxlc3lzdGVtOiB7ZGlyZWN0b3J5OiAvZGF0YS9sb2tpL2NodW5rc30KY2h1bmtfc3RvcmVfY29uZmlnOiB7bWF4X2xvb2tfYmFja19wZXJpb2Q6IDBzfQp0YWJsZV9tYW5hZ2VyOiB7cmV0ZW50aW9uX2RlbGV0ZXNfZW5hYmxlZDogZmFsc2UsIHJldGVudGlvbl9wZXJpb2Q6IDBzfQpjb21wYWN0b3I6IHt3b3JraW5nX2RpcmVjdG9yeTogL2RhdGEvbG9raS9ib2x0ZGItc2hpcHBlci1jb21wYWN0b3IsIHNoYXJlZF9zdG9yZTogZmlsZXN5c3RlbX0K

****** END FILE: 002-loki-config.yaml ********
****** BEGIN FILE: 003-loki.yaml ********
apiVersion: v1
kind: Service
metadata:
  name: myloki-headless
  namespace: app-monitoring
  labels:
    app: myloki
spec:
  clusterIP: None
  ports:
  - port: 3100
    protocol: TCP
    name: http-metrics
    targetPort: http-metrics
  selector:
    app: myloki
---
apiVersion: v1
kind: Service
metadata:
  name: myloki
  namespace: app-monitoring
  labels:
    app: myloki
<...more...>
****** END FILE: 003-loki.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-loki-config.yaml
kubectl apply -f 003-loki.yaml

****** END FILE: create_gke.sh ********
```

## Credits

based on

[Install Loki with Helm](https://grafana.com/docs/loki/latest/installation/helm/)

## Author

Rangel Reale (rangelspam@gmail.com)
