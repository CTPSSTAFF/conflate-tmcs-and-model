# conflate-tmcs-and-model

Tool to conflate INRIX TMCs and CTPS Model Links

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
### TDM19
The model links for TDM19 were delivered in a shapfile using the EPSG:4019 ('GCS_GRS_1980') spatial reference system. 
Why this SRS was used for the link data was never made clear to me.
In any event, in order to make the model links usable in the conflation process, this shapefile was:
* imported into a file GeoDatabase as a feature class
* that feature class was first projected to the EPSG:4326 ('WGS84', a.k.a. 'lat/lng') SRS
* and then projected to the EPSG:26986 ('Mass State Plane, NAD83, meters) SRS.

### TDM23 - this is a work in progress
The TMD23 model links are delivered in a shapefile stored in Google Drive - J:\Shared drives\TMD_TSA\Model\platform\outputs\FullRun\_networks\links.shp.
All of the 'pieces' of this shapefile are downloaded and stored in the subfolder 'Model_Links_Shapefile', in order to be run by this script: ESRI tools
don't work well (really, don't work at all) with Google Drive data sources.

This shapefile is in the Lambert Conformal Conic SRS. The user is expected to have projected this shapefile to
the EPSG:26986 SRS ('Mass State Plane, NAD83, meters) and stored the result in feature class 'links' in the File Geodatabase 'model_links.gdb'.

## Pre-requisites
### TDM19
1. Model links reprojected to EPSG:26986, as described above, and stored in the feature class __model_links.gdb\Statewide_Model_Links_EPSG26986__.
2. This feature class has been 'augmented' by adding fields named __route\_numb__, __route\_dir__, and __route\_id__ to it, into which the
   correspondingly-named attributes from the Road Inventory __LRSN_Routes__ feature class have been harvested. The means by which these fields were harvested in 2020 is as follows:
```
	for each MassDOT route_id:
		select all records with SCEN_00_FU == 1 in Model links feature class
		select record with route_id == specified MassDOT route_id in MassDOT_LRSN_Routes FC
		Spatial Join:
			target_features = model links FC
			join_features = MassDOT_LRSN_Routes FC
			keep_all_target_features = False
			how = HAVE_THEIR_CENTER_IN
			search_radius = 2 meters
			in field_map of join_features: specify (at least) route_id
	# end_for
	Use ESRI 'merge' tool to merge all the individual FC's created above into a single FC 'Statewide_Model_Links_EPSG26986__augmented'
```
3. The user has created following empty geodatabases for storing intermediate results produced by running this script
    1. __tmc_events.gdb__
    2. __links_events.gdb__
    3. __overlay.gdb__
    4. __output_prep.gdb__
4. The user has created an empty output folder for the final CSV output files named __csv_output__.

### TDM23 - this is a work in progress.
1. Model Links in the feature class __model_links.gdb\links__ - see note above under 'Input Model Links' for TDM23.
  * Note that this feature class should use the EPSG:26986 SRS ('Mass State Plane, NAD 83, meters')
2. The user has created following geodatabases for storing intermediate results:
    1. __tmc_events.gdb__
    2. __links_events.gdb__
    3. __overlay.gdb__ 
    4. __output_prep.gdb__
3. The user has created an output folder for the final CSV output files named __csv_output__.
  
The creation of the 'empty' geodatabases and folder could be moved into a separate 'initialization' script.
However, given that this tool was intended to be 'run once' on each route - and thus requires 'setup' only onece - the value automating this didn't seem worthwhile.

## Algorithm
The approach implemented by this tool is to use the MassDOT Road Inventory __route system__ as a common 'backbone'
against which the INRIX TMCs and the Model Network links can be located. 

The algorithm proceeds as follows:
1. select the features from the INRIX TMC feature class for the specified route
2. locate these features against the MassDOT route system feature for the specified route
3. select the features from the model links feature class for the specified route
4. locate these features againt the MassDOT route system feature for the specified route
5. overlay (i.e., intersect) the results of \(2\) and \(4\)

This script makes extensive of the ESRI tools __Locate Features Along Routes__ and __Overlay Route Events__.