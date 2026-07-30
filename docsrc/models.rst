.. _models:

============
Model Inputs
============

The inputs of each InVEST model, generated automatically from the model's
``MODEL_SPEC`` at documentation build time.

Each diagram is a dependency tree: the model is the root, every parameter is a
node, and an edge runs from each parameter to the one that enables it -- so an
optional toggle branches to the inputs it switches on. Nodes are coloured by
requirement: **green** = required, **amber** = conditional (the condition is
printed on the node), **grey** = optional.

``workspace_dir`` and ``n_workers`` are not shown: the WPS manages them itself
and does not accept them as process inputs. ``results_suffix`` is left out of
the diagrams too, but every process does accept it.

Annual Water Yield
==================

.. invest-inputs:: annual_water_yield

Carbon Storage and Sequestration
================================

.. invest-inputs:: carbon

Coastal Blue Carbon
===================

.. invest-inputs:: coastal_blue_carbon

Coastal Blue Carbon Preprocessor
================================

.. invest-inputs:: coastal_blue_carbon_preprocessor

Coastal Vulnerability
=====================

.. invest-inputs:: coastal_vulnerability

Crop Pollination
================

.. invest-inputs:: pollination

Crop Production: Percentile
===========================

.. invest-inputs:: crop_production_percentile

Crop Production: Regression
===========================

.. invest-inputs:: crop_production_regression

DelineateIt
===========

.. invest-inputs:: delineateit

Forest Carbon Edge Effect
=========================

.. invest-inputs:: forest_carbon_edge_effect

Habitat Quality
===============

.. invest-inputs:: habitat_quality

Habitat Risk Assessment
=======================

.. invest-inputs:: habitat_risk_assessment

Nutrient Delivery Ratio
=======================

.. invest-inputs:: ndr

RouteDEM
========

.. invest-inputs:: routedem

Scenario Generator: Proximity Based
===================================

.. invest-inputs:: scenario_generator_proximity

Scenic Quality
==============

.. invest-inputs:: scenic_quality

Seasonal Water Yield
====================

.. invest-inputs:: seasonal_water_yield

Sediment Delivery Ratio
=======================

.. invest-inputs:: sdr

Urban Cooling
=============

.. invest-inputs:: urban_cooling_model

Urban Flood Risk Mitigation
===========================

.. invest-inputs:: urban_flood_risk_mitigation

Urban Mental Health
===================

.. invest-inputs:: urban_mental_health

Urban Nature Access
===================

.. invest-inputs:: urban_nature_access

Urban Stormwater Retention
==========================

.. invest-inputs:: stormwater

Visitation: Recreation and Tourism
==================================

.. invest-inputs:: recreation

Wave Energy Production
======================

.. invest-inputs:: wave_energy

Wind Energy Production
======================

.. invest-inputs:: wind_energy

