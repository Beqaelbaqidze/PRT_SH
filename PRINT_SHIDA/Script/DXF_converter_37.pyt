import arcpy
import os
import pythonaddins


class Toolbox(object):
    def __init__(self):
        self.label = "CAD to SHP Converter"
        self.alias = "cadconverter"
        self.tools = [DXFToSHPTool]

class DXFToSHPTool(object):
    def __init__(self):
        self.label = "Convert CAD Polylines to Scaled Polygon (EPSG:32637)"
        self.description = "Supports DXF and DWG. Scales polylines, converts to polygons, and appends to MDB."
        self.canRunInBackground = False

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input CAD File (DXF or DWG)",
            name="in_cad",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = ['dxf', 'dwg']  # Accept both formats

        param1 = arcpy.Parameter(
            displayName="Output Folder",
            name="out_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Output"
        )

        param2 = arcpy.Parameter(
            displayName="Scale Factor (default: 0.001)",
            name="scale_factor",
            datatype="Double",
            parameterType="Optional",
            direction="Input"
        )
        param2.value = 0.001

        return [param0, param1, param2]

    def execute(self, parameters, messages):
        try:
            cad_path = parameters[0].valueAsText
            output_folder = parameters[1].valueAsText
            scale_factor = float(parameters[2].valueAsText or 0.001)

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            temp_polyline = os.path.join(output_folder, "temp_polyline.shp")
            merged_polyline = os.path.join(output_folder, "merged_polyline.shp")
            scaled_polyline = os.path.join(output_folder, "scaled_polyline.shp")
            final_polygon = os.path.join(output_folder, "final_polygon.shp")

            spatial_ref = arcpy.SpatialReference(32637)

            base_path = os.environ.get("PRINT_SHIDA_PATH")
            if not base_path:
                raise Exception("PRINT_SHIDA_PATH environment variable is not set.")

            mdb_path = os.path.join(base_path, "SHIDA_AZOMVEBI_37.mdb")
            mdb_polygon_layer = os.path.join(mdb_path, "SHIDA_AZOMVEBI", "unit_polygon")

            if not arcpy.Exists(cad_path):
                raise Exception("The CAD file does not exist: " + cad_path)

            polyline_layer = cad_path + "\\Polyline"
            if not arcpy.Exists(polyline_layer):
                raise Exception("No 'Polyline' feature found in CAD file.")

            arcpy.FeatureClassToFeatureClass_conversion(polyline_layer, output_folder, "temp_polyline")
            arcpy.DefineProjection_management(temp_polyline, spatial_ref)

            arcpy.Dissolve_management(temp_polyline, merged_polyline)

            arcpy.CopyFeatures_management(merged_polyline, scaled_polyline)
            arcpy.DefineProjection_management(scaled_polyline, spatial_ref)

            with arcpy.da.UpdateCursor(scaled_polyline, ["SHAPE@"]) as cursor:
                for row in cursor:
                    parts = []
                    for part in row[0]:
                        scaled_part = arcpy.Array([
                            arcpy.Point(pt.X * scale_factor, pt.Y * scale_factor)
                            for pt in part if pt
                        ])
                        parts.append(scaled_part)
                    row[0] = arcpy.Polyline(arcpy.Array(parts), spatial_ref)
                    cursor.updateRow(row)

            arcpy.FeatureToPolygon_management(scaled_polyline, final_polygon, "", "NO_ATTRIBUTES", "")
            arcpy.DefineProjection_management(final_polygon, spatial_ref)

            arcpy.Append_management(final_polygon, mdb_polygon_layer, "NO_TEST")
            messages.addMessage("✅ Polygon imported into MDB: " + mdb_polygon_layer)

            try:
                mxd = arcpy.mapping.MapDocument("CURRENT")
                df = arcpy.mapping.ListDataFrames(mxd)[0]
                temp_layer = arcpy.MakeFeatureLayer_management(final_polygon, "temp_zoom_layer")
                extent = arcpy.Describe(temp_layer).extent
                df.extent = extent
                arcpy.RefreshActiveView()
                arcpy.Delete_management(temp_layer)
                messages.addMessage("✅ Zoomed to imported polygons.")
            except Exception as zoom_ex:
                messages.addWarningMessage("⚠ Zoom failed: " + str(zoom_ex))

        except Exception as e:
            messages.addErrorMessage("❌ Error: " + str(e))
            arcpy.AddError("Error Details: " + str(e))
