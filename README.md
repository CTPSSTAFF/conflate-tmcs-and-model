# conflate-tmcs-and-model

Tool to conflate INRIX TMCs and CTPS Model Links

This version is intended for use with the model links file produced by TDM23.

## Usage
Usage: conflate_tmcs_and_model_link MassDOT_route_id \[list_of_tmcs_file\]
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

## Dependencies
This module depends upon the following modules:
  1. arcpy
  2. csv

## Input Model Links
The TMD23 model links are delivered in a shapefile stored in Google Drive - J:\Shared drives\TMD_TSA\Model\platform\outputs\FullRun\_networks\links.shp.
All of the 'pieces' of this shapefile are downloaded and stored in the subfolder 'Model_Links_Shapefile', in order to be run by this tool: ESRI tools
don't work well (really, at all) with Google Drive data sources.

This shapefile is in the Lambert Conformal Conic SRS. The user is expected to have projected this shapefile to
the EPSG:26986 SRS ('Mass State Plane, NAD83, meters) and stored the result in feature class 'links' in the File Geodatabase 'model_links.gdb'.

## Pre-requisites
  1. Model Links in model_links.gdb\links - see note above
    * Note that this feature class should use the EPSG:26986 SRS ('Mass State Plane, NAD 83, meters')
  2. The user has created following geodatabases for storing intermediate results:
     1. tmc_events.gdb
	 2. links_events.gdb
	 3. overlay.gdb
	 4.output_prep.gdb
  3. The user has created an output folder for the final CSV output files named csv_output
  
All of the above _could_ be parameterized, but given that this tool will be 'run once' (on each route), the value of so doing seemed minimal.