## web view: ##

Advantages over the original map:
* shows a background map, not a aerial
* button to center map to current position
* all data available in the area is presented immediately (no need to choose rgt nor date range)
* displays both wgs84 elevation and geoid elevation 



DONE:
add track to show the 100 meters segemnts (hard bit: compute track) DONE in hacky way
store tiles on s3 compressed DONE
minimap: DONE
nice sattelite view button DONE
geoid elevation DONE
publish . webpack + amazon
link to photon data

TODO:
database tiles boundary (i.e. just min and max tile)



# upload to aws
npm run build && \
aws s3 cp /home/bc/bruno/work/rinkai/gitted/brunesto/icesat2webview/web/dist/index.html  s3://icesat2webview/ && \
aws s3 sync --no-follow-symlinks /home/bc/bruno/work/rinkai/gitted/brunesto/icesat2webview/web/dist/site  s3://icesat2webview/site


browse directly thru s3 (so cloudfront is not required?)
https://icesat2webview.s3.eu-central-1.amazonaws.com/index.html


https://d3863ripe95iiz.cloudfront.net/index.html


Notes:

webpack/babel setup following https://github.com/taniarascia/webpack-boilerplate


# npm for handling KML:
https://www.npmjs.com/package/leaflet-plugins


# nice sample tiles
https://a.tile.openstreetmap.org/15/17748/11185.png
http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/15/11185/17748

# extract bottom 100x100px:
curl -o /tmp/11185.png https://b.basemaps.cartocdn.com/dark_all/15/17658/11112.png
convert  /tmp/11185.png -crop 100x100+156+156 light.png




looking @ 50.25283,13.988055, the link to openaltimetry fails, 

https://openaltimetry.org/data/icesat2/elevation?minx=13.98000000000000&miny=50.25245200000000&maxx=13.98900000000000&maxy=50.25320800000000&zoom_level=16&beams=1,2,3,4,5,6&tracks=305&date=2018-10-18&product=ATL08&mapType=geographic&tab=photon

but this one works :... dunno why

https://openaltimetry.org/data/icesat2/elevation?minx=13.98000000000000&miny=50.25245200000000&maxx=13.98900000000000&maxy=50.25310800000000&zoom_level=16&beams=1,2,3,4,5,6&tracks=305&date=2018-10-18&product=ATL08&mapType=geographic&tab=photon