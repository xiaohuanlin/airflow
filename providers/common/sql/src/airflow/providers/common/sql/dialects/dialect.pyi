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
#
# This is automatically generated stub for the `common.sql` provider
#
# This file is generated automatically by the `update-common-sql-api stubs` pre-commit
# and the .pyi file represents part of the "public" API that the
# `common.sql` provider exposes to other providers.
#
# Any, potentially breaking change in the stubs will require deliberate manual action from the contributor
# making a change to the `common.sql` provider. Those stubs are also used by MyPy automatically when checking
# if only public API of the common.sql provider is used by all the other providers.
#
# You can read more in the README_API.md file
#
"""
Definition of the public interface for airflow.providers.common.sql.src.airflow.providers.common.sql.dialects.dialect
isort:skip_file
"""

from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

from _typeshed import Incomplete as Incomplete
from sqlalchemy.engine import Inspector as Inspector

from airflow.utils.log.logging_mixin import LoggingMixin as LoggingMixin

T = TypeVar("T")

class Dialect(LoggingMixin):
    hook: Incomplete
    def __init__(self, hook, **kwargs) -> None: ...
    def escape_word(self, column_name: str) -> str: ...
    def unescape_word(self, value: str | None) -> str | None: ...
    @property
    def placeholder(self) -> str: ...
    @property
    def insert_statement_format(self) -> str: ...
    @property
    def replace_statement_format(self) -> str: ...
    @property
    def escape_word_format(self) -> str: ...
    @property
    def inspector(self) -> Inspector: ...
    @classmethod
    def extract_schema_from_table(cls, table: str) -> tuple[str, str | None]: ...
    def get_column_names(
        self, table: str, schema: str | None = None, predicate: Callable[[T], bool] = ...
    ) -> list[str] | None: ...
    def get_target_fields(self, table: str, schema: str | None = None) -> list[str] | None: ...
    def get_primary_keys(self, table: str, schema: str | None = None) -> list[str] | None: ...
    def run(
        self,
        sql: str | Iterable[str],
        autocommit: bool = False,
        parameters: Iterable | Mapping[str, Any] | None = None,
        handler: Callable[[Any], T] | None = None,
        split_statements: bool = False,
        return_last: bool = True,
    ) -> tuple | list | list[tuple] | list[list[tuple] | tuple] | None: ...
    def get_records(
        self, sql: str | list[str], parameters: Iterable | Mapping[str, Any] | None = None
    ) -> Any: ...
    @property
    def reserved_words(self) -> set[str]: ...
    def generate_insert_sql(self, table, values, target_fields, **kwargs) -> str: ...
    def generate_replace_sql(self, table, values, target_fields, **kwargs) -> str: ...
