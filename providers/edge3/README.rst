
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

.. NOTE! THIS FILE IS AUTOMATICALLY GENERATED AND WILL BE OVERWRITTEN!

.. IF YOU WANT TO MODIFY TEMPLATE FOR THIS FILE, YOU SHOULD MODIFY THE TEMPLATE
   ``PROVIDER_README_TEMPLATE.rst.jinja2`` IN the ``dev/breeze/src/airflow_breeze/templates`` DIRECTORY

Package ``apache-airflow-providers-edge3``

Release: ``1.1.2``


Handle edge workers on remote sites via HTTP(s) connection and orchestrates work over distributed sites.

When tasks need to be executed on remote sites where the connection need to pass through
firewalls or other network restrictions, the Edge Worker can be deployed. The Edge Worker
is a lightweight process with reduced dependencies. The worker only needs to be able to
communicate with the central Airflow site via HTTPS.

In the central Airflow site the EdgeExecutor is used to orchestrate the work. The EdgeExecutor
is a custom executor which is used to schedule tasks on the edge workers. The EdgeExecutor can co-exist
with other executors (for example CeleryExecutor or KubernetesExecutor) in the same Airflow site.

Additional REST API endpoints are provided to distribute tasks and manage the edge workers. The endpoints
are provided by the API server.


Provider package
----------------

This is a provider package for ``edge3`` provider. All classes for this provider package
are in ``airflow.providers.edge3`` python package.

You can find package information and changelog for the provider
in the `documentation <https://airflow.apache.org/docs/apache-airflow-providers-edge3/1.1.2/>`_.

Installation
------------

You can install this package on top of an existing Airflow 2 installation (see ``Requirements`` below
for the minimum Airflow version supported) via
``pip install apache-airflow-providers-edge3``

The package supports the following python versions: 3.10,3.11,3.12,3.13

Requirements
------------

==================  ===================
PIP package         Version required
==================  ===================
``apache-airflow``  ``>=2.10.0``
``pydantic``        ``>=2.11.0``
``retryhttp``       ``>=1.2.0,!=1.3.0``
==================  ===================

Cross provider package dependencies
-----------------------------------

Those are dependencies that might be needed in order to use all the features of the package.
You need to install the specified providers in order to use them.

You can install such cross-provider dependencies when installing from PyPI. For example:

.. code-block:: bash

    pip install apache-airflow-providers-edge3[fab]


==============================================================================================  =======
Dependent package                                                                               Extra
==============================================================================================  =======
`apache-airflow-providers-fab <https://airflow.apache.org/docs/apache-airflow-providers-fab>`_  ``fab``
==============================================================================================  =======

The changelog for the provider package can be found in the
`changelog <https://airflow.apache.org/docs/apache-airflow-providers-edge3/1.1.2/changelog.html>`_.
