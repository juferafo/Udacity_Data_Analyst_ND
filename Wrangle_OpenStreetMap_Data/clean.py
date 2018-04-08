#!/usr/bin/env python

'''
This module contains definitons to correct/standarize the following elements in the database:
    
    * c_pc            -> Postal code cleaning
    * c_telephone     -> Telephone numbers
    * c_tagstr        -> Words spelling correction
    * audit_nonascii  -> Removal of non-ASCII characters
    * c_recycling     -> Categorizing waste management
    * c_place_worship -> Greek Orthodox to Orthodox
'''

import re


def c_pc(tag):
    # Postal code cleaning
    # In the region of Cambridgeshire the postal codes have the following structure:
    # CBN AAA where N = [1-11] or [21-25] and AAA is a combination of three letters or numbers
    re_pc = re.compile(r'CB(([1-9]|[1][0-1])|([2][1-5]))\s([A-Z]|[0-9]){3}')
    tag['key'] = "postal_code"
    if not re_pc.search(tag['value']):
        return "purge" 

    return tag


def c_telephone(tag):
    # Telephone number cleaning
    # I set up the following format for the telephone number +44XXXXXXXXXX
    # Here I also convert the key for "telephone" and "phone" into "telephone"
    if tag['value'][0] == '0':
        tag['value'] = tag['value'][1:]
    t = tag['value'].split()
    if t[0] != '+44':
        prefix = '+44'
    else:
        prefix = ''
    # Only the thelephones with 13 characters are kept
    if len(''.join(t)) == 13:
        tag['value'] = prefix+''.join(t) 
    else:
        tag['value'] = ''

    tag['key'] = "telephone"
    
    return tag


def c_tagstr(tag):
    # Here I verify that the keys have the same lower case format
    tag['key'] = tag['key'].lower()

    # Websites should not be modified
    if tag['key'] == 'source' or tag['key'] == 'website':
       return tag

    # Here I correct shorcuts for certain words and directions
    types = {"Road": "Rd ", "College": "Coll ", "St. ": "St ",\
             "North" : "north", "South": "south", "West": "west", "East": "east"}

    # First we check if there are some non-ascii characters in the key or value
    try:
        for k in tag.keys():
            tag[k].decode('ascii')
    except:
        # If so, we correct the tag with the audit_nonascii method
        tag = audit_nonascii(tag)
        if tag == "purge":
            return "purge"

    for k in types.keys():
        if types[k] in tag['value']:
            tag['value'] = tag['value'].replace(types[k],k)
            st = tag['value'].split()
            st_tmp = []
            
            # I implement upper case for the first letter in each word
            for i in st:
                if i[0] in ['(', '"', '[', '{']:
                    i = i[0] + i[1:].capitalize()
                else:
                    i = i.capitalize()
                st_tmp.append(i)
            tag['value'] = " ".join(st_tmp)

    # Check wrong spell of particular non-processed words
    wrong_spelling = {"East": "lEast", "College Pathway": "Collegepathway", "Crepeaffaire": "Crpeaffaire", "Realybes": "Realybs"}
    for s in wrong_spelling.keys():
        if wrong_spelling[s] in tag['value']:
            tag['value'] = tag['value'].replace(wrong_spelling[s],s)
    
    return tag


def audit_nonascii(tag):
    # This definition clean the non-ascii characters from the data.

    # Dictionary with close characters to non-ascii ones
    utf8 = {"-": u'\u2013', "'": u'\u2019', 'e': u'\xe8', 'e': u'\xea', 'c': u'\xe7', 'e': u'\u0117',\
            'l': u'\u0142', 's': u'\u0161', 'ae': u'\xe4', 'e': u'\xe9', 'z': u'\u017e', 'g': u'\u011d'}

    for k in tag.keys():
        # If no difference between the 2 encodings, then it is OK
        if k == k.encode('ascii', 'ignore') and tag[k] == tag[k].encode('ascii', 'ignore'):
            continue
        
        # We make a first substitution of some utf8 close letter characters 
        for u_k in utf8:
            tag[k] = re.sub(utf8[u_k], u_k, tag[k])

        k = k.encode('ascii', 'ignore')
        tag[k] = tag[k].encode('ascii', 'ignore')
        
        # If the tag has no length means that all of its characters were non-ascii
        # If so, it will be eliminated
        if len(k) == 0 or len(tag[k]) == 0:
            return "purge"

        # Correcting Coffee names
        tag[k] = re.sub(r'Ca((ff)|(ffe)|(fe))','Coffee', tag[k])
        
    return tag


def c_recycling(tag):
    # This definition reduces/clasifies the waste types into:
    # plastic, tin, glass, paper, batteries and general
    rec = {'plastic'  : ['cds', 'printer_ink_cartridges', 'pens', 'printer_cartridges'],\
           'tin'      : ['foil', 'cans', 'aluminium', 'scrap_metal'],\
           'glass'    : ['low_energy_bulbs', 'fluorescent_tubes'],\
           'paper'    : ['books', 'magazines', 'cartons', 'cardboard', 'beverage_cartons'],\
           'general'  : ['electrical_items', 'clothes', 'shoes', 'textiles', 'pallets',\
                          'small_appliances', 'electrical_appliances', 'green_waste', 'wood', 'waste'],\
           'batteries': []}

    for re_k in rec.keys():
        # Come keys are like: plastic_bags. We perform a first check on them
        if tag['key'] in re_k or re_k in tag['key']:
            tag['key'] = re_k
            
            return tag
        
        else:
            if tag['key'] in rec[re_k]:
                tag['key'] = re_k
                
                return tag


def c_place_worship(tag):
    # This method corrects transform the format of the value of the denominations
    # of the places_of_worship
    
    # The only change I do here is unifying the orthodox and greek orthodox into orthodox only.
    
    tag['key']   = tag['key'].lower()
    tag['value'] = tag['value'].lower() 

    if tag['value'] == 'greek_orthodox':
        tag['value'] = 'orthodox'

    return tag

