# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import base64

import jmespath
import pytest
from chart_utils.helm_template_generator import render_chart


class TestPgbouncer:
    """Tests PgBouncer."""

    @pytest.mark.parametrize("yaml_filename", ["pgbouncer-deployment", "pgbouncer-service"])
    def test_pgbouncer_resources_not_created_by_default(self, yaml_filename):
        docs = render_chart(
            show_only=[f"templates/pgbouncer/{yaml_filename}.yaml"],
        )
        assert docs == []

    def test_should_create_pgbouncer(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}},
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("kind", docs[0]) == "Deployment"
        assert jmespath.search("metadata.name", docs[0]) == "release-name-pgbouncer"
        assert jmespath.search("spec.template.spec.containers[0].name", docs[0]) == "pgbouncer"

    def test_should_create_pgbouncer_service(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}},
            show_only=["templates/pgbouncer/pgbouncer-service.yaml"],
        )

        assert jmespath.search("kind", docs[0]) == "Service"
        assert jmespath.search("metadata.name", docs[0]) == "release-name-pgbouncer"
        assert jmespath.search('metadata.annotations."prometheus.io/scrape"', docs[0]) == "true"
        assert jmespath.search('metadata.annotations."prometheus.io/port"', docs[0]) == "9127"

        assert jmespath.search("metadata.annotations", docs[0]) == {
            "prometheus.io/scrape": "true",
            "prometheus.io/port": "9127",
        }

        assert {"name": "pgbouncer", "protocol": "TCP", "port": 6543} in jmespath.search(
            "spec.ports", docs[0]
        )
        assert {"name": "pgb-metrics", "protocol": "TCP", "port": 9127} in jmespath.search(
            "spec.ports", docs[0]
        )

    def test_pgbouncer_service_with_custom_ports(self):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True},
                "ports": {"pgbouncer": 1111, "pgbouncerScrape": 2222},
            },
            show_only=["templates/pgbouncer/pgbouncer-service.yaml"],
        )

        assert jmespath.search('metadata.annotations."prometheus.io/scrape"', docs[0]) == "true"
        assert jmespath.search('metadata.annotations."prometheus.io/port"', docs[0]) == "2222"
        assert {"name": "pgbouncer", "protocol": "TCP", "port": 1111} in jmespath.search(
            "spec.ports", docs[0]
        )
        assert {"name": "pgb-metrics", "protocol": "TCP", "port": 2222} in jmespath.search(
            "spec.ports", docs[0]
        )

    def test_pgbouncer_service_extra_annotations(self):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True, "service": {"extraAnnotations": {"foo": "bar"}}},
            },
            show_only=["templates/pgbouncer/pgbouncer-service.yaml"],
        )

        assert jmespath.search("metadata.annotations", docs[0]) == {
            "prometheus.io/scrape": "true",
            "prometheus.io/port": "9127",
            "foo": "bar",
        }

    def test_pgbouncer_service_static_cluster_ip(self):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True, "service": {"clusterIp": "10.10.10.10"}},
            },
            show_only=["templates/pgbouncer/pgbouncer-service.yaml"],
        )

        assert jmespath.search("spec.clusterIP", docs[0]) == "10.10.10.10"

    @pytest.mark.parametrize(
        "revision_history_limit, global_revision_history_limit",
        [(8, 10), (10, 8), (8, None), (None, 10), (None, None)],
    )
    def test_revision_history_limit(self, revision_history_limit, global_revision_history_limit):
        values = {
            "pgbouncer": {
                "enabled": True,
            }
        }
        if revision_history_limit:
            values["pgbouncer"]["revisionHistoryLimit"] = revision_history_limit
        if global_revision_history_limit:
            values["revisionHistoryLimit"] = global_revision_history_limit
        docs = render_chart(
            values=values,
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        expected_result = revision_history_limit or global_revision_history_limit
        assert jmespath.search("spec.revisionHistoryLimit", docs[0]) == expected_result

    def test_scheduler_name(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}, "schedulerName": "airflow-scheduler"},
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert (
            jmespath.search(
                "spec.template.spec.schedulerName",
                docs[0],
            )
            == "airflow-scheduler"
        )

    def test_should_create_valid_affinity_tolerations_and_node_selector(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "affinity": {
                        "nodeAffinity": {
                            "requiredDuringSchedulingIgnoredDuringExecution": {
                                "nodeSelectorTerms": [
                                    {
                                        "matchExpressions": [
                                            {"key": "foo", "operator": "In", "values": ["true"]},
                                        ]
                                    }
                                ]
                            }
                        }
                    },
                    "tolerations": [
                        {"key": "dynamic-pods", "operator": "Equal", "value": "true", "effect": "NoSchedule"}
                    ],
                    "nodeSelector": {"diskType": "ssd"},
                }
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert (
            jmespath.search(
                "spec.template.spec.affinity.nodeAffinity."
                "requiredDuringSchedulingIgnoredDuringExecution."
                "nodeSelectorTerms[0]."
                "matchExpressions[0]."
                "key",
                docs[0],
            )
            == "foo"
        )
        assert (
            jmespath.search(
                "spec.template.spec.nodeSelector.diskType",
                docs[0],
            )
            == "ssd"
        )
        assert (
            jmespath.search(
                "spec.template.spec.tolerations[0].key",
                docs[0],
            )
            == "dynamic-pods"
        )

    def test_no_existing_secret(self):
        docs = render_chart(
            "test-pgbouncer-config",
            values={
                "pgbouncer": {"enabled": True},
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.volumes[0]", docs[0]) == {
            "name": "pgbouncer-config",
            "secret": {"secretName": "test-pgbouncer-config-pgbouncer-config"},
        }

    def test_existing_secret(self):
        docs = render_chart(
            "test-pgbouncer-config",
            values={
                "pgbouncer": {"enabled": True, "configSecretName": "pgbouncer-config-secret"},
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.volumes[0]", docs[0]) == {
            "name": "pgbouncer-config",
            "secret": {"secretName": "pgbouncer-config-secret"},
        }

    def test_pgbouncer_resources_are_configurable(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "resources": {
                        "limits": {"cpu": "200m", "memory": "128Mi"},
                        "requests": {"cpu": "300m", "memory": "169Mi"},
                    },
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        assert jmespath.search("spec.template.spec.containers[0].resources.limits.memory", docs[0]) == "128Mi"
        assert (
            jmespath.search("spec.template.spec.containers[0].resources.requests.memory", docs[0]) == "169Mi"
        )
        assert jmespath.search("spec.template.spec.containers[0].resources.requests.cpu", docs[0]) == "300m"

    def test_pgbouncer_resources_are_not_added_by_default(self):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True},
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        assert jmespath.search("spec.template.spec.containers[0].resources", docs[0]) == {}

    def test_metrics_exporter_resources(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "resources": {
                            "requests": {"memory": "2Gi", "cpu": "1"},
                            "limits": {"memory": "3Gi", "cpu": "2"},
                        }
                    },
                }
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].resources", docs[0]) == {
            "limits": {
                "cpu": "2",
                "memory": "3Gi",
            },
            "requests": {
                "cpu": "1",
                "memory": "2Gi",
            },
        }

    def test_default_command_and_args(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}},
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[0].command", docs[0]) == [
            "pgbouncer",
            "-u",
            "nobody",
            "/etc/pgbouncer/pgbouncer.ini",
        ]
        assert jmespath.search("spec.template.spec.containers[0].args", docs[0]) is None

    @pytest.mark.parametrize("command", [None, ["custom", "command"]])
    @pytest.mark.parametrize("args", [None, ["custom", "args"]])
    def test_command_and_args_overrides(self, command, args):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True, "command": command, "args": args}},
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert command == jmespath.search("spec.template.spec.containers[0].command", docs[0])
        assert args == jmespath.search("spec.template.spec.containers[0].args", docs[0])

    def test_command_and_args_overrides_are_templated(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "command": ["{{ .Release.Name }}"],
                    "args": ["{{ .Release.Service }}"],
                }
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[0].command", docs[0]) == ["release-name"]
        assert jmespath.search("spec.template.spec.containers[0].args", docs[0]) == ["Helm"]

    def test_should_add_extra_volume_and_extra_volume_mount(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "extraVolumes": [
                        {
                            "name": "pgbouncer-client-certificates-{{ .Chart.Name }}",
                            "secret": {"secretName": "pgbouncer-client-tls-certificate"},
                        }
                    ],
                    "extraVolumeMounts": [
                        {
                            "name": "pgbouncer-client-certificates-{{ .Chart.Name }}",
                            "mountPath": "/etc/pgbouncer/certs",
                        }
                    ],
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert "pgbouncer-client-certificates-airflow" in jmespath.search(
            "spec.template.spec.volumes[*].name", docs[0]
        )
        assert "pgbouncer-client-certificates-airflow" in jmespath.search(
            "spec.template.spec.containers[0].volumeMounts[*].name", docs[0]
        )

    def test_should_add_global_volume_and_global_volume_mount(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                },
                "volumes": [
                    {
                        "name": "pgbouncer-client-certificates",
                        "secret": {"secretName": "pgbouncer-client-tls-certificate"},
                    }
                ],
                "volumeMounts": [
                    {"name": "pgbouncer-client-certificates", "mountPath": "/etc/pgbouncer/certs"}
                ],
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert "pgbouncer-client-certificates" in jmespath.search(
            "spec.template.spec.volumes[*].name", docs[0]
        )
        assert "pgbouncer-client-certificates" in jmespath.search(
            "spec.template.spec.containers[0].volumeMounts[*].name", docs[0]
        )

    def test_pgbouncer_replicas_are_configurable(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "replicas": 2,
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        assert jmespath.search("spec.replicas", docs[0]) == 2

    def test_should_add_component_specific_annotations(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "annotations": {"test_annotation": "test_annotation_value"},
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        assert "annotations" in jmespath.search("metadata", docs[0])
        assert jmespath.search("metadata.annotations", docs[0])["test_annotation"] == "test_annotation_value"

    def test_should_add_component_specific_labels(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "labels": {"test_label": "test_label_value"},
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )
        assert "labels" in jmespath.search("spec.template.metadata", docs[0])
        assert jmespath.search("spec.template.metadata.labels", docs[0])["test_label"] == "test_label_value"


class TestPgbouncerConfig:
    """Tests PgBouncer config."""

    def test_config_not_created_by_default(self):
        docs = render_chart(
            show_only=["templates/secrets/pgbouncer-config-secret.yaml"],
        )

        assert docs == []

    def test_should_add_annotations_to_pgbouncer_config_secret(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "configSecretAnnotations": {"test_annotation": "test_annotation_value"},
                },
            },
            show_only=["templates/secrets/pgbouncer-config-secret.yaml"],
        )[0]

        assert "annotations" in jmespath.search("metadata", docs)
        assert jmespath.search("metadata.annotations", docs)["test_annotation"] == "test_annotation_value"

    def _get_pgbouncer_ini(self, values: dict) -> str:
        docs = render_chart(
            values=values,
            show_only=["templates/secrets/pgbouncer-config-secret.yaml"],
        )
        encoded_ini = jmespath.search('data."pgbouncer.ini"', docs[0])
        return base64.b64decode(encoded_ini).decode()

    def test_databases_default(self):
        ini = self._get_pgbouncer_ini({"pgbouncer": {"enabled": True}})

        assert (
            "release-name-metadata = host=release-name-postgresql.default dbname=postgres port=5432"
            " pool_size=10" in ini
        )
        assert (
            "release-name-result-backend = host=release-name-postgresql.default dbname=postgres port=5432"
            " pool_size=5" in ini
        )

    def test_databases_override(self):
        values = {
            "pgbouncer": {
                "enabled": True,
                "metadataPoolSize": 12,
                "resultBackendPoolSize": 7,
                "extraIniMetadata": "reserve_pool = 5",
                "extraIniResultBackend": "reserve_pool = 3",
            },
            "data": {
                "metadataConnection": {"host": "meta_host", "db": "meta_db", "port": 1111},
                "resultBackendConnection": {
                    "protocol": "postgresql",
                    "host": "rb_host",
                    "user": "someuser",
                    "pass": "someuser",
                    "db": "rb_db",
                    "port": 2222,
                    "sslmode": "disabled",
                },
            },
        }
        ini = self._get_pgbouncer_ini(values)

        assert (
            "release-name-metadata = host=meta_host dbname=meta_db port=1111 pool_size=12 reserve_pool = 5"
            in ini
        )
        assert (
            "release-name-result-backend = host=rb_host dbname=rb_db port=2222 pool_size=7 reserve_pool = 3"
            in ini
        )

    def test_config_defaults(self):
        ini = self._get_pgbouncer_ini({"pgbouncer": {"enabled": True}})

        assert "listen_port = 6543" in ini
        assert "stats_users = postgres" in ini
        assert "max_client_conn = 100" in ini
        assert "verbose = 0" in ini
        assert "log_disconnections = 0" in ini
        assert "log_connections = 0" in ini
        assert "server_tls_sslmode = prefer" in ini
        assert "server_tls_ciphers = normal" in ini

        assert "server_tls_ca_file = " not in ini
        assert "server_tls_cert_file = " not in ini
        assert "server_tls_key_file = " not in ini

    def test_config_overrides(self):
        values = {
            "pgbouncer": {
                "enabled": True,
                "maxClientConn": 111,
                "verbose": 2,
                "logDisconnections": 1,
                "logConnections": 1,
                "sslmode": "verify-full",
                "ciphers": "secure",
            },
            "ports": {"pgbouncer": 7777},
            "data": {"metadataConnection": {"user": "someuser"}},
        }
        ini = self._get_pgbouncer_ini(values)

        assert "listen_port = 7777" in ini
        assert "stats_users = someuser" in ini
        assert "max_client_conn = 111" in ini
        assert "verbose = 2" in ini
        assert "log_disconnections = 1" in ini
        assert "log_connections = 1" in ini
        assert "server_tls_sslmode = verify-full" in ini
        assert "server_tls_ciphers = secure" in ini

    def test_auth_type_file_defaults(self):
        values = {
            "pgbouncer": {"enabled": True},
            "ports": {"pgbouncer": 7777},
            "data": {"metadataConnection": {"user": "someuser"}},
        }
        ini = self._get_pgbouncer_ini(values)

        assert "auth_type = scram-sha-256" in ini
        assert "auth_file = /etc/pgbouncer/users.txt" in ini

    def test_auth_type_file_overrides(self):
        values = {
            "pgbouncer": {"enabled": True, "auth_type": "any", "auth_file": "/home/auth.txt"},
            "ports": {"pgbouncer": 7777},
            "data": {"metadataConnection": {"user": "someuser"}},
        }
        ini = self._get_pgbouncer_ini(values)

        assert "auth_type = any" in ini
        assert "auth_file = /home/auth.txt" in ini

    def test_ssl_defaults_dont_create_cert_secret(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}},
            show_only=["templates/secrets/pgbouncer-certificates-secret.yaml"],
        )

        assert docs == []

    def test_ssl_config(self):
        values = {
            "pgbouncer": {"enabled": True, "ssl": {"ca": "someca", "cert": "somecert", "key": "somekey"}}
        }
        ini = self._get_pgbouncer_ini(values)

        assert "server_tls_ca_file = /etc/pgbouncer/root.crt" in ini
        assert "server_tls_cert_file = /etc/pgbouncer/server.crt" in ini
        assert "server_tls_key_file = /etc/pgbouncer/server.key" in ini

        docs = render_chart(
            values=values,
            show_only=["templates/secrets/pgbouncer-certificates-secret.yaml"],
        )

        for key, expected in [("root.crt", "someca"), ("server.crt", "somecert"), ("server.key", "somekey")]:
            encoded = jmespath.search(f'data."{key}"', docs[0])
            value = base64.b64decode(encoded).decode()
            assert expected == value

    def test_should_add_annotations_to_pgbouncer_certificates_secret(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "ssl": {"ca": "someca", "cert": "somecert", "key": "somekey"},
                    "certificatesSecretAnnotations": {"test_annotation": "test_annotation_value"},
                },
            },
            show_only=["templates/secrets/pgbouncer-certificates-secret.yaml"],
        )[0]

        assert "annotations" in jmespath.search("metadata", docs)
        assert jmespath.search("metadata.annotations", docs)["test_annotation"] == "test_annotation_value"

    def test_extra_ini_configs(self):
        values = {"pgbouncer": {"enabled": True, "extraIni": "server_round_robin = 1\nstats_period = 30"}}
        ini = self._get_pgbouncer_ini(values)

        assert "server_round_robin = 1" in ini
        assert "stats_period = 30" in ini

    def test_should_add_custom_env_variables(self):
        env1 = {"name": "TEST_ENV_1", "value": "test_env_1"}

        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "env": [env1],
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )[0]

        assert jmespath.search("spec.template.spec.containers[0].env", docs) == [env1]

    def test_should_add_extra_containers(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "extraContainers": [
                        {"name": "{{ .Chart.Name }}", "image": "test-registry/test-repo:test-tag"}
                    ],
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[-1]", docs[0]) == {
            "name": "airflow",
            "image": "test-registry/test-repo:test-tag",
        }

    def test_no_config_secret_mount(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "mountConfigSecret": False,
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        spec = jmespath.search("spec.template.spec", docs[0])
        assert spec is not None
        assert "volumes" not in spec


class TestPgbouncerExporter:
    """Tests PgBouncer exporter."""

    def test_secret_not_created_by_default(self):
        docs = render_chart(
            show_only=["templates/secrets/pgbouncer-stats-secret.yaml"],
        )
        assert len(docs) == 0

    def test_should_add_annotations_to_pgbouncer_stats_secret(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "statsSecretAnnotations": {"test_annotation": "test_annotation_value"},
                    },
                },
            },
            show_only=["templates/secrets/pgbouncer-stats-secret.yaml"],
        )[0]

        assert "annotations" in jmespath.search("metadata", docs)
        assert jmespath.search("metadata.annotations", docs)["test_annotation"] == "test_annotation_value"

    def _get_connection(self, values: dict) -> str:
        docs = render_chart(
            values=values,
            show_only=["templates/secrets/pgbouncer-stats-secret.yaml"],
        )
        encoded_connection = jmespath.search("data.connection", docs[0])
        return base64.b64decode(encoded_connection).decode()

    def test_default_exporter_secret(self):
        connection = self._get_connection({"pgbouncer": {"enabled": True}})
        assert connection == "postgresql://postgres:postgres@127.0.0.1:6543/pgbouncer?sslmode=disable"

    def test_exporter_secret_with_overrides(self):
        connection = self._get_connection(
            {
                "pgbouncer": {"enabled": True, "metricsExporterSidecar": {"sslmode": "require"}},
                "data": {
                    "metadataConnection": {
                        "user": "username@123123",
                        "pass": "password@!@#$^&*()",
                        "host": "somehost",
                        "port": 7777,
                        "db": "somedb",
                    },
                },
                "ports": {"pgbouncer": 1111},
            }
        )
        assert (
            connection == "postgresql://username%40123123:password%40%21%40%23$%5E&%2A%28%29@127.0.0.1:1111"
            "/pgbouncer?sslmode=require"
        )

    def test_no_existing_secret(self):
        docs = render_chart(
            "test-pgbouncer-stats",
            values={
                "pgbouncer": {"enabled": True},
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].env[0].valueFrom.secretKeyRef", docs[0]) == {
            "name": "test-pgbouncer-stats-pgbouncer-stats",
            "key": "connection",
        }

    def test_existing_secret(self):
        docs = render_chart(
            "test-pgbouncer-stats",
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "statsSecretName": "existing-stats-secret",
                    },
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].env[0].valueFrom.secretKeyRef", docs[0]) == {
            "name": "existing-stats-secret",
            "key": "connection",
        }

    def test_existing_secret_existing_key(self):
        docs = render_chart(
            "test-pgbouncer-stats",
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "statsSecretName": "existing-stats-secret",
                        "statsSecretKey": "existing-stats-secret-key",
                    },
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].env[0].valueFrom.secretKeyRef", docs[0]) == {
            "name": "existing-stats-secret",
            "key": "existing-stats-secret-key",
        }

    def test_unused_secret_key(self):
        docs = render_chart(
            "test-pgbouncer-stats",
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "statsSecretKey": "unused",
                    },
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert jmespath.search("spec.template.spec.containers[1].env[0].valueFrom.secretKeyRef", docs[0]) == {
            "name": "test-pgbouncer-stats-pgbouncer-stats",
            "key": "connection",
        }

    def test_extra_volume_mounts(self):
        extra_volume_mounts = [
            {
                "name": "test-volume",
                "mountPath": "/mnt/test_volume",
            }
        ]

        docs = render_chart(
            "test-pgbouncer-stats",
            values={
                "pgbouncer": {
                    "enabled": True,
                    "metricsExporterSidecar": {
                        "statsSecretKey": "unused",
                        "extraVolumeMounts": extra_volume_mounts,
                    },
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-deployment.yaml"],
        )

        assert (
            jmespath.search("spec.template.spec.containers[1].volumeMounts", docs[0]) == extra_volume_mounts
        )


class TestPgBouncerServiceAccount:
    """Tests PgBouncer Service Account."""

    def test_default_automount_service_account_token(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "serviceAccount": {"create": True},
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-serviceaccount.yaml"],
        )
        assert jmespath.search("automountServiceAccountToken", docs[0]) is True

    def test_overridden_automount_service_account_token(self):
        docs = render_chart(
            values={
                "pgbouncer": {
                    "enabled": True,
                    "serviceAccount": {"create": True, "automountServiceAccountToken": False},
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-serviceaccount.yaml"],
        )
        assert jmespath.search("automountServiceAccountToken", docs[0]) is False


class TestPgbouncerNetworkPolicy:
    """Tests PgBouncer Network Policy."""

    def test_should_create_pgbouncer_network_policy(self):
        docs = render_chart(
            values={"pgbouncer": {"enabled": True}, "networkPolicies": {"enabled": True}},
            show_only=["templates/pgbouncer/pgbouncer-networkpolicy.yaml"],
        )

        assert jmespath.search("kind", docs[0]) == "NetworkPolicy"
        assert jmespath.search("metadata.name", docs[0]) == "release-name-pgbouncer-policy"

    @pytest.mark.parametrize(
        "conf, expected_selector",
        [
            # test with workers.keda enabled without namespace labels
            (
                {"executor": "CeleryExecutor", "workers": {"keda": {"enabled": True}}},
                [{"podSelector": {"matchLabels": {"app": "keda-operator"}}}],
            ),
            # test with triggerer.keda enabled without namespace labels
            (
                {"triggerer": {"keda": {"enabled": True}}},
                [{"podSelector": {"matchLabels": {"app": "keda-operator"}}}],
            ),
            # test with workers.keda and triggerer.keda both enabled without namespace labels
            (
                {
                    "executor": "CeleryExecutor",
                    "workers": {"keda": {"enabled": True}},
                    "triggerer": {"keda": {"enabled": True}},
                },
                [{"podSelector": {"matchLabels": {"app": "keda-operator"}}}],
            ),
            # test with workers.keda enabled with namespace labels
            (
                {
                    "executor": "CeleryExecutor",
                    "workers": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}},
                },
                [
                    {
                        "namespaceSelector": {"matchLabels": {"app": "airflow"}},
                        "podSelector": {"matchLabels": {"app": "keda-operator"}},
                    }
                ],
            ),
            # test with triggerer.keda enabled with namespace labels
            (
                {"triggerer": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}}},
                [
                    {
                        "namespaceSelector": {"matchLabels": {"app": "airflow"}},
                        "podSelector": {"matchLabels": {"app": "keda-operator"}},
                    }
                ],
            ),
            # test with workers.keda and triggerer.keda both enabled with namespace labels
            (
                {
                    "executor": "CeleryExecutor",
                    "workers": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}},
                    "triggerer": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}},
                },
                [
                    {
                        "namespaceSelector": {"matchLabels": {"app": "airflow"}},
                        "podSelector": {"matchLabels": {"app": "keda-operator"}},
                    }
                ],
            ),
            # test with workers.keda and triggerer.keda both enabled workers with namespace labels
            # and triggerer without namespace labels
            (
                {
                    "executor": "CeleryExecutor",
                    "workers": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}},
                    "triggerer": {"keda": {"enabled": True}},
                },
                [
                    {
                        "namespaceSelector": {"matchLabels": {"app": "airflow"}},
                        "podSelector": {"matchLabels": {"app": "keda-operator"}},
                    }
                ],
            ),
            # test with workers.keda and triggerer.keda both enabled workers without namespace labels
            # and triggerer with namespace labels
            (
                {
                    "executor": "CeleryExecutor",
                    "workers": {"keda": {"enabled": True}},
                    "triggerer": {"keda": {"enabled": True, "namespaceLabels": {"app": "airflow"}}},
                },
                [
                    {
                        "namespaceSelector": {"matchLabels": {"app": "airflow"}},
                        "podSelector": {"matchLabels": {"app": "keda-operator"}},
                    }
                ],
            ),
        ],
    )
    def test_pgbouncer_network_policy_with_keda(self, conf, expected_selector):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True},
                "networkPolicies": {"enabled": True},
                **conf,
            },
            show_only=["templates/pgbouncer/pgbouncer-networkpolicy.yaml"],
        )

        assert expected_selector == jmespath.search("spec.ingress[0].from[1:]", docs[0])


class TestPgbouncerIngress:
    """Tests PgBouncer Ingress."""

    def test_pgbouncer_ingress(self):
        docs = render_chart(
            values={
                "pgbouncer": {"enabled": True},
                "ingress": {
                    "pgbouncer": {
                        "enabled": True,
                        "hosts": [
                            {"name": "some-host", "tls": {"enabled": True, "secretName": "some-secret"}}
                        ],
                        "ingressClassName": "ingress-class",
                    }
                },
            },
            show_only=["templates/pgbouncer/pgbouncer-ingress.yaml"],
        )

        assert jmespath.search("spec.rules[0].http.paths[0].backend.service", docs[0]) == {
            "name": "release-name-pgbouncer",
            "port": {"name": "pgb-metrics"},
        }
        assert jmespath.search("spec.rules[0].http.paths[0].path", docs[0]) == "/metrics"
        assert jmespath.search("spec.rules[0].host", docs[0]) == "some-host"
        assert jmespath.search("spec.tls[0]", docs[0]) == {
            "hosts": ["some-host"],
            "secretName": "some-secret",
        }
        assert jmespath.search("spec.ingressClassName", docs[0]) == "ingress-class"
