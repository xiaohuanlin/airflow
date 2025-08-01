#
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

from kylinpy import exceptions, kylinpy

from airflow.exceptions import AirflowException

try:
    from airflow.sdk import BaseHook
except ImportError:
    from airflow.hooks.base import BaseHook  # type: ignore[attr-defined,no-redef]


class KylinHook(BaseHook):
    """
    Interact with Kylin to run CubeSource commands and get job status.

    :param kylin_conn_id: The connection id as configured in Airflow administration.
    :param project: project name
    :param dsn: dsn
    """

    conn_name_attr = "kylin_conn_id"
    default_conn_name = "kylin_default"
    conn_type = "kylin"
    hook_name = "Apache Kylin"

    def __init__(
        self,
        kylin_conn_id: str = default_conn_name,
        project: str | None = None,
        dsn: str | None = None,
    ):
        super().__init__()
        self.kylin_conn_id = kylin_conn_id
        self.project = project
        self.dsn = dsn

    def get_conn(self):
        conn = self.get_connection(self.kylin_conn_id)
        if self.dsn:
            return kylinpy.create_kylin(self.dsn)
        self.project = self.project or conn.schema
        return kylinpy.Kylin(
            conn.host,
            username=conn.login,
            password=conn.password,
            port=conn.port,
            project=self.project,
            **conn.extra_dejson,
        )

    def cube_run(self, datasource_name, op, **op_args):
        """
        Run CubeSource command which in CubeSource.support_invoke_command.

        :param datasource_name:
        :param op: command
        :param op_args: command args
        :return: response
        """
        cube_source = self.get_conn().get_datasource(datasource_name)
        try:
            return cube_source.invoke_command(op, **op_args)
        except exceptions.KylinError as err:
            raise AirflowException(f"Cube operation {op} error , Message: {err}")

    def get_job_status(self, job_id):
        """
        Get job status.

        :param job_id: kylin job id
        :return: job status
        """
        return self.get_conn().get_job(job_id).status
