# conflate_tmcs_and_model_links.py
#
# Usage: conflate_tmcs_and_model_link MassDOT_route_id [list_of_tmcs_file]
#
# This script conflates Statewide Model Links and TMCs onto the MassDOT Road Inventory
#     1. For a given MassDOT "route_id", generate an event table containing the
#        "overlay" (i.e., the logical UNION) of the following events onto it:
#           a. CTPS Model Links
#           b. INRIX TMCs
#     2. Produce a final output CSV file from this event table, each record of which
#        contains a link_id, a tmc ID, the fraction of the given TMC contibuting
#        to the given link_id, and the fraction of the given link_id contributing 
#        to the given tmc ID.
#
# This module depends upon the following modules:
#     1. arcpy
#     2. csv
#
# Ben Krepp 01/07/2020-01/16/2020
# ---------------------------------------------------------------------------

import arcpy
import csv

# Translate MassDOT route_id into INRIX 'roadnum' and INRIX 'direction'
def get_inrix_attrs(MassDOT_route_id):
    # return value
    retval = { 'roadnum' : '', 'direction' : '' }
    # Dict to map MassDOT route direction string to INRIX route direction string
    massdot_to_inrix_direction = { 'NB' : 'Northbound' , 'SB' : 'Southbound', 'EB' : 'Eastbound' , 'WB' : 'Westbound' }   
    pieces = MassDOT_route_id.split(' ')
    if pieces[0].startswith('I'):
        # Interstate route
        roadnum = 'I-' + pieces[0][1:len(pieces[0])]
    elif pieces[0].startswith('US'):
        # US route
        roadnum = 'US-' + pieces[0][2:len(pieces[0])]
    elif pieces[0].startswith('SR'):
        # State route: at least as of Jan 2020, INRIX uses 'RT' instead of 'SR'.
        # Note: I believe I've seen at least some MA state routes indicated by the prefix 'MA' in the ***XD*** shapefile.
        roadnum = 'RT-' + pieces[0][2:len(pieces[0])]
    else:
        # We're not set up to process other kinds of routes, bail out
        arcpy.AddError("Specified route: " + MassDOT_route_id + " has unsupported route_system. Exiting.")
        exit()
    # end_if
    retval['roadnum'] = roadnum
    direction = massdot_to_inrix_direction[pieces[1]]
    # HACK: Handle INRIX incorrectly regarding I-291 as a NB/SB rather than an EB/WB route.
    if roadnum == 'I-291':
        if direction == 'Eastbound':
            direction = 'Northbound'
        else:
            direction = 'Southbound'
    # end_if (HACK)
    retval['direction'] = direction
    return retval
# def get_inrix_attrs()
       
# Script parameters
# First argument, MassDOT route_id is REQUIRED
MassDOT_route_id = arcpy.GetParameterAsText(0)
arcpy.AddMessage("Processing " + MassDOT_route_id) 
MassDOT_route_query_string = "route_id = " + "'" + MassDOT_route_id + "'"
arcpy.AddMessage("MassDOT_route_query_string = " + MassDOT_route_query_string)
# N.B. We've rigged things up so that the MassDOT_route_query_string can be used as the Model_Links_FC_query_string
Model_Links_FC_query_string = MassDOT_route_query_string
arcpy.AddMessage("Model_Links_FC_query_string = " + Model_Links_FC_query_string)

# Second parameter, indicating a file containing a specific list of TMCs, is OPTIONAL    
TMC_list_file = arcpy.GetParameterAsText(1)
if TMC_list_file != '':
    arcpy.AddMessage("TMC_list_file = " + TMC_list_file)
# end_if

if not TMC_list_file:
    INRIX_attrs = get_inrix_attrs(MassDOT_route_id)
    INRIX_roadnum = INRIX_attrs['roadnum']
    INRIX_route_direction = INRIX_attrs['direction']
    INRIX_query_string = "roadnum = " + "'" + INRIX_roadnum + "'" + " AND direction = " + "'" + INRIX_route_direction + "'"
    arcpy.AddMessage("INRIX_roadnum = " + INRIX_roadnum)
    arcpy.AddMessage("INRIX_route_direction = " + INRIX_route_direction)
    arcpy.AddMessage("INRIX_query_string = " + INRIX_query_string)
else:
    f = open(TMC_list_file, 'r')
    str1 = f.read()
    str2 = str1.replace('\n', '')
    INRIX_query_string = "tmc IN (" + str2 + ")"
    arcpy.AddMessage("Using specified list of TMCs.")
    arcpy.AddMessage("INRIX_query_string = " + INRIX_query_string)
# end_if

# Path to "base directory" in which the GDB containing the input Model Links feature class resides
# and in which all output files are written
base_dir = r'\\lilliput\groups\Data_Resources\conflate-tmcs-and-model'


# INPUT DATA: INRIX TMCs, CTPS model links, MassDOT LRSN_Routes 
#
# INRIX TMCs 
INRIX_MASSACHUSETTS_TMC_2019 = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.INRIX_MASSACHUSETTS_TMC_2019'

# Layer containing TMCs selected from the above
INRIX_TMCS = "INRIX_TMCS"

# CTPS model links
CTPS_Model_Links_FC = base_dir + '\model_links.gdb\Statewide_Model_Links_EPSG26986_augmented'
# Layer containing selected CTPS model links
CTPS_Model_Links = "CTPS_Model_Links"

# MassDOT LRSN_Routes
MASSDOT_LRSN_Routes_19Dec2019 = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.MASSDOT_LRSN_Routes_19Dec2019'

# Layer containing route selected from the above
Selected_LRSN_Route = "Selected LRSN Route"


# OUTPUT DATA: Event tables and CSV file

# Names of generated event tables and intermediate CSV file
#
base_table_name = MassDOT_route_id.lower().replace(' ','_')
tmc_event_table_name = base_table_name + "_events_tmc"
links_event_table_name = base_table_name + "_events_links"

overlay_event_table_name = base_table_name + "_events_overlay"

output_event_table_name = base_table_name + "_events_output"
output_csv_file_name = base_table_name + "_events_output.csv"

# Full paths of geodatabases in which event tables are written
#
tmc_event_table_gdb = base_dir + "\\tmc_events.gdb"
links_event_table_gdb = base_dir + "\\links_events.gdb"
overlay_events_gdb = base_dir + "\\overlay.gdb"
output_events_gdb = base_dir + "\\output_prep.gdb"

# Full path of directory in which output CSV file is written
# 
output_csv_dir = base_dir + "\csv_output"

# Full paths of generated event tables
#
tmc_event_table = tmc_event_table_gdb + "\\" + tmc_event_table_name 
links_event_table = links_event_table_gdb + "\\" + links_event_table_name
overlay_events = overlay_events_gdb + "\\" + overlay_event_table_name
output_event_table = output_events_gdb + "\\" + output_event_table_name 

# Full path of generated output CSV file
#
output_csv = output_csv_dir + "\\" + output_csv_file_name

# Name of "table view" created of overlay_events_ (see below)
overlay_events_View = "overlay_event_table_View"
# Name of "table view" created of output_event_table (see below)
output_event_table_View = "output_event_table_View"

# Make Feature Layer "INRIX_TMCS": from INRIX TMCs, select TMCs using the INRIX_query_string
arcpy.MakeFeatureLayer_management(INRIX_MASSACHUSETTS_TMC_2019, INRIX_TMCS, INRIX_query_string, 
                                  "", "objectid objectid HIDDEN NONE;tmc tmc VISIBLE NONE;tmctype tmctype VISIBLE NONE;linrtmc linrtmc HIDDEN NONE;frc frc VISIBLE NONE;lenmiles lenmiles VISIBLE NONE;strtlat strtlat HIDDEN NONE;strtlong strtlong HIDDEN NONE;endlat endlat HIDDEN NONE;endlong endlong HIDDEN NONE;roadnum roadnum VISIBLE NONE;roadname roadname VISIBLE NONE;firstnm firstnm VISIBLE NONE;direction direction VISIBLE NONE;country country HIDDEN NONE;state state HIDDEN NONE;zipcode zipcode HIDDEN NONE;shape shape HIDDEN NONE;st_length(shape) st_length(shape) HIDDEN NONE")

# Make Feature Layer "Selected_LRSN_Route": from MASSDOT LRSN_Routes select route with MassDOT_route_id
arcpy.MakeFeatureLayer_management(MASSDOT_LRSN_Routes_19Dec2019, Selected_LRSN_Route, MassDOT_route_query_string, 
                                   "", "objectid objectid HIDDEN NONE;from_date from_date HIDDEN NONE;to_date to_date HIDDEN NONE;route_system route_system HIDDEN NONE;route_number route_number HIDDEN NONE;route_direction route_direction HIDDEN NONE;route_id route_id VISIBLE NONE;route_type route_type VISIBLE NONE;route_qualifier route_qualifier HIDDEN NONE;alternate_route_number alternate_route_number HIDDEN NONE;created_by created_by HIDDEN NONE;date_created date_created HIDDEN NONE;edited_by edited_by HIDDEN NONE;date_edited date_edited HIDDEN NONE;globalid globalid HIDDEN NONE;shape shape HIDDEN NONE;st_length(shape) st_length(shape) HIDDEN NONE")

arcpy.AddMessage("Generating TMC events.")
#
# Locate Features Along Routes: locate selected TMCs along selected MassDOT route
# Output is: tmc_event_table
# Note XY tolerance of ***40 meters***. This was found to be necessary even for express highways, e.g., case of I-95 @ new bridge over Merrimack River.
tmc_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.LocateFeaturesAlongRoutes_lr(INRIX_TMCS, Selected_LRSN_Route, "route_id", "40 Meters", tmc_event_table, tmc_event_table_properties, 
                                   "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")
# Delete un-needed fields from tmc_event_table
# Be sure to retain "lenmiles" field - the length, in miles of the ENTIRE TMC
arcpy.DeleteField_management(tmc_event_table, "linrtmc;frc;strtlat;strtlong;endlat;endlong;roadname;country;state;zipcode")

arcpy.AddMessage("Generating model link events.")
#
# Make Feature Layer "CTPS_Model_Links": from CTPS_Model_Links_FC, select model links using the INRIX_query_string
arcpy.MakeFeatureLayer_management(CTPS_Model_Links_FC, CTPS_Model_Links, Model_Links_FC_query_string)

# Locate Features Along Routes: locate selected model links along selected MassDOT route
# Output is: links_event_table
links_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.LocateFeaturesAlongRoutes_lr(CTPS_Model_Links, Selected_LRSN_Route, "route_id", "40 Meters", links_event_table, links_event_table_properties, 
                                   "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")
# Be sure to retain "LENGTH" field - the length of the ENTIRE model link
                             
arcpy.AddMessage("Generating overlay.")    
#                            
# HERE: tmc_event_table and links_event_table have been generated.
#       Generate overlay #1.
# Overlay Route Events: inputs: tmc_events, links_events
#                       output: overlay_events
overlay_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.OverlayRouteEvents_lr(tmc_event_table, "route_id LINE from_meas to_meas", 
                            links_event_table, "route_id LINE from_meas to_meas", "UNION", 
                            overlay_events, overlay_event_table_properties, "NO_ZERO", "FIELDS", "INDEX")

# Rename two fields in the overlay table to make their meanings clearer:
#   lenmiles ==> tmc_lenmiles  (length, in miles, of the ENTIRE TMC)
#   LENGTH   ==> link_lenmiles (length, in miles, of the ENTIRE model link)
arcpy.AlterField_management(overlay_events, 'lenmiles', 'tmc_lenmiles')
arcpy.AlterField_management(overlay_events, 'LENGTH', 'link_lenmiles')

# Make Table View of overlay_events
arcpy.MakeTableView_management(overlay_events, overlay_events_View) 

# Roads and Highways allows (among other things) events with measure values < 0. In particular, we are concerned with from_measure values < 0.
# Clean these up by setting the relevant from_measures to 0.
#
# Select records in overlay_events with from_meas < 0, set the from_meas of these records to 0, and clear selection
arcpy.SelectLayerByAttribute_management(overlay_events_View, "NEW_SELECTION", "from_meas < 0")
arcpy.CalculateField_management(overlay_events_View, "from_meas", "0.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(overlay_events_View, "CLEAR_SELECTION", "")

# Sort the table in ascending order on from _meas, and add a "calc_len" (calculated length) field to each record, 
# and calculate its value appropriately.
# Sort overlay_events on from_meas, in ascending order
# output is in output_event_table
arcpy.Sort_management(overlay_events_View, output_event_table, "from_meas ASCENDING;tmc ASCENDING", "UR")

arcpy.AddMessage("Generating output event table.")

# Add a "calc_len" field to output_event_table, and calc it to (to_meas - from_meas)
arcpy.AddField_management(output_event_table, "calc_len", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(output_event_table, "calc_len", "!to_meas! - !from_meas!", "PYTHON_9.3", "")

# Add "fraction_of_tmc_in_link" and "fraction_of_link_in_tmc" fields
arcpy.AddField_management(output_event_table, "fraction_of_tmc_in_link", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.AddField_management(output_event_table, "fraction_of_link_in_tmc", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

# Make Table View of output_event_table
arcpy.MakeTableView_management(output_event_table, output_event_table_View) 

# Calc fraction_of_tmc_in_link
#
# The general formula is: calc_len / tmc_lenmiles
# Exceptions:
#   If tmc_lenmiles == 0, calc fraction_of_tmc_in_link to 0.0
#   If (calc_len / tmc_lenmiles) > 1.0, calc fraction_of_tmc_in_link to 1.0
#
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "tmc_lenmiles = 0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_tmc_in_link", "0.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "tmc_lenmiles <> 0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_tmc_in_link", "!calc_len! / !tmc_lenmiles!", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "fraction_of_tmc_in_link > 1.0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_tmc_in_link", "1.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")

# Calc fraction_of_link_in_tmc 
#
# The general formula is: calc_len / link_lenmiles
# Exceptions:
#   If link_lenmiles == 0, calc fraction_of_link_in_tmc to 0.0
#   If (calc_len / link_lenmiles) > 1.0, calc fraction_of_link_in_tmc to 1.0
#
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "link_lenmiles = 0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_link_in_tmc", "0.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "link_lenmiles <> 0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_link_in_tmc", "!calc_len! / !link_lenmiles!", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "NEW_SELECTION", "fraction_of_link_in_tmc > 1.0")
arcpy.CalculateField_management(output_event_table_View, "fraction_of_link_in_tmc", "1.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(output_event_table_View, "CLEAR_SELECTION", "")

# Export final_event_table to CSV file
arcpy.AddMessage("Exporting output event table to CSV file.")

open_fn = output_csv_dir + "\\" + "processed_" + output_csv_file_name
                  
csv_fieldnames = ['link_id', 'tmc', 'fraction_of_tmc_in_link', 'fraction_of_link_in_tmc', \
                 'tmc_lenmiles', 'link_lenmiles', 'calc_len', 'from_meas', 'to_meas', 'route_id', 'firstnm']

with open(open_fn, 'wb') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
    writer.writeheader()
    for row in arcpy.SearchCursor(output_event_table):
        writer.writerow({ 'link_id'                 : row.getValue('ID'), \
                          'tmc'                     : row.getValue('tmc'), \
                          'fraction_of_tmc_in_link' : row.getValue('fraction_of_tmc_in_link'), \
                          'fraction_of_link_in_tmc' : row.getValue('fraction_of_link_in_tmc'), \
                          'tmc_lenmiles'            : row.getValue('tmc_lenmiles'), \
                          'link_lenmiles'           : row.getValue('link_lenmiles'), \
                          'calc_len'                : row.getValue('calc_len'), \
                          'from_meas'               : row.getValue('from_meas'), \
                          'to_meas'                 : row.getValue('to_meas'), \
                          'route_id'                : row.getValue('route_id'), \
                          'firstnm'                 : '"' + row.getValue('firstnm') + '"'})
    # for
# with

arcpy.AddMessage("*** Finished CSV export for: " + MassDOT_route_id + ". Final output is in: " + output_csv_dir + "\\" + output_csv_file_name)