#!/usr/bin/python3


"""

syntax: db-path -[fd] [file-1.h5 [file-2.h5 [...]]] 

-f forces
-d add debug info

the h5 files will be all parsed and the relevant data extracted into tiles at zoomlevel 11,
the tiles are saved in the db path

tile format:
each tile consists of a simple csv file


"""

import gzip
import sys
import h5py
import numpy as np
import os
import re
import datetime

import math

CHANNELS = ['1l', '1r','2l', '2r','3l', '3r']
#CHANNELS =['1l']

ZOOM_LEVEL=11
tilesStore= {}
coordsCnt=0
# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def coords2tilexy(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def recordPoint(filename,channel,rgt,time,lat,lon,terrain,canopy,direction):
   global coordsCnt
   key=coords2tilexy(lat,lon,ZOOM_LEVEL)
   payload=filename+";"+channel+";"+str(rgt)+";"+str(round(time,3))+";"+str(lat)+";"+str(lon)+";"+str(terrain)+";"+str(canopy)+";"+str(direction)
   #print("=="+payload)
   tilesStore.setdefault(key, []).append(payload)
   coordsCnt=coordsCnt+1

def dumpAll(prefix,group,maxRow):
    for key in group.keys():
      is_dataset = isinstance(group[key], h5py.Dataset)
      #print(key+": "+str(is_dataset))
      if (not is_dataset):
          dumpAll(prefix+"/"+key,group[key],maxRow)
      else:
        for i in range(min(maxRow,len(group[key]))) :
          print(prefix+"/"+key+"["+str(i)+"]:"+str(group[key][i]))  


def processFile(filename,addDebugInfo):

    

    print("processFile "+filename)
    f = h5py.File(filename)

    #dumpAll("", f,3306)
    #return

    #list(f.keys())
    #['METADATA', 'ancillary_data', 'ds_geosegments', 'ds_metrics', 'ds_surf_type', 'gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r', 'orbit_info', 'quality_assessment']
    debugInfo=""
    if (addDebugInfo):
       debugInfo=os.path.basename(filename)

    
    for channel in CHANNELS:


        ancillary_data=f['/ancillary_data']
        orbit_info=f['/orbit_info']
        #dump('/orbit_info',orbit_info,0)
        print(filename+":"+" reading channel:"+channel)
        

        land_segments=f['/gt'+channel+'/land_segments']
        terrain=f['/gt'+channel+'/land_segments/terrain']
        canopy=f['/gt'+channel+'/land_segments/canopy']
        signal_photons=f['/gt'+channel+'/signal_photons']
        
        #print("ancillary_data" ,ancillary_data.keys())
        ##start_delta_time=ancillary_data['start_delta_time'][0]
        ##print("start_delta_time:",start_delta_time)
        ##print("land_segments" ,land_segments.keys())
        ##print("terrain" ,terrain.keys())
        ##print("canopy" ,canopy.keys())

        # previous latitude - 999 means uninitialized
        plat=-999
        for i, x in enumerate(zip(
        land_segments['rgt'],  
        land_segments['delta_time'],
        land_segments['latitude'],
        land_segments['longitude'],
        terrain['h_te_best_fit'],
        #canopy['canopy_flag'],
        canopy['h_canopy'],
        signal_photons['ph_segment_id'],
        signal_photons['classed_pc_indx']

        )):
           

         
          if (x[5]<1000):
            #print("#"+str(i))
            lat=x[2]
            #dump("signal_photons",signal_photons,i)
            #dump("land_segments",land_segments,i)
            #dump("canopy",canopy,i)
            #dump("terrain",terrain,i)

            
            #  hacky detection of rgt direction
            if (not (plat == -999) and plat>lat):
              direction='s'
            else:
              direction='n'  

            recordPoint(debugInfo,channel,x[0],x[1],lat,x[3],x[4],x[5],direction)
            #print("ph_segment_id:",str(x[6]))
            #print("classed_pc_indx:",str(x[7]))
            #return
            plat=lat


#
# empty the store
#
def resetStore():
    global tilesStore
    tilesStore={}
    global  coordsCnt
    coordsCnt=0


#
# store the store :)
#
def saveStore(storePath):
  for tile in tilesStore:
      # print(tile)
      # tile[0]
      latDir=storePath+"/"+str(ZOOM_LEVEL)+"/"+str(tile[0])
      
      os.makedirs(latDir, exist_ok=True)
      tileCsv=latDir+"/"+str(tile[1])+".csv"
      tileCsvGz=tileCsv+".gz"
      # print(tileCsv+" has "+str(len(tilesStore[tile]))+" records")


    
      if (os.path.exists(tileCsvGz)):
        with gzip.open(tileCsvGz, 'rt') as fin:          
          tileCsvText = fin.read()
      else:          
          tileCsvText=""

      #if (tile[0]==1103 and tile[1]==694):
      #  print("====================================")
      #  print("tileCsvGz:"+tileCsvGz)
      #  print("tileCsvText:"+tileCsvText)
      #  print("new lines:"+tileCsvText)
      #  for line in tilesStore[tile]:
      #        print(line)
      #  print("====================================")

      # BRITTLE 
      with gzip.open(tileCsvGz, 'wt') as fout:
          fout.write(tileCsvText)
          for line in tilesStore[tile]:
              print(line,file=fout)

  






#-- main --
def main(storePath,options,granules):

  
  addDebugInfo="d" in options
  force="f" in options

  srcs={}
  
  # open or create src.txt (the list of already processed h5 files)
  if (not os.path.exists(storePath)):
     print("new tiles db will be created: "+storePath)
     os.mkdir(storePath) 
     open(storePath+"/src.txt", 'a').close()     
  else:
     print("found existing tiles db: "+storePath)



  with open(storePath+"/src.txt") as f:
      for line in f.read().splitlines():
        tokens=re.split(';',line)
        srcs[tokens[0]]=tokens[1:]
        print(tokens[0]+";"+line)

  print("channels:"+str(CHANNELS))

  # process each h5 file

  for filename in granules:
      if (not os.path.exists(filename)):
        print(filename+": does not exists")
      elif (not force and os.path.basename(filename) in srcs):
        print(filename+":already loaded")
      else :  
        resetStore()
        processFile(filename,addDebugInfo)
        saveStore(storePath)
        srcInfoLine=datetime.datetime.now().replace(microsecond=0).isoformat()+";"+str(coordsCnt)+" records in "+str(len(tilesStore))+" tiles "
        print(os.path.basename(filename)+":"+srcInfoLine)
        with open(storePath+"/src.txt", 'a+') as out:
          print(os.path.basename(filename)+";"+srcInfoLine,file=out)



# main

if (not sys.argv[2].startswith("-")):
    print ("2nd param must start with dash")
    exit(1)

main ( storePath=sys.argv[1], options=sys.argv[2],granules=sys.argv[3:])