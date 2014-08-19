"""
prepare shading/context geometries

    Args:
        northVectorOrRotation: A vector that shows North or a number that shows
                               the rotation of the North from the Y axis
        bldgMasses: List of closed Breps as thermal zones.
    Returns:
        report: ...
        thermalZones: Thermal zone's geometries for visualiza
"""

ghenv.Component.Name = 'Honeybee EP context Surfaces'
ghenv.Component.NickName = 'HB_EPContextSrf'
ghenv.Component.Message = 'VER 0.0.53\nAUG_19_2014'
ghenv.Component.Category = "Honeybee"
ghenv.Component.SubCategory = "09 | Energy | Energy"
ghenv.Component.AdditionalHelpFromDocStrings = "1"

import rhinoscriptsyntax as rs
import Rhino as rc
import scriptcontext as sc
import os
import System
import Grasshopper.Kernel as gh
import uuid

tolerance = sc.doc.ModelAbsoluteTolerance
import math


def main(shdSurfaces, EPTransSchedule, meshingSettings, justBoundingBox):
    
    # import the classes
    if sc.sticky.has_key('honeybee_release'):
        
        # don't customize this part
        hb_EPSrf = sc.sticky["honeybee_EPSurface"]
        hb_EPSHDSurface = sc.sticky["honeybee_EPShdSurface"]
        hb_RADMaterialAUX = sc.sticky["honeybee_RADMaterialAUX"]()
        hb_EPObjectsAux = sc.sticky["honeybee_EPObjectsAUX"]()
        HBScheduleList = sc.sticky["honeybee_ScheduleLib"]["List"]

        ########################################################################
        #----------------------------------------------------------------------#
        shdBreps = []
        # create bounding box of shading geometries
        if justBoundingBox:
            for brep in shdSurfaces:
                if brep.Faces.Count>1 or not brep.Faces[0].IsPlanar(sc.doc.ModelAbsoluteTolerance):
                    shdBreps.append(brep.GetBoundingBox(True).ToBrep())
                else:
                    shdBreps.append(brep)
        else: shdBreps = shdSurfaces
        
        shadingClasses = []
        shadingMeshPreview = []
        
        if meshingSettings == None:
            mp = rc.Geometry.MeshingParameters.Minimal
            mp.SimplePlanes = True
        else:
            mp = meshingSettings
        
        def getRadMaterialName(radMaterial):
            nameStr = radMaterial.split(" ")[2]
            name =  nameStr.split("\n")[0]
            return name
        
        for brepCount, brep in enumerate(shdBreps):
            if len(brep.DuplicateEdgeCurves(False))>1:
                
                meshArray = rc.Geometry.Mesh.CreateFromBrep(brep, mp)
                for mesh in meshArray:
                    for meshFace in range(mesh.Faces.Count):
                        vertices = list(mesh.Faces.GetFaceVertices(meshFace))[1:]
                        vertices = vertices + [sc.doc.ModelAbsoluteTolerance]
                        # create the brep from mesh
                        shdBrep = rc.Geometry.Brep.CreateFromCornerPoints(*vertices)
                        
                        thisShading = hb_EPSHDSurface(shdBrep, 1000*brepCount + meshFace, 'shdSrf_' + `brepCount` + '_' + `meshFace` + "_" + str(uuid.uuid4()))
                        
                        # add transmittance schedule if any
                        if EPTransSchedule!=None:
                            schedule= EPTransSchedule.upper()
                            if schedule!=None and not schedule.lower().endswith(".csv") and schedule not in HBScheduleList:
                                msg = "Cannot find " + schedule + " in Honeybee schedule library."
                                print msg
                                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
                                return -1
                            elif schedule!=None and schedule.lower().endswith(".csv"):
                                # check if csv file is existed
                                if not os.path.isfile(schedule):
                                    msg = "Cannot find the shchedule file: " + schedule
                                    print msg
                                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, msg)
                                    return -1
                            
                            thisShading.TransmittanceSCH = schedule
                        
                        # add the Rad Material if any
                        if RADMaterial!=None:
                            # if it is just the name of the material make sure it is already defined
                            if len(RADMaterial.split(" ")) == 1:
                                # if the material is not in the library add it to the library
                                if RADMaterial not in sc.sticky ["honeybee_RADMaterialLib"].keys():
                                    warningMsg = "Can't find " + RADMaterial + " in RAD Material Library.\n" + \
                                                "Add the material to the library and try again."
                                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                                    return
                                
                                try:
                                    thisShading.setRADMaterial(RADMaterial)
                                except Exception, e:
                                    print e
                                    warningMsg = "You are using an old version of Honeybee_Honeybee! Update your files and try again."
                                    print warningMsg
                                    ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                                    return
                                
                                addedToLib = True
                            else:
                                
                                # try to add the material to the library
                                addedToLib, thisShading.RadMaterial = hb_RADMaterialAUX.analyseRadMaterials(RADMaterial, True)
                                
                            if addedToLib==False:
                                warningMsg = "Failed to add " + RADMaterial + " to the Library."
                                ghenv.Component.AddRuntimeMessage(gh.GH_RuntimeMessageLevel.Warning, warningMsg)
                                return
                        
                        # add shading to the list
                        shadingClasses.append(thisShading)
            
        # add to the hive
        hb_hive = sc.sticky["honeybee_Hive"]()
        HBContext  = hb_hive.addToHoneybeeHive(shadingClasses, ghenv.Component.InstanceGuid.ToString())
        return HBContext
        ################################################################################################
    else:
        print "You should first let Honeybee to fly..."
        w = gh.GH_RuntimeMessageLevel.Warning
        ghenv.Component.AddRuntimeMessage(w, "You should first let Honeybee to fly...")
        return -1
        

if _shdSurfaces and _shdSurfaces[0]!=None:
    # add cleaning function
    result= main(_shdSurfaces, EPTransSchedule_, meshingSettings_, justBoundingBox_)
    
    if result != -1: HBContext = result