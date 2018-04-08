#!/usr/bin/env python

import os
import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET
import cerberus
import schema
import clean

#OSM_PATH = "./samples/sample_10.osm"
OSM_PATH = "Cambridge.osm"

NODES_PATH     = "nodes.csv"
WAYS_PATH      = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH  = "ways_tags.csv"
NODE_TAGS_PATH = "nodes_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Modify schema in order to contain information about relations!
SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'version']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'nodes', 'version']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            # After passing the element info the root is removed from memory. 
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):

    node_attribs = {}
    way_attribs  = {}
    way_nodes    = []
    tags         = []  
    
    # Handle secondary tags the same way for both node and way elements
    # print element.tag
    
    if element.tag == 'node':
        for i in element.attrib.keys():
            if i in node_attr_fields:
                node_attribs[i] = element.attrib[i]
                
        for child_tag in element:
            # We store into a dictionary the attributes of each child tag
            ct = {}
            
            if problem_chars.search(child_tag.attrib['k']):
                # We skip the child tags with problematic characters
                continue
                
            ct['key']  = child_tag.attrib['k']
            ct['value']  = child_tag.attrib['v']
            ct['id']   = node_attribs['id']
            
            # We correct the key values and create a new 'type' field
            if ':' not in ct['key']:
                ct['type'] = default_tag_type
            else:
                ct['type'] = ''
                for i in range(len(ct['key'])):
                    if ct['key'][i] == ':':
                        # To correct cases like "source:addr:housenumber"
                        if ct['key'].split(":")[0] == "source":
                            ct['key'] = "source"
                        else:
                            ct['key'] = ct['key'][i+1:]
                        break
                    ct['type'] = ct['type'] + ct['key'][i]
            
            # Cleaning of postal codes, telephone numbers, etc from ./clean.py
            ct = clean.c_tagstr(ct)
            if type(ct) == str and ct == "purge":
                continue
            
            if "post" in ct['key'] and "code" in ct['key']:
                ct = clean.c_pc(ct)
            elif ct['key'] == "telephone" or ct['key'] == "phone":
                ct = clean.c_telephone(ct)
            elif ct['type'] == "recycling":
                ct = clean.c_recycling(ct)
            else:
                pass
            # We remove the tags with empty key or values. This arrrise from 
            # encoding chineese/arabic/russian characters with encode('ascii', 'ignore')
            # that I can not process.
            
            if type(ct) == str and ct == "purge":
                pass
            else:
                tags.append(ct)
       
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        for i in element.attrib.keys():
            if i in way_attr_fields:
                way_attribs[i] = element.attrib[i]
        c_wn = 0
        for child_tag in element:
            if child_tag.tag == 'nd':
                    wn = {}
                    wn['id']      = way_attribs['id']
                    wn['node_id'] = child_tag.attrib['ref']
                    wn['position'] = c_wn
                    c_wn += 1
                    way_nodes.append(wn)
            else:
                ct = {}
                if problem_chars.search(child_tag.attrib['k']):
                    continue
                ct['key']  = child_tag.attrib['k']
                ct['value']  = child_tag.attrib['v']
                ct['id']   = way_attribs['id']

                # Shaping the key tags like "addr:housenumer" or "addr:postcode"
                if ':' not in ct['key']:
                    ct['type'] = default_tag_type
                else:
                    k_tmp = ct['key'].split(":")
                    ct['key']  = k_tmp[-1]
                    ct['type'] = k_tmp[-2]
                # Cleaning of postal codes, telephone numbers, etc from ./clean.py
                # Cleaning of postal codes, telephone numbers, etc from ./clean.py
                #print ct
                ct = clean.c_tagstr(ct)
                if type(ct) == str and ct == "purge":
                    continue
                
                if "post" in ct['key'] and "code" in ct['key']:
                    ct = clean.c_pc(ct)
                if type(ct) == str and ct == "purge":
                    continue
                if ct['key'] == "telephone" or ct['key'] == "phone":
                    ct = clean.c_telephone(ct)
                
                #if ct['key'] == "recycling":
                #    ct = clean.c_recycling(ct)
                if type(ct) == str and ct == "purge":
                    continue
                else:
                    tags.append(ct)
                
            way_attribs['nodes'] = c_wn
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}




# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    
    with codecs.open(NODES_PATH, 'w') as nodes_file,\
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file,\
         codecs.open(WAYS_PATH, 'w') as ways_file,\
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file,\
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)
        
        # We write the header of the csv files with the fields of the schema
        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()
        
        # We iteratively read the node and ways elements of the XML file
        # Too big to load it into memory so we clean and read one element at a time
        
        # We put a counter for testing!
        for element in get_element(file_in, tags=('node','way')):
            #print
            #print "___________ NEW XML ELEMENT ______________"
            #print
            el = shape_element(element)
            #print el

            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])
        
        
if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=False)
    # Creating the database Cambdridge.db
    os.system("create_db.py")

