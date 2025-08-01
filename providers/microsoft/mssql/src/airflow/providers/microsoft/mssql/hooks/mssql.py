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
"""Microsoft SQLServer hook module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pymssql
from pymssql import Connection as PymssqlConnection

from airflow.providers.common.sql.hooks.sql import DbApiHook
from airflow.providers.microsoft.mssql.dialects.mssql import MsSqlDialect

if TYPE_CHECKING:
    from airflow.providers.common.sql.dialects.dialect import Dialect
    from airflow.providers.openlineage.sqlparser import DatabaseInfo


class MsSqlHook(DbApiHook):
    """
    Interact with Microsoft SQL Server.

    :param args: passed to DBApiHook
    :param sqlalchemy_scheme: Scheme sqlalchemy connection.  Default is ``mssql+pymssql`` Only used for
      ``get_sqlalchemy_engine`` and ``get_sqlalchemy_connection`` methods.
    :param kwargs: passed to DbApiHook
    """

    conn_name_attr = "mssql_conn_id"
    default_conn_name = "mssql_default"
    conn_type = "mssql"
    hook_name = "Microsoft SQL Server"
    supports_autocommit = True
    DEFAULT_SQLALCHEMY_SCHEME = "mssql+pymssql"

    def __init__(
        self,
        *args,
        sqlalchemy_scheme: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **{**kwargs, **{"escape_word_format": "[{}]"}})
        self.schema = kwargs.pop("schema", None)
        self._sqlalchemy_scheme = sqlalchemy_scheme

    @property
    def sqlalchemy_scheme(self) -> str:
        """Sqlalchemy scheme either from constructor, connection extras or default."""
        extra_scheme = self.connection_extra_lower.get("sqlalchemy_scheme")
        if not self._sqlalchemy_scheme and extra_scheme and (":" in extra_scheme or "/" in extra_scheme):
            raise RuntimeError("sqlalchemy_scheme in connection extra should not contain : or / characters")
        return self._sqlalchemy_scheme or extra_scheme or self.DEFAULT_SQLALCHEMY_SCHEME

    @property
    def dialect_name(self) -> str:
        return "mssql"

    @property
    def dialect(self) -> Dialect:
        return MsSqlDialect(self)

    def get_uri(self) -> str:
        from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

        r = list(urlsplit(super().get_uri()))
        # change pymssql driver:
        r[0] = self.sqlalchemy_scheme
        # remove query string 'sqlalchemy_scheme' like parameters:
        qs = parse_qs(r[3], keep_blank_values=True)
        for k in list(qs.keys()):
            if k.lower() == "sqlalchemy_scheme":
                qs.pop(k, None)
        r[3] = urlencode(qs, doseq=True)
        return urlunsplit(r)

    def get_sqlalchemy_connection(
        self, connect_kwargs: dict | None = None, engine_kwargs: dict | None = None
    ) -> Any:
        """Sqlalchemy connection object."""
        engine = self.get_sqlalchemy_engine(engine_kwargs=engine_kwargs)
        return engine.connect(**(connect_kwargs or {}))

    def get_conn(self) -> PymssqlConnection:
        """Return ``pymssql`` connection object."""
        conn = self.connection
        extra_conn_args = {key: val for key, val in conn.extra_dejson.items() if key != "sqlalchemy_scheme"}
        return pymssql.connect(
            server=conn.host or "",
            user=conn.login,
            password=conn.password,
            database=self.schema or conn.schema or "",
            port=str(conn.port),
            **extra_conn_args,
        )

    def set_autocommit(
        self,
        conn: PymssqlConnection,
        autocommit: bool,
    ) -> None:
        conn.autocommit(autocommit)

    def get_autocommit(self, conn: PymssqlConnection):
        return conn.autocommit_state

    def get_openlineage_database_info(self, connection) -> DatabaseInfo:
        """Return MSSQL specific information for OpenLineage."""
        from airflow.providers.openlineage.sqlparser import DatabaseInfo

        return DatabaseInfo(
            scheme=self.get_openlineage_database_dialect(connection),
            authority=DbApiHook.get_openlineage_authority_part(connection, default_port=1433),
            information_schema_columns=[
                "table_schema",
                "table_name",
                "column_name",
                "ordinal_position",
                "data_type",
                "table_catalog",
            ],
            database=self.schema or self.connection.schema,
            is_information_schema_cross_db=True,
        )

    def get_openlineage_database_dialect(self, connection) -> str:
        """Return database dialect."""
        return "mssql"

    def get_openlineage_default_schema(self) -> str | None:
        """Return current schema."""
        return self.get_first("SELECT SCHEMA_NAME();")[0]
