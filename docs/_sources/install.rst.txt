============
Installation
============

VirtualBox
==========

Install the latest version of `VirtualBox <https://www.virtualbox.org/>`_

Host Network Manager
--------------------

Create an internal network for your computer to connect to VirtualBox virtual machines.

GUI
~~~
1. Select **File > Host Network Manager** from the menu

Linux Commandline
~~~~~~~~~~~~~~~~~

1. Create a new interface on the host OS

.. code-block:: console

    VBoxManage hostonlyif create
    VBoxManage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1
    VBoxManage dhcpserver add --ifname vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0 --lowerip 192.168.56.100 --upperip 192.168.56.200

2. If necessary modify the DHCP server settings

.. code-block:: console

    VBoxManage dhcpserver modify --ifname vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0 --lowerip 192.168.56.100 --upperip 192.168.56.200
    VBoxManage dhcpserver modify --ifname vboxnet0 --enable


* Optionally confirm that the settings are in effect

.. code-block:: console

    VBoxManage list hostonlyifs
    VBoxManage list dhcpservers


Import Appliance
----------------

* Download the `ESWS OVA <https://drive.google.com/file/d/1YtR5WWwU8OS5ozW-WGaL_6NcDnmMGdFq/view?usp=sharing>`_ and save it as **esws.ova**

GUI
~~~

1. Select **File > Import Appliance** from the menu

Linux Commandline
~~~~~~~~~~~~~~~~~

.. code-block:: console

    VBoxManage import esws.ova --vsys 0 --vmname "ESWS"
