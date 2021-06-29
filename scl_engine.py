import lxml.etree as ET
import os, sys
import logger_dialog as log

ns = {'61850': 'http://www.iec.ch/61850/2003/SCL',
      'NSD': 'http://www.iec.ch/61850/2016/NSD',
      'efsk': 'http://www.fsk-ees.ru/61850/2020',
      'emt': 'http://www.mtrele.ru/npp/2021'}

nsURI = '{%s}' % (ns['61850'])
nsMap = {None : ns['61850']}

ns_dURI = '{%s}' % (ns['NSD'])
ns_dMap = {None : ns['NSD']}

def indentXML(elem, level=0):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indentXML(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

#------------ settings ----------------------


class SettingsValues:
    def __init__(self, filename):
        self.settings_filename = filename
        default_salt = 'WcdVmxFoE7a'#do not change!
        # set default values
        app_path = os.path.dirname(os.path.abspath(__file__))
        # do/da library filename
        self.settings = {'dodas' : os.path.join(app_path,'dodas.xml'),
                         'lntypes' : os.path.join(app_path,'lntypes.xml'),
                         'nsd' : os.path.join(app_path,'NSD'),
                         's_dodas' : '254wzM3nTen',#do not change!
                         's_lntypes' : 'HbjSGGbonAW',#do not change!
                         's_nsd' : 'VFqBCPKvEnz',#do not change!
                         'private_ns' : 'MT NPP:2021A'}
        self.licenses = {'None' : 0}
        
    def load(self, do_log = True):
        if do_log: log.logger.info('Loading settings.')
        try:
            tree = ET.parse(self.settings_filename)
            root = tree.getroot()
            self.settings = dict(root.attrib)
            self.licenses = {lic.get('val') : 0 for lic in root.findall('./emt:Lic', ns)}
            print(self.licenses)
        except OSError:
            if do_log: log.logger.error('Unexpected loading error.')

    def save(self):
        root = ET.Element('{%s}Settings' % (ns['emt']),
                          nsmap = {None : ns['emt']})
        root.attrib.update(self.settings)
        for lic in self.licenses.keys():
            ET.SubElement(root, '{%s}Lic' % (ns['emt']),
                          nsmap = {None : ns['emt']}).set('val',lic)
        indentXML(root)
        tree = ET.ElementTree(root)
        tree.write(self.settings_filename, encoding="utf-8", xml_declaration=True)


def update_licenses():
    global settings, lntypes
    lic_used = {ln_type.get('{%(emt)s}license' % ns) for ln_type\
                in lntypes.findall('./61850:LNodeType', ns)}
    settings.licenses.update((key, 0) for key in settings.licenses)
    settings.licenses.update((key, 1) for key in lic_used)
    
    


#----------------- data loading
        
dodas = None
lntypes = None

CDC_list = list()
CDC_types = dict()

ln_file = ''

def load_dodas(filename):
    def critical(obj, item, err):
        nonlocal crit
        crit = True
        log.logger.critical('Internal error in DO/DA database. '+\
                            '%s "%s.%s" %s error.',
                            obj, item.getparent().get('id'), item.get('name'), err)
        
            
    global dodas, CDC_list, CDC_types
    log.logger.info('Loading data types')
    tree = ET.parse(filename)
    dodas = tree.getroot()
    #check for internal errors
    crit = False
    #SDO
    for item in dodas.findall('.//61850:SDO', ns):
        if dodas.find('.//61850:DOType[@id="%s"]' % item.get('type'), ns) is None:
            critical('SDO', item, 'typecast')
    #struct in DA
    for item in dodas.findall('.//61850:DA[@bType="Struct"]', ns):
        if dodas.find('.//61850:DAType[@id="%s"]' % item.get('type'), ns) is None:
            critical('DA', item, 'typecast')
    #struct in BDA
    for item in dodas.findall('.//61850:BDA[@bType="Struct"]', ns):
        if dodas.find('.//61850:DAType[@id="%s"]' % item.get('type'), ns) is None:
            critical('BDA', item, 'typecast')
    #enum in DA
    for item in dodas.findall('.//61850:DA[@bType="Enum"]', ns):
        if dodas.find('.//61850:EnumType[@id="%s"]' % item.get('type'), ns) is None:
            critical('DA', item, 'enum type')
    #enum in BDA
    for item in dodas.findall('.//61850:BDA[@bType="Enum"]', ns):
        if dodas.find('.//61850:EnumType[@id="%s"]' % item.get('type'), ns) is None:
            critical('BDA', item, 'enum type')

    #caches
    CDC_list = sorted({item.get('cdc') for item in dodas.findall('./61850:DOType', ns)},
                      key = lambda cdc: cdc[::-1])
    CDC_types = { cdc : sorted([item.get('id') for item in
                         dodas.findall('./61850:DOType[@cdc="%s"]'% cdc, ns)])\
                  for cdc in CDC_list}
    #check for nsd's CDC support
    for nsd in NSD.keys():
        cdc = {do.get('type') for do in NSD[nsd].findall('.//NSD:DataObject', ns)}
        diff = cdc.difference(CDC_list)
        if len(diff):
            log.logger.warning('Data types miss a CDCs, used in namespace "%s": %s',
                               nsd, ', '.join(diff))
    return (not crit) and len(CDC_list) and len(CDC_types)
            
def q_load_lns(filename):
    global lntypes
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        for ln_type in root.findall('./61850:LNodeType', ns):
            if ln_type.get('{%(emt)s}integrity' % ns) !=  hash_ln(ln_type):
                raise OSError()
        del lntypes
        lntypes = root
        return True
    except OSError:
        log.logger.error('Unexpected error in undo stack.')
        return False
    

def load_lns(filename, licenses):
    global lntypes
    global ln_file
    log.logger.info('Loading logic nodes')
    try:
        ln_file = filename
        tree = ET.parse(ln_file)
    except OSError:
        log.logger.error('Unexpected loading error.')
        root = ET.Element(nsURI+'DataTypeTemplates', nsmap = nsMap)
        tree = ET.ElementTree(root)
        tree.write(ln_file, encoding="utf-8", xml_declaration=True)
    lntypes = tree.getroot()
    #check/update integriry and namespaces of LN
    for ln_type in lntypes.findall('./61850:LNodeType', ns):
        spaces =[s for s in get_nsd_of_ln_class(ln_type.get('lnClass'))]
        if ln_type.get('{%(emt)s}integrity' % ns) !=  hash_ln(ln_type):
            log.logger.error('LNodeType "%s" damaged, purged.', ln_type.get('id'))
            lntypes.remove(ln_type)
        elif not ln_type.get('{%(emt)s}lnNs' % ns) in spaces:
            add_private_node(ln_type.get('lnClass'))
            if ln_type.get('{%(emt)s}lnNs' % ns) != private_namespace():
                log.logger.warning('LNodeType "%s" declared unknown lnNs="%s". Changed to "%s".',
                                   ln_type.get('id'), ln_type.get('{%(emt)s}lnNs' % ns), private_namespace())
            ln_type.set('{%(emt)s}lnNs' % ns, private_namespace())
    #check/update namespaces of DO
    for data_object in lntypes.findall('.//61850:DO', ns):
        space, cdc, pc = get_do_attrs(data_object.getparent().get('lnClass'),
                                      data_object.getparent().get('{%(emt)s}lnNs' % ns),
                                      data_object.get('name'))
        try:
            current_cdc = dodas.find('./61850:DOType[@id="%s"]'%
                                     data_object.get('type'), ns).get('cdc')
            if (data_object.get('{%(emt)s}dataNs' % ns) != space)\
               or not (current_cdc in cdc):
                log.logger.warning('Data object "%s.%s" does not match to namespaces, will be fixed.',
                                   data_object.getparent().get('id'), data_object.get('name'))
                fix_do_namespace(data_object)
            else:
                #repopulate da values for case of dodas was updated
                populate_da_values(data_object, logging = True)
        except (AttributeError, TypeError):
            log.logger.error('Data object "%s.%s" out of DO/DA database. Will be purged.',
                             data_object.getparent().get('id'), data_object.get('name'))
            data_object.getparent().remove(data_object)
            
    #update licenses, lntypes integrity
    for ln_type in lntypes.findall('./61850:LNodeType', ns):
        lic = str(ln_type.get('{%(emt)s}license' % ns))
        licenses[lic] = 1
        ln_type.set('{%(emt)s}license' % ns, lic)
        ln_type.set('{%(emt)s}integrity' % ns, hash_ln(ln_type))
    return True
            
            

def save_lns():
    global ln_file
    tree = ET.ElementTree(lntypes)
    indentXML(lntypes)
    tree.write(ln_file, encoding="utf-8", xml_declaration=True)

def private_namespace():
    global settings
    return settings.settings['private_ns']

#==============================================    
#        BDA and DataObjets
#==============================================    
def _scan_da(parent, item, desc):
    res_desc = desc if item.get('desc') is None else\
               ', '.join((desc, item.get('desc')))
    if item.get('bType') == 'Struct':
        for bda in dodas.findall('./61850:DAType[@id="%s"]/61850:BDA' %
                                     item.get('type'), ns):
            for res in _scan_da('.'.join((parent, item.get('name'))),
                                bda,
                                res_desc): yield res
    else:
        path_name = '.'.join((parent, item.get('name')))
        yield {'path' : path_name[1:],
               'desc' : res_desc[2:],
               'bda' : item}


def _scan_do(data, fc_list, parent='', desc=''):
    for item in data:
        if item.tag == '{%(61850)s}SDO' % ns:
            for bda in _scan_do(data = dodas.find('./61850:DOType[@id="%s"]' %
                                                  item.get('type'), ns),
                                fc_list = fc_list,
                                parent = '.'.join((parent, item.get('name'))),
                                desc = desc if item.get('desc') is None else ', '.\
                                join((desc, item.get('desc')))): yield bda
        elif item.get('fc') in fc_list:
            for bda in _scan_da(parent, item, desc):
                bda.update ({'fc' : item.get('fc'),
                             'valKind' : item.get('valKind')})
                yield bda

def get_bda(data_object, fc_list):
    global dodas
    for item in _scan_do(dodas.find('./61850:DOType[@id="%s"]' %
                                    data_object.get('type'), ns),
                         fc_list):
        yield item

def populate_da_values(data_object, logging = False):
    def _is_int(s):
        try:
            v = int(s)
            return True
        except ValueError:
            return False

    def _is_float(s):
        try:
            v = float(s)
            return '.' in s
        except ValueError:
            return False

    #pop values to dict
    prev = dict()
    for key in data_object.keys():
        if '{%(emt)s}val' % ns in key:
            prev[key] = data_object.attrib.pop(key)
    #create values
    new_val_list = [] # for logging
    for bda_data in get_bda(data_object, ['CF', 'SE', 'SG', 'SP', 'DC']):
        if bda_data['bda'].get('name') == 'dU': continue
        # bda "dU" excluded from operations
        path_tag = '{%(emt)s}' % ns + 'val%s' % bda_data['path'].replace('.','')
        bType = bda_data['bda'].get('bType')
        if bType == 'Enum':
            enums = {env.get('ord') : ('' if env.text is None else env.text)
                     for env in dodas.findall(
                         './61850:EnumType[@id="%s"]/61850:EnumVal'%
                         bda_data['bda'].get('type'), ns)}
            if path_tag in prev.keys() and prev[path_tag] in enums.values():
                val = prev.pop(path_tag)
            else:
                new_val_list.append(bda_data['path'])
                if '0' in enums.keys(): val = enums['0']
                elif '1' in enums.keys(): val = enums['1']
                else: val = enums[enums.keys()[0]]
        elif bType == 'BOOLEAN':
            if path_tag in prev.keys() and prev[path_tag] in ('true', 'false'):
                val = prev.pop(path_tag)
            else:
                new_val_list.append(bda_data['path'])
                val = 'false'
        elif 'INT' in bType:
            if path_tag in prev.keys() and _is_int(prev[path_tag]):
                val = prev.pop(path_tag)
            else:
                new_val_list.append(bda_data['path'])
                val = '0'
        elif 'FLOAT' in bType:
            if path_tag in prev.keys() and _is_float(prev[path_tag]):
                val = prev.pop(path_tag)
            else:
                new_val_list.append(bda_data['path'])
                val = '0.0'
        elif path_tag in prev.keys():
            val = prev.pop(path_tag)
        else:
            new_val_list.append(bda_data['path'])
            val = ''
        data_object.set(path_tag, val)
    if len(new_val_list) and logging:
        # log new default value applied
        log.logger.warning('Data object "%s.%s" updated with new default value(s): "%s".',
                            data_object.getparent().get('id'), data_object.get('name'),
                            ', '.join(new_val_list))
    if len(prev) and logging:
        #log previous values are not implemented in actual dodas version
        log.logger.warning('Data object "%s.%s" cleared from obsolete default value(s): "%s".',
                           data_object.getparent().get('id'), data_object.get('name'),
                           ', '.join((key[len('{%(emt)s}val' % ns):] for key in prev.keys())))
        

def is_process(data_object):
    return next(get_bda(data_object, ['ST', 'MX']), None) is not None


def fix_do_namespace(data_object):
    space, cdc, pc = get_do_attrs(data_object.getparent().get('lnClass'),
                                  data_object.getparent().get('{%(emt)s}lnNs' % ns),
                                  data_object.get('name'))
    #ns
    data_object.set('{%(emt)s}dataNs' % ns, space)
    #cdc
    current_cdc = dodas.find('./61850:DOType[@id="%s"]'%
                             data_object.get('type'), ns).get('cdc')
    if not (current_cdc in cdc):
        current_cdc = cdc[0]
        # reconfigure type
        type_vals = CDC_types[current_cdc]
        new_val = next((v for v in type_vals if data_object.get('name') in v),
                       type_vals[0])
        data_object.set('type',new_val)
        # clear da values
        populate_da_values(data_object)
        # reconfigure process
        proc = data_object.get('{%(emt)s}process' % ns)
        if is_process(data_object):
            if proc is None: data_object.set('{%(emt)s}process' % ns, 'model')
        elif proc is not None: data_object.attrib.pop('{%(emt)s}process' % ns)

#==============================================    
#        NSD processing
#==============================================    

def _ns_name(item):
    return item.get('id') + ':' + item.get('version') + item.get('revision')

def get_nsd(nsd_path):
    for root, dirs, files in os.walk(nsd_path):
        for file in files:
            if file.endswith('.nsd'):
                full_name = os.path.join(root,file)
                space = ''
                contain = False
                for event, element in ET.iterparse(full_name, events=("start", "end")):
                    if event == 'start' and element.tag == '{%s}NS' % (ns['NSD']):
                        space = _ns_name(element)
                    if element.tag == '{%s}LNClasses' % (ns['NSD']):
                        contain = True
                        break
                if space != '':
                    yield({'file' : full_name,
                           'space' : space,
                           'contain' : contain})

NSD = None

def load_nsd(nsd_path):
    global NSD
    if NSD is not None: return
    NSD = dict()
    dep_list = list()
    for nsd in get_nsd(nsd_path):
        if nsd['contain']:
            #load
            NSD[nsd['space']] = ET.parse(nsd['file']).getroot()
            #register dependencies
            for dep in NSD[nsd['space']].findall('./NSD:DependsOn',ns):
                dep_list.append({'space' : nsd['space'],
                                 'depends' : _ns_name(dep)})
        else: NSD[nsd['space']] = None
    log.logger.info('Analyzed namespaces: %s', ', '.join(NSD.keys()))
    #check dependencies loaded
    for dep in dep_list:
        if (dep['space'] in NSD.keys()) and (dep['depends'] not in NSD.keys()):
            log.logger.warning('NS "%s" depends to missing "%s", will be purged.',
                               dep['space'], dep['depends'])
            NSD.pop(dep['space'])
    #clear non-ln namespaces
    keys = [key for key in NSD.keys()]
    for key in keys:
        if NSD[key] is None: NSD.pop(key)
    #check for DO cdc conflicts
    keys = [key for key in NSD.keys()]
    purged = set()
    for nsd in keys:
        for i in range(keys.index(nsd) + 1, len(keys)):
            for node in NSD[nsd].findall('.//NSD:DataObject', ns):
                set_type = node.get('type')
                for node2 in NSD[keys[i]].findall('.//NSD:DataObject[@name="%s"]'
                                            % node.get('name'), ns):
                    if node2.get('type') != set_type:
                        log.logger.warning('Namespace "%s" conflicts to "%s": DO "%s" in "%s" declared type "%s" vs "%s".',
                                           keys[i], nsd, node.get('name'), node2.getparent().get('name'),
                                           node2.get('type'), set_type)
    #create private namespace
    if private_namespace() in NSD.keys():
        log.logger.error('Namespace "%s" conflicts to a private namespace, will be purged.',
                         private_namespace())
        NSD.pop(private_namespace())
    p_id, p_ver_rev = private_namespace().split(':')
    p_ns = ET.Element(ns_dURI+'NS',
                      attrib = {'id' : p_id,
                                'version' : p_ver_rev[:-1],
                                'revision' : p_ver_rev[-1]},
                      nsmap = ns_dMap)
    ET.SubElement(p_ns, ns_dURI+'LNClasses', nsmap = ns_dMap)
    NSD[private_namespace()] = p_ns
    #show the rest
    log.logger.info('Domain/transitional namespaces in use: %s', ', '.join(NSD.keys()))
    return len(NSD)-1 #0 if only private ns

def get_ln_classes(space):
    return sorted((node.get('name') for node in NSD[space].findall('.//NSD:LNClass', ns)))

def add_private_node(ln_class):
    root = NSD[private_namespace()].find('./NSD:LNClasses', ns)
    if root.find('./NSD:LNClass[@name="%s"]' % ln_class, ns) is None:
        ET.SubElement(root, ns_dURI+'LNClass',
                      attrib = {'name' : ln_class},
                      nsmap = ns_dMap)

class NsdError(Exception):
    pass            

def get_nsd_object(space, ln_class, extended = False):
    def find_node(space, extended):
        nonlocal ln_class
        node = None
        in_space = space
        if not extended:
            node = NSD[space].find('./NSD:LNClasses/NSD:AbstractLNClass[@name="%s"]' % ln_class, ns)
            if node is None:
                node = NSD[space].find('./NSD:LNClasses/NSD:LNClass[@name="%s"]' % ln_class, ns)
        if node is None:
            for dep in NSD[space].findall('./NSD:DependsOn',ns):
                in_space = _ns_name(dep)
                if in_space in NSD.keys():
                    node, in_space = find_node(in_space, False)
                if node is not None: break
        return node, in_space
            
    node, node_space = find_node(space, extended)
    if node is None: raise NsdError('LnClass "%s" not found in namespaces.' % ln_class)
    if node.get('isExtension'):
        for item in get_nsd_object(node_space, ln_class, extended = True): yield item
    elif node.get('base') is not None:
        for item in get_nsd_object(node_space, node.get('base')): yield item
    for data_object in node.findall('./NSD:DataObject', ns):
        yield {'name' : data_object.get('name'),
               'cdc' : data_object.get('type'),
               'type' : data_object.get('underlyingType'),
               'pres' : data_object.get('presCond'),
               'tr' : data_object.get('transient'),
               'space' : node_space}
    
def get_nsd_of_object(obj_name):
    for space in NSD.keys():
        node = NSD[space].find('.//NSD:DataObject[@name="%s"]' % obj_name, ns)
        if node is not None:
            yield {'space' : space,
                   'cdc' : node.get('type'),
                   'type': node.get('underlyingType')}

def get_nsd_of_ln_class(ln_class):
    for space in NSD.keys():
        node = NSD[space].find('.//NSD:LNClass[@name="%s"]' % ln_class, ns)
        if node is not None: yield space

def get_do_attrs(ln_class, ln_ns, do_name):
    #get base non-indexed name part for 'multi' prescond check
    for k in range(1,len(do_name)+1):
        if not do_name[-k].isdigit(): break
    index = None
    try:
        base_name = do_name[:-(k-1)]
        index = int(do_name[-(k-1):])+1
        #we have indexed name, otherwis we get ValueError
        space, cdc, pc = next(((do['space'], do['cdc'], do['pres'])\
                                for do in get_nsd_object(ln_ns, ln_class)\
                                if do['name'] == base_name and\
                                'multi' in do['pres']))
    except (ValueError, StopIteration):
        #name was not indexed (ValueError)
        #or indexed, but not found in space (StopIteration)
        space, cdc, pc = next(((do['space'], do['cdc'], do['pres'])\
                                for do in get_nsd_object(ln_ns, ln_class)\
                                if do['name'] == do_name),
                              (private_namespace(), None, None))
    if cdc is None:
        #in private_namespace allowed all CDC or only matched
        if index is not None:
            cdc = {(n['cdc']) for n in get_nsd_of_object(base_name)}
            cdc = list(cdc) if len(cdc) else None 
        if index is None or cdc is None:
            cdc = {(n['cdc']) for n in get_nsd_of_object(do_name)}
            cdc = list(cdc) if len(cdc) else CDC_list
    if not(type(cdc) is list): cdc = [cdc]
    return space, cdc, pc
        
#============== subscribing ===================

def _canonize_ln(ln_type):
    s = ln_type.tag
    attrs = sorted(list(ln_type.attrib))
    rem_attr = next((attr for attr in attrs if 'integrity' in attr), None)
    if rem_attr is not None: attrs.remove(rem_attr)
    s = s + ''.join(''.join((s, ln_type.get(s))) for s in attrs)
    text = ln_type.text
    if text:
        text = text.replace('\t','')
        text = text.replace('\n','')
        if text != '': s = s + text
    for child in ln_type: s = s + _canonize_ln(child)
    return s

import hashlib
import base64

def hash_ln(ln_type):
    return base64.urlsafe_b64encode(\
        hashlib.sha256(_canonize_ln(ln_type).encode('utf-8')).digest())\
        .decode('utf-8')

#==============================================    

settings = None

def init():
    global settings
    settings = SettingsValues('init.xml')
    settings.load()
    a = load_nsd(settings.settings['nsd'])
    b = load_dodas(settings.settings['dodas'])
    c = load_lns(settings.settings['lntypes'], settings.licenses)
    settings.save()
    return a and b and c
    
