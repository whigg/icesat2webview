#!/usr/bin/python3


"""

syntax: db-path [file-1.h5 [file-2.h5 [...]]] 

the db-path must be non existent
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


ZOOM_LEVEL=11
tilesStore= {}
coordsCnt=0
# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
  return (xtile, ytile)


def store(filename,channel,rgt,time,lat,lon,terrain,canopy):
   global coordsCnt
   key=deg2num(lat,lon,ZOOM_LEVEL)
   payload=filename+";"+channel+";"+str(rgt)+";"+str(time)+";"+str(lat)+";"+str(lon)+";"+str(terrain)+";"+str(canopy)
   # print("=="+payload)
   tilesStore.setdefault(key, []).append(payload)
   coordsCnt=coordsCnt+1


def processFile(filename):
    print("processFile "+filename)
    f = h5py.File(filename)
    #list(f.keys())
    #['METADATA', 'ancillary_data', 'ds_geosegments', 'ds_metrics', 'ds_surf_type', 'gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r', 'orbit_info', 'quality_assessment']



    channels = ['1l', '1r','2l', '2r','3l', '3r']
    for channel in channels:


        ancillary_data=f['/ancillary_data']

        print(filename+":"+" reading channel:"+channel)
        

        land_segments=f['/gt'+channel+'/land_segments']
        terrain=f['/gt'+channel+'/land_segments/terrain']
        canopy=f['/gt'+channel+'/land_segments/canopy']

        ##print("ancillary_data" ,ancillary_data.keys())
        ##start_delta_time=ancillary_data['start_delta_time'][0]
        ##print("start_delta_time:",start_delta_time)
        ##print("land_segments" ,land_segments.keys())
        ##print("terrain" ,terrain.keys())
        ##print("canopy" ,canopy.keys())


        for x in list(zip(
        land_segments['rgt'],  
        land_segments['delta_time'],
        land_segments['latitude'],
        land_segments['longitude'],
        terrain['h_te_best_fit'],
        #canopy['canopy_flag'],
        canopy['h_canopy'],
        )):
          if (x[5]<1000):
            store('',channel,x[0],x[1],x[2],x[3],x[4],x[5])


#
# empty the store
#
def resetStore():
    tilesStore= {}
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

      # BRITTLE 
      with gzip.open(tileCsvGz, 'wt') as fout:
          fout.write(tileCsvText)
          for line in tilesStore[tile]:
              print(line,file=fout)

  






#-- main --
def main(storePath,granules):

  
  srcs={}
  
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





  for filename in granules:
      if (filename in srcs):
        print(filename+":already loaded")
      else :  
        resetStore()
        processFile(filename)
        saveStore(storePath)
        srcInfoLine=datetime.datetime.now().replace(microsecond=0).isoformat()+";"+str(coordsCnt)+" records in "+str(len(tilesStore))+" tiles "
        print(filename+":"+srcInfoLine)
        with open(storePath+"/src.txt", 'a+') as out:
          print(filename+";"+srcInfoLine,file=out)





main ( storePath=sys.argv[1], granules=sys.argv[2:])