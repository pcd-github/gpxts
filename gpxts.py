

# add timestamps to a manually-created gpx file so that strava can use it
import sys
import re
from datetime import datetime, date, time, timedelta 
from xml.dom import minidom
from geopy import distance

def calcTotalDistance (trkptList) :
    totalDist = 0
    trkptCurr = 0
    lastLat = 0
    lastLon = 0

    for tp in trkptList:
        currLat = tp.attributes['lat'].value
        currLon = tp.attributes['lon'].value
        
        if (0 < trkptCurr) :
            totalDist += distance.distance((currLat, currLon), (lastLat, lastLon)).miles
            
        lastLat = currLat
        lastLon = currLon
        trkptCurr += 1

    return totalDist

def generateTimestamp (xmldoc, dtCurr, tp) :
    timeTag = 'time'

    strTimestamp = dtCurr.isoformat()
    newTimeElem = xmldoc.createElement(timeTag)
    tp.appendChild(newTimeElem)
    newTimeText = xmldoc.createTextNode(strTimestamp)
    newTimeElem.appendChild(newTimeText)

def interpolateTrackpoints (xmldoc, tp, lastLat, lastLon, currLat, currLon, deltaTime, dtCurr) :
    interLat = lastLat
    deltaLat = (currLat - lastLat) / deltaTime
    interLon = lastLon
    deltaLon = (currLon - lastLon) / deltaTime
    tpTag = 'trkpt'
    latName = 'lat'
    lonName = 'lon'
    interp = 'interpolated'
    tpParent = tp.parentNode

    # i is assumed to indicate delta in seconds
    for i in range (1, deltaTime) :
        # create new trackpoint with the interpolated lat/lon values
        newTP = xmldoc.createElement(tpTag)
        newTP.setAttribute(latName, str((i * deltaLat) + lastLat))        
        newTP.setAttribute(lonName, str((i * deltaLon) + lastLon))
        newTP.setAttribute(interp, str(i))

        # add timestamp to it       
        generateTimestamp(xmldoc, dtCurr + timedelta(seconds=i), newTP)
        tpParent.insertBefore(newTP, tp)

def modifyTrkPts (inFile, outFile, dtStart, totalDur) :
    trkptTag = 'trkpt'
    xmldoc = minidom.parse(inFile)
    trkptList = xmldoc.getElementsByTagName(trkptTag)
    totalDist =  calcTotalDistance(trkptList)
    trkptCount = trkptList.length
    trkptCurr = 0
    lastLat = 0
    lastLon = 0
    dtCurr = dtStart
    currDist = 0
    calcTrkptPace = 0
    uniformPace = totalDur / totalDist

    for tp in trkptList:
        currLat = tp.attributes['lat'].value
        currLon = tp.attributes['lon'].value
        
        if (0 < trkptCurr) :
            currDist = distance.distance((currLat, currLon), (lastLat, lastLon)).miles
            
        # figure out the new time delta
        pctOfTimePerTrkPt = currDist / totalDist
        incSecs = float(totalDur * 60.0) * pctOfTimePerTrkPt
        deltaTime = int(incSecs)
        td = timedelta(seconds=deltaTime)

        # interpolate to 1s resolution per trackpoint
        if (1 < deltaTime) :
            interpolateTrackpoints (xmldoc, tp, float(lastLat), float(lastLon), float(currLat), float(currLon), deltaTime, dtCurr)

        dtCurr += td
        generateTimestamp (xmldoc, dtCurr, tp)
        deltaMin = deltaTime / 60

        trkptCurr += 1
        lastLat = currLat
        lastLon = currLon

    f= open(outFile,"w+")
    f.write(xmldoc.toxml())
    f.close()


try:
    inFile = sys.argv[1]
    outFile = sys.argv[2]
    sDate = sys.argv[3]
    sTime = sys.argv[4]
    sTZ = sys.argv[5]
    totalDur = int(sys.argv[6])

    dtNow = datetime.now()
    # print(dtNow.strftime("%d/%m/%Y %H:%M:%S %Z"))
    # print('timezone ', dtNow.strftime("%Z"))

    strDT = sDate + ' ' + sTime + ' ' + sTZ
    dtStart = datetime.strptime(strDT, '%Y-%m-%d %H:%M:%S %z')

    modifyTrkPts(inFile, outFile, dtStart, totalDur)
    
except :
    print ('usage : ', sys.argv[0], 'infile outfile <start date> <start time> <UTC offset, e.g. -0800> <duration in minutes> : eg python3 gpxts.py gpx/20220309-route4889746135.gpx gpx/20220309-2.gpx 2022-03-09 12:30:00 -0700 60')
