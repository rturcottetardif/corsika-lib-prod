import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

import numpy as np
from math import cos, sin, pi
import pathlib

DrawScintHub = True
DrawScint = True
DrawIceTop = True
DrawAnt = True
DrawCircle = False
DrawArrow = True

InICCoords = True  #If false, this will be in CORSIKA coords

antArmLength = 72/2.

magneticEast = -8.557
magneticNorth = 14.399
#Angle between IC coords and CORSIKA coords ~= 120.72 deg
MagRotation = np.arctan2(magneticNorth, magneticEast)

def qualitative_colors(n):
    if n < 1:
        raise ValueError('Minimum number of qualitative colors is 1.')
    elif n > 12:
        raise ValueError('Maximum number of qualitative colors is 12.')
    cols = ['#4477AA', '#332288', '#6699CC', '#88CCEE', '#44AA99', '#117733',
            '#999933', '#DDCC77', '#661100', '#CC6677', '#AA4466', '#882255',
            '#AA4499']
    indices = [[0],
               [0, 9],
               [0, 7, 9],
               [0, 5, 7, 9],
               [1, 3, 5, 7, 9],
               [1, 3, 5, 7, 9, 12],
               [1, 3, 4, 5, 7, 9, 12],
               [1, 3, 4, 5, 6, 7, 9, 12],
               [1, 3, 4, 5, 6, 7, 9, 11, 12],
               [1, 3, 4, 5, 6, 7, 8, 9, 11, 12],
               [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12],
               [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
    return [cols[ix] for ix in indices[n - 1]]

totalColors = DrawScintHub + DrawScint + DrawIceTop + DrawAnt

myColors = qualitative_colors(totalColors)


scintHubX = np.array([])
scintHubY = np.array([])
scintArmX = np.array([])
scintArmY = np.array([])

if InICCoords:
  rotangle = 0.
else:
  rotangle = MagRotation

rot = np.array([[cos(rotangle), -1*sin(rotangle)], [sin(rotangle), cos(rotangle)]])


########################################
####Make the scintillator plots
########################################

file = open(str(pathlib.Path(__file__).parent.absolute())+"/../resources/CoordinateScintillator.txt", "r")

NScintPerStation = 8
NScintPerLocation = 2
NSpoke = int((NScintPerStation - NScintPerLocation) / NScintPerLocation)
scintLoc = []
stationNumbers = []

for i, line in enumerate(file):
  columns = line.split()
  stnID = int(columns[0])
  panelID = int(columns[1])
  x = float(columns[2])
  y = float(columns[3])

  if panelID != i % NScintPerStation:
    print("Unexpected station ID found")
    print("Expected", i % NScintPerStation, "and got", panelID)
    print("Maybe you have the wrong \"NScintPerStation\" set?")
    exit()


  if not stnID in stationNumbers:
    stationNumbers.append(stnID)

  position = np.array([x,y])
  position = position.dot(rot)

  scintLoc.append(position)

  x = position[0]
  y = position[1]


  if panelID < NScintPerLocation:
    scintHubX = np.append(scintHubX, [x])
    scintHubY = np.append(scintHubY, [y])

  else:
    scintArmX = np.append(scintArmX, [x])
    scintArmY = np.append(scintArmY, [y])

file.close()



########################################
####Make the New antenna locations
########################################

file = open(str(pathlib.Path(__file__).parent.absolute())+"/../resources/CoordinateScintillator.txt", "r")

stations = np.zeros(shape=(8,2))

antx = []
anty = []
antn = []

for i in range(int(len(scintLoc) / NScintPerStation)):
  ibase = i * NScintPerStation

  poshub = (np.array(scintLoc[ibase + 0]) + np.array(scintLoc[ibase + 1])) / 2.

  ispoke = 0
  for j in range(NSpoke):

    spoke1 = np.array(scintLoc[ibase + NScintPerLocation + ispoke + 0])
    spoke2 = np.array(scintLoc[ibase + NScintPerLocation + ispoke + 1])

    ispoke += 2

    posspoke = (spoke1 + spoke2) / 2.

    vec = posspoke - poshub
    vec /= np.linalg.norm(vec)

    posant1 = vec * antArmLength + poshub

    antx.append(posant1[0]) 
    anty.append(posant1[1]) 
    antn.append(len(antx))


########################################
####Make SD tank locations
########################################
file = open (str(pathlib.Path(__file__).parent.absolute())+"/../resources/CoordinateSD.txt", "r")

sdx = np.array([])
sdy = np.array([])

cantx = np.array([])
canty = np.array([])

tempx = 0
tempy = 0

for line in file:
  columns = line.split()
  panelID = int(columns[0])
  letter = columns[1]
  x = float(columns[2])
  y = float(columns[3])
  z = float(columns[4])
  data = int(columns[5])

  ####Rotate
  position = np.array([x,y])
  position = position.dot(rot)

  x = position[0]
  y = position[1]


  sdx = np.append(sdx, x)
  sdy = np.append(sdy, y)

  if letter == 'A':
    tempx = x
    tempy = y
  else:
    tempx = (tempx + x) / 2.
    tempy = (tempy + y) / 2.

    cantx = np.append(cantx, tempx)
    canty = np.append(canty, tempy)


fig = plt.figure()
ax = fig.add_subplot(1,1,1)
ax.grid(color='lightgrey', linewidth=1.2)

icolor = 0

if DrawIceTop:
  ax.scatter(sdx, sdy, color=myColors[icolor], marker='.', label='IceTop', alpha=0.5)
  icolor += 1

##The scintillators
if DrawScintHub or DrawScint:
  ax.plot(scintHubX, scintHubY, color=myColors[icolor], marker='s', markersize=3.5, linestyle="none", label='Scint. Hub')
  icolor += 1

if DrawScint:
  ax.plot(scintArmX, scintArmY, color=myColors[icolor], marker='s', markersize=3.5, linestyle="none", label='Scint')
  icolor += 1

if DrawAnt:
  ax.scatter(antx, anty, color=myColors[icolor], marker='*', label='Antenna')
  icolor += 1
  # for i, txt in enumerate(antn):
  #   ax.annotate(txt, (antx[i], anty[i]))

arrowX = 620.
arrowY = -400.
arrowR = 100.

if DrawArrow:
  ylow, yhigh = ax.get_ylim()
  xlow, xhigh = ax.get_xlim()

  arrowX = (xhigh - xlow) * 0.95 + xlow
  arrowY = (yhigh - ylow) * 0.1 + ylow

  if InICCoords:
    angle = -1*MagRotation
    rot = np.array([[cos(angle), -1*sin(angle)], [sin(angle), cos(angle)]])

    darrow = np.array([arrowR, 0])
    darrow = darrow.dot(rot)
  else:
    angle = (MagRotation - np.pi/2)
    rot = np.array([[cos(angle), -1*sin(angle)], [sin(angle), cos(angle)]])

    darrow = np.array([arrowR, 0])
    darrow = darrow.dot(rot)

  plt.arrow(arrowX, arrowY, darrow[0], darrow[1], head_width=10)

  if darrow[1] > 0:
    vertAlign = "top" 
  else:
    vertAlign = "bottom" 

  if InICCoords:
    ax.text(arrowX, arrowY, 'Mag. North', horizontalalignment='center', verticalalignment=vertAlign)
  else:
    ax.text(arrowX, arrowY, 'Coord. North', horizontalalignment='center', verticalalignment=vertAlign)

if DrawCircle:
  circ3 = plt.Circle((0,0), radius=300, color='k', fill=False)
  ax.add_patch(circ3)
  circ4 = plt.Circle((0,0), radius=400, color='r', fill=False)
  ax.add_patch(circ4)
  circ5 = plt.Circle((0,0), radius=500, color='b', fill=False)
  ax.add_patch(circ5)

ax.legend(framealpha=0.93)

if not InICCoords:
  ax.set_xlabel('Magnetic North [m]')
  ax.set_ylabel('Magnetic West [m]')
  whichCoords = "CORSIKA Coords"
else:
  ax.set_xlabel('East [m]')
  ax.set_ylabel('North [m]')
  whichCoords = "IC Coords"

ax.set_title('Surface Upgrade Array Layout ('+whichCoords+")")

ax.set_aspect('equal', adjustable='datalim')


plt.savefig(str(pathlib.Path(__file__).parent.absolute())+"/../resources/ArrayPlot.pdf")
print("Made file", str(pathlib.Path(__file__).parent.absolute())+"/../resources/ArrayPlot.pdf")

if not InICCoords:
  file = open(str(pathlib.Path(__file__).parent.absolute())+"/../resources/BaseList.list", "w")

file2 = open(str(pathlib.Path(__file__).parent.absolute())+"/../resources/AntennaLocations.txt", "w")
if InICCoords:
  file2.write("Antenna locations in IC Coordinates\n")
  file2.write("StnID, AntID, East [m], North [m], Altitude [m]\n")
else:
  file2.write("Antenna locations in CORSIKA Coordinates\n")
  file2.write("StnID, AntID, Mag North [m], Mag West [m], Altitude [m]\n")

for i in range(len(antx)):
  x = antx[i] * 1.e2
  y = anty[i] * 1.e2
  stationID = stationNumbers[int(i/NSpoke)]
  spokeID = int(i % NSpoke) + 100

  if not InICCoords:
    file.write("AntennaPosition = {0:0.3f} \t{1:0.3f} \t{2} \tant_{3}_{4}\n".format(x, y, theVars.height, stationID, spokeID))

  file2.write("{0}\t{1}\t{2:0.3f}\t{3:0.3f}\t{4}\n".format(stationID, spokeID, x/1.e2, y/1.e2, theVars.height/1.e2)) 

if not InICCoords:
  file.close()
  print("Made file", str(pathlib.Path(__file__).parent.absolute())+"/../resources/BaseList.list")
file2.close()
print("Made file", str(pathlib.Path(__file__).parent.absolute())+"/../resources/AntennaLocations.txt")