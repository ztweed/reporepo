# extracts transform matrices from catmaid alignment xml
# also plots x and y drift
from xml.etree import ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import re
import scipy.io as sio

# parse xml with ElementTree
tree = ET.parse('InterSectionAffineLockFirstLastCompleted_Failed_weicatmaid1.xml')

# retrieve all t2_patch nodes
patches = tree.getiterator('t2_patch')

trans_mats = []
# retrieve transform matrices from each t2_patch for each medium res file
for i in range(0, len(patches)):
    name = patches[i].get('title')
    if 'm' in name:
        trans_mats.append(patches[i].get('transform'))

# format string appropriately and create a list from each string
for i in range(0, len(trans_mats)):
    l = len(trans_mats[i])
    trans_mats[i] = trans_mats[i][7:l-1]
    trans_mats[i] = trans_mats[i].split(',')

xlist = []
ylist = []
z_idx = np.arange(1, len(trans_mats)+1)

# separate into x and y lists
for i in range(0, len(trans_mats)):
    xlist.append(float(trans_mats[i][4]))
    ylist.append(float(trans_mats[i][5]))

# save values to .npy and .mat files
zxy = np.column_stack([z_idx, xlist, ylist])
np.save("transforms", zxy)
sio.savemat("transforms", mdict={'trans': zxy})


# my attempt at one point per pixel...may be flawed
fig = plt.figure(figsize=(136, 16), dpi=80)

ax1 = fig.add_subplot(211)
ax2 = fig.add_subplot(212)

# plot xlist to check for drift
ax1.plot(xlist)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.tick_params(top='off', right='off', direction='out')
ax1.set_xlim(0, len(xlist))
ax1.set_title('X Coordinates', loc='left', fontsize=18)
ax1.set_xticklabels([], visible=False)
ax1.set_ylabel('x', style='italic')

# plot ylist to check for drift
ax2.plot(ylist)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.tick_params(top='off', right='off', direction='out')
ax2.set_xlim(0, len(ylist))
ax2.set_title('Y Coordinates', loc='left', fontsize=18)
ax2.set_xlabel('z', style='italic')
ax2.set_ylabel('y', style='italic')

plt.tight_layout()

plt.savefig('coords.eps', format='eps')
