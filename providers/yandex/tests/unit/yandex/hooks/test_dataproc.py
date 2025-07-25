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

import json
from unittest import mock

import pytest

pytest.importorskip("yandexcloud")

try:
    import importlib.util

    if not importlib.util.find_spec("airflow.sdk.bases.hook"):
        raise ImportError

    BASEHOOK_PATCH_PATH = "airflow.sdk.bases.hook.BaseHook"
except ImportError:
    BASEHOOK_PATCH_PATH = "airflow.hooks.base.BaseHook"

from airflow.models import Connection
from airflow.providers.yandex.hooks.dataproc import DataprocHook

# Airflow connection with type "yandexcloud" must be created
CONNECTION_ID = "yandexcloud_default"

# Name of the datacenter where Dataproc cluster will be created
AVAILABILITY_ZONE_ID = "ru-central1-c"

CLUSTER_NAME = "dataproc_cluster"
CLUSTER_IMAGE_VERSION = "1.4"

# https://cloud.yandex.com/docs/resource-manager/operations/folder/get-id
FOLDER_ID = "my_folder_id"

# Subnetwork id should belong to the availability zone set above
SUBNET_ID = "my_subnet_id"

# Dataproc cluster jobs will produce logs in specified s3 bucket
S3_BUCKET_NAME_FOR_LOGS = "my_bucket_name"

# https://cloud.yandex.com/docs/iam/concepts/users/service-accounts
SERVICE_ACCOUNT_ID = "my_service_account_id"

# https://cloud.yandex.com/docs/iam/concepts/authorization/oauth-token
OAUTH_TOKEN = "my_oauth_token"

# Ssh public keys will be placed to Dataproc cluster nodes, allowing to get a root shell at the nodes
SSH_PUBLIC_KEYS = [
    "ssh-rsa AAA5B3NzaC1yc2EAA1ADA2ABA3AA4QCxO38tKA0XIs9ivPxt7AYdf3bgtAR1ow3Qkb9GPQ6wkFHQq"
    "cFDe6faKCxH6iDRt2o4D8L8Bx6zN42uZSB0nf8jkIxFTcEU3mFSXEbWByg78ao3dMrAAj1tyr1H1pON6P0="
]

# If Yandex.Cloud credentials are set than full test will be run. Otherwise, only mocked tests.
HAS_CREDENTIALS = OAUTH_TOKEN != "my_oauth_token"


class TestYandexCloudDataprocHook:
    def _init_hook(self):
        with mock.patch(f"{BASEHOOK_PATCH_PATH}.get_connection") as mock_get_connection:
            mock_get_connection.return_value = self.connection
            self.hook = DataprocHook()

    def setup_method(self):
        self.connection = Connection(extra=json.dumps({"oauth": OAUTH_TOKEN}))
        self._init_hook()

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_create_dataproc_cluster_mocked(self, mock_create_operation):
        self._init_hook()

        self.hook.dataproc_client.create_cluster(
            cluster_name=CLUSTER_NAME,
            ssh_public_keys=SSH_PUBLIC_KEYS,
            folder_id=FOLDER_ID,
            subnet_id=SUBNET_ID,
            zone=AVAILABILITY_ZONE_ID,
            s3_bucket=S3_BUCKET_NAME_FOR_LOGS,
            cluster_image_version=CLUSTER_IMAGE_VERSION,
            service_account_id=SERVICE_ACCOUNT_ID,
        )
        assert mock_create_operation.called

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_delete_dataproc_cluster_mocked(self, mock_create_operation):
        self._init_hook()
        self.hook.dataproc_client.delete_cluster("my_cluster_id")
        assert mock_create_operation.called

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_create_hive_job_hook(self, mock_create_operation):
        self._init_hook()

        self.hook.dataproc_client.create_hive_job(
            cluster_id="my_cluster_id",
            continue_on_failure=False,
            name="Hive job",
            properties=None,
            query="SELECT 1;",
            script_variables=None,
        )
        assert mock_create_operation.called

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_create_mapreduce_job_hook(self, mock_create_operation):
        self._init_hook()

        self.hook.dataproc_client.create_mapreduce_job(
            archive_uris=None,
            args=[
                "-mapper",
                "mapper.py",
                "-reducer",
                "reducer.py",
                "-numReduceTasks",
                "1",
                "-input",
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "-output",
                "s3a://some-out-bucket/dataproc/job/results",
            ],
            cluster_id="my_cluster_id",
            file_uris=[
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/mapper.py",
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/reducer.py",
            ],
            jar_file_uris=None,
            main_class="org.apache.hadoop.streaming.HadoopStreaming",
            main_jar_file_uri=None,
            name="Mapreduce job",
            properties={
                "yarn.app.mapreduce.am.resource.mb": "2048",
                "yarn.app.mapreduce.am.command-opts": "-Xmx2048m",
                "mapreduce.job.maps": "6",
            },
        )
        assert mock_create_operation.called

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_create_spark_job_hook(self, mock_create_operation):
        self._init_hook()

        self.hook.dataproc_client.create_spark_job(
            archive_uris=["s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip"],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/dataproc/job/results/${{JOB_ID}}",
            ],
            cluster_id="my_cluster_id",
            file_uris=["s3a://some-in-bucket/jobs/sources/data/config.json"],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
                "s3a://some-in-bucket/jobs/sources/java/opencsv-4.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/json-20190722.jar",
            ],
            main_class="ru.yandex.cloud.dataproc.examples.PopulationSparkJob",
            main_jar_file_uri="s3a://data-proc-public/jobs/sources/java/dataproc-examples-1.0.jar",
            name="Spark job",
            properties={"spark.submit.deployMode": "cluster"},
        )
        assert mock_create_operation.called

    @mock.patch("yandexcloud.SDK.create_operation_and_get_result")
    def test_create_pyspark_job_hook(self, mock_create_operation):
        self._init_hook()

        self.hook.dataproc_client.create_pyspark_job(
            archive_uris=["s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip"],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/jobs/results/${{JOB_ID}}",
            ],
            cluster_id="my_cluster_id",
            file_uris=["s3a://some-in-bucket/jobs/sources/data/config.json"],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/dataproc-examples-1.0.jar",
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
            ],
            main_python_file_uri="s3a://some-in-bucket/jobs/sources/pyspark-001/main.py",
            name="Pyspark job",
            properties={"spark.submit.deployMode": "cluster"},
            python_file_uris=["s3a://some-in-bucket/jobs/sources/pyspark-001/geonames.py"],
        )
        assert mock_create_operation.called
