#!/usr/bin/env python
import sys
import re
import pprint
import numpy as np
from lxml import etree
import scipy.io as sio

#from PIL  import Image
pp = pprint.PrettyPrinter(indent=2)

## set file names
template_fn   = 'InterSectionAffineLockFirstLastCompleted_Failed_weicatmaid1.xml'
output_fn     = 'output.xml'

## define functions
def xml_to_mat(tf_str):
    transform  = {}
    tf_str     = tf_str.replace('matrix(','')
    tf_str     = tf_str.replace(')','')
    str_split  = re.split(',', tf_str)
    if len(str_split) == 6:
        # transform="matrix(Sx,Kxy,Kyx,Sy,Tx,Ty)"
        transform['Sx']    = float(str_split[0])
        transform['Kyx']   = float(str_split[1])
        transform['Kxy']   = float(str_split[2])
        transform['Sy']    = float(str_split[3])
        transform['Tx']    = float(str_split[4])
        transform['Ty']    = float(str_split[5])
        transform['tfmat'] = np.matrix([[transform['Sx'], transform['Kxy'], transform['Tx']], [transform['Kyx'], transform['Sy'], transform['Ty']], [0, 0, 1]])
    else:
        print 'Error: xml_to_mat transform input did not have the correct number of elements'
        sys.exit()
    return transform

def mat_to_dict(mat):
    d = {}
    d['Sx']  = str(mat[0,0])
    d['Kxy'] = str(mat[0,1])
    d['Sy']  = str(mat[1,1])
    d['Kyx'] = str(mat[1,0])
    d['Tx']  = str(mat[0,2])
    d['Ty']  = str(mat[1,2])
    return d

## set some internal variables
tf_keepreading = True

## read input files
with open(template_fn, 'r') as template_f:
    template = template_f.read().replace('DOCTYPE trakem2_anything','DOCTYPE trakem2')

## parse xml template so it is ready for modification
xmlroot = etree.fromstring(template)#.getroottree()
xmltree = xmlroot.getroottree()

## extract section and image information from xml
## change transform
xml_sections = []
midRes_tmats = []
midRes_sects = []
xml_layerprops = {}
xml_patchprops = {}
xml_layers = xmlroot.findall('.//t2_layer')
print 'Found',len(xml_layers),'layers'
for layer in xml_layers:
    layer_props = {}
    for layer_attrkey, layer_attrval in layer.items():
        layer_props[layer_attrkey] = layer_attrval
    if layer_props['z']:
        layeridx = int(layer_props['z'].replace('.0',''))
        xml_layerprops[layeridx] = {}
        for layer_attrkey, layer_attrval in layer_props.items():
            xml_layerprops[layeridx][layer_attrkey] = layer_attrval
    else:
        print 'WARNING: Could not determine layer index.'
    patches = layer.findall('./t2_patch')
    xml_patchprops[layeridx] = {}
    for pidx, patch in enumerate(patches):
        xml_patchprops[layeridx][pidx + 1] = {}
        for patch_attrkey, patch_attrval in patch.items():
            xml_patchprops[layeridx][pidx + 1][patch_attrkey] = patch_attrval
    if len(patches) == 2:
        print 'Layer',layeridx,'is associated with 2 patches.'
        hiIdx = 0
        for pidx, p in enumerate(xml_patchprops[layeridx]):
            if '_h' in re.sub(r'(\D{2})_.*\.tif', r'\1', xml_patchprops[layeridx][pidx+1]['title']):
                hiIdx = pidx + 1
            elif '_m' in re.sub(r'(\D{2})_.*\.tif', r'\1', xml_patchprops[layeridx][pidx+1]['title']):
                midIdx = pidx + 1
            else:
                print 'WARNING: Found patch that does NOT correspond to a 20nm/px or a 60nm/px image.'
        if hiIdx and midIdx:
            for pidx, patch in enumerate(patches):
                if pidx + 1 == midIdx:
                    print '    20nm/px transform matrix:',xml_patchprops[layeridx][midIdx]['transform']
                    midRes_sects.append(layeridx)
                    midRes_tmats.append(xml_to_mat(xml_patchprops[layeridx][midIdx]['transform'])['tfmat'])
                    print '    Saved to midRes_tmats'
        else:
            print 'ERROR: Layer',layeridx,'is associated with 2 patches, but they are not strictly 20nm/px and 60nm/px images.'
    elif len(patches) == 1:
        patchidx = 1
        if re.sub(r'(\D{2})_.*\.tif', r'\1', xml_patchprops[layeridx][patchidx]['title']) == '_h':
            print 'Layer',layeridx,'is associated with only 1 patch corresponding to a 60nm/px image.'
            print '    60nm/px transform change:',xml_patchprops[layeridx][patchidx]['transform']
            for pidx, patch in enumerate(patches):
                patch.set('transform',mo_tf_n)
        else:
            print 'WARNING: Layer',layeridx,'is associated with only 1 patch, but it does NOT correspond to a 60nm/px image.'
    else:
        print 'WARNING: Layer',layeridx,'has a non-standard number of patches... skipping.'
        continue
    xml_sections.append(layeridx)

# determine missing indices
r = range(1, len(midRes_sects))
missing = list(set(r) - set(midRes_sects))

# insert matrix of zeros at missing indices
empty = np.matrix(np.zeros((3, 3)))
for m in missing:
    midRes_tmats.insert(m, empty)


# create an object mimicking a matlab cell array to associate indices and matrices
#transforms = np.zeros((2, ), dtype=np.object)
#transforms[0] = np.array(midRes_sects)
#transforms[1] = np.array(midRes_tmats)


# save values to .npy and .mat files
np.save("transforms", midRes_tmats)
sio.savemat("transforms", mdict={'trans': midRes_tmats})


    # find t2_layer matching num in xml
    #   <t2_layer oid="8"
    #           thickness="1.0"
    #           z="17420.0"
    #           title=""
    #   >
    #       <t2_patch
    #          oid="41"
    #          width="5120.0"
    #          height="4096.0"
    #          transform="matrix(1.0,0.0,0.0,1.0,0.0,0.0)"
    #          title="mo_17420_raw.tif"
    #          links="43"
    #          type="1"
    #          file_path="/hms/scratch1/htem/users/dh97/130201zf142/Raw_Preferred_Test/MO/mo_17420_raw.tif"
    #          style="fill-opacity:1.0;stroke:#ffff00;"
    #          o_width="5120"
    #          o_height="4096"
    #          min="32.0"
    #          max="20292.0"
    #          mres="32"
    #       >
    #       </t2_patch>
    #       <t2_patch
    #          oid="43"
    #          width="7168.0"
    #          height="5120.0"
    #          transform="matrix(1.0,0.0,0.0,1.0,0.0,0.0)"
    #          title="im_17420_raw.tif"
    #          links="41"
    #          type="1"
    #          file_path="/hms/scratch1/htem/users/dh97/130201zf142/Raw_Preferred_Test/Im/im_17420_raw.tif"
    #          style="fill-opacity:1.0;stroke:#ffff00;"
    #          o_width="7168"
    #          o_height="5120"
    #          min="32.0"
    #          max="19992.0"
    #          mres="32"
    #       >
    #       </t2_patch>
    #   </t2_layer>
