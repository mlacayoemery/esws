===========================
Configuration & Maintenance
===========================

These steps are **optional**.

Login
=====
The default user name and password are **esws**

.. code-block:: console

    ssh esws@192.168.56.104

Update the Guest OS
===================

.. code-block:: console

    sudo apt-get update
    sudo apt-get dist-upgrade
    sudo apt-get autoremove

Update ESWS
===========

.. code-block:: console

    git -C /home/esws/esws pull

