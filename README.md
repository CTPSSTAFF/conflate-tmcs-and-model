# conflate-tmcs-and-model

Tool to conflate INRIX TMCs and CTPS Model Links

Usage: conflate_tmcs_and_model_link MassDOT_route_id list_of_tmcs_file
  1. MassDOT_route_id is required
  2. list_of_tmcs_file is optional
If list_of_tmcs_file is not provided, all TMCs in the inidcated route will be processed.

This script conflates INRIX TMCs and Statewide Model Linkx onto the MassDOT Road Inventory
  1. For a given MassDOT "route_id", generate an event table containing the
     "overlay" (i.e., the logical UNION) of the following events onto it:
    a. INRIX TMCs
    b. CTPS Model Links
  2. Produce a final output CSV file from this event table, each record of which
     contains a link_id, a tmc ID, the fraction of the given TMC contibuting
     to the given link_id, and the fraction of the given link_id contributing 
     to the given tmc ID.

This module depends upon the following modules:
  1. arcpy
  2. csv
