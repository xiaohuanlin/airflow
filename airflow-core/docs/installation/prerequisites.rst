 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

Prerequisites
-------------

Airflow® is tested with:

* Python: 3.10, 3.11, 3.12, 3.13

* Databases:

  * PostgreSQL: 13, 14, 15, 16, 17
  * MySQL: 8.0, `Innovation <https://dev.mysql.com/blog-archive/introducing-mysql-innovation-and-long-term-support-lts-versions>`_
  * SQLite: 3.15.0+

* Kubernetes: 1.30, 1.31, 1.32, 1.33

While we recommend a minimum of 4GB of memory for Airflow, the actual requirements heavily depend on your chosen deployment.

.. warning::

  Despite significant similarities between MariaDB and MySQL, we DO NOT support MariaDB as a backend for Airflow.
  There are known problems (for example index handling) between MariaDB and MySQL and we do not test
  our migration scripts nor application execution on Maria DB. We know there were people who used
  MariaDB for Airflow and that cause a lot of operational headache for them so we strongly discourage
  attempts to use MariaDB as a backend and users cannot expect any community support for it
  because the number of users who tried to use MariaDB for Airflow is very small.

.. warning::
  SQLite is used in Airflow tests. DO NOT use it in production. We recommend
  using the latest stable version of SQLite for local development.


.. warning::

  Airflow® currently can be run on POSIX-compliant Operating Systems. For development it is regularly
  tested on fairly modern Linux distributions that our contributors use and recent versions of MacOS.
  On Windows you can run it via WSL2 (Windows Subsystem for Linux 2) or via Linux Containers.
  The work to add Windows support is tracked via `#10388 <https://github.com/apache/airflow/issues/10388>`__
  but it is not a high priority. You should only use Linux-based distributions as "Production environment"
  as this is the only environment that is supported. The only distribution that is used in our CI tests and that
  is used in the `Community managed DockerHub image <https://hub.docker.com/p/apache/airflow>`__ is
  ``Debian Bookworm``.
