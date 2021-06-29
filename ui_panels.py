from tkinter import *
import tkinter.ttk as ttk
import scl_engine as scl
from scl_engine import ns, nsURI, nsMap
from copy import deepcopy
import resources
import re
import random
import string

class Do_images():
    def __init__(self):
        self.do_ins = PhotoImage(data=resources.ICO_DO_INS)
        self.do_up = PhotoImage(data=resources.ICO_DO_UP)
        self.do_dn = PhotoImage(data=resources.ICO_DO_DN)
        self.do_dup = PhotoImage(data=resources.ICO_DO_DUP)
        self.do_del = PhotoImage(data=resources.ICO_DO_DEL)

icons = None

MAX_DO_NAME_LEN = 12
MAX_PREFIX_LEN = 11
MAX_LD_LEN = 64

INT_RANGES = {'INT8U' : {'min' : 0, 'max' : 255},
              'INT16U': {'min' : 0, 'max' : 65535},
              'INT32U': {'min' : 0, 'max' : 4294967295},
              'INT8'  : {'min' : -128, 'max' : 127},
              'INT16'  : {'min' : -32768, 'max' : 32767},
              'INT24'  : {'min' : -8388608, 'max' : 8388607},
              'INT32'  : {'min' : -2147483648, 'max' : 2147483647}}

VISIBLE_CHARS = set(string.ascii_letters + string.digits + string.punctuation) - {'"','\\'}

PROC_VALUES = list(('model', 'input', 'output'))

#====================================
#
#      Data attributes Frame
#
#====================================

class DaFrame(Frame):
    def __init__(self, data=None, bda_data=None, **kw):
        self.data_object = data
        self.bda_data = bda_data
        self.path_tag = '{%(emt)s}' % ns + 'val%s' % bda_data['path'].replace('.','')
        Frame.__init__(self, **kw)
        self.valid_int = (self.register(self.on_validate_int),'%d' ,'%P' ,'%S')
        self.valid_uint = (self.register(self.on_validate_uint),'%P')
        self.valid_float = (self.register(self.on_validate_float),'%d' ,'%P' ,'%S')
        self.valid_vstr = (self.register(self.on_validate_vstr),'%P')
        self.valid_objref = (self.register(self.on_validate_objref),'%P')
        self.vstr_len = 0
        self.apply_data()

    def apply_data(self):
        w_fc = Entry(master = self, width = 4)
        w_fc.insert(0, self.bda_data['fc'])
        w_fc.configure(state = DISABLED)
        w_fc.grid(column = 0, row = 0, stick="nsew")

        w_id = Entry(master = self, width = 25)
        w_id.insert(0, self.bda_data['path'])
        w_id.configure(state = DISABLED)
        w_id.grid(column = 1, row = 0, stick="nsew")

        w_vk = Entry(master = self, width = 5)
        w_vk.insert(0, '' if self.bda_data['valKind'] is None else self.bda_data['valKind'])
        w_vk.configure(state = DISABLED)
        w_vk.grid(column = 2, row = 0, stick="nsew")

        w_ds = Entry(master = self, width = 50)
        w_ds.insert(0, self.bda_data['desc'])
        w_ds.configure(state = DISABLED)
        w_ds.grid(column = 4, row = 0, stick="nsew")
        
        val = self.data_object.get(self.path_tag)
        bda_btype = self.bda_data['bda'].get('bType')
        bda_type = self.bda_data['bda'].get('type')
        if bda_btype in ['Enum', 'BOOLEAN']:
            # combobox - selection
            if bda_btype == 'Enum':
                enum_vals = ['' if env.text is None else env.text for env in
                                     scl.dodas.findall('./61850:EnumType[@id="%s"]/61850:EnumVal'%
                                                       bda_type, ns)]
            else: enum_vals = ['false', 'true']
            self.w = ttk.Combobox(master = self, values = enum_vals, width = 21, state = 'readonly')
            self.w.current(enum_vals.index(val))
            self.w.bind('<<ComboboxSelected>>', self._on_change)
        else: #da_btype is entry value
            # entry - edit
            self.w = Entry(master = self, width = 24)
            if 'INT' in bda_btype:
                if bda_btype[-1] == 'U': self.w.configure(validate="key", validatecommand=self.valid_uint)
                else: self.w.configure(validate="key", validatecommand=self.valid_int)
            elif 'FLOAT' in bda_btype: self.w.configure(validate="key", validatecommand=self.valid_float)
            elif 'VisString' in bda_btype:
                self.w.configure(validate="key", validatecommand=self.valid_vstr)
                self.vstr_len = int(bda_btype[9:])
            elif bda_btype == 'ObjRef': self.w.configure(validate="key", validatecommand=self.valid_objref)
            else: raise ValueError('Unknown bType "%s"' %bda_btype)
            self.w.insert(0, val)
            self.w.bind('<Return>', self._on_change)
            self.w.bind('<Escape>', self._on_esc)
        self.w.grid(column = 3, row = 0, stick="nsew")

    def _on_change(self, event):
        val = event.widget.get()
        bda_btype = self.bda_data['bda'].get('bType')
        #empty value is possible in some enumerations - no escape action!
        #so check values according to b_type
        try:
            if val == '' and not (bda_btype == 'Enum'): raise ValueError()
            if 'INT' in bda_btype:
                val = str(int(val))
                if not (INT_RANGES[bda_btype]['min'] <= int(val) <= \
                        INT_RANGES[bda_btype]['max']): raise ValueError()
            elif 'FLOAT' in bda_btype: val = str(float(val))
        except ValueError:
            self.bell()
            return self._on_esc(event)
        self._before_object_change()
        self.data_object.set(self.path_tag, val)
        self._on_object_change()
        if not (bda_btype == 'Enum'):
            event.widget.delete(0,END)
            event.widget.insert(0, val)
            event.widget.select_range(0, END)

    def _on_esc(self, event):
        event.widget.delete(0, END)
        event.widget.insert(0, self.data_object.get(self.path_tag))
        event.widget.select_range(0, END)
        
    def on_validate_int(self, d, P, S):
        if len(P) == 0 : return True
        if (d == '1'):
            if not set(S).issubset(set(string.digits + '-')):
                    self.bell()
                    return False
        return True
    
    def on_validate_uint(self, P):
        if len(P) == 0 or P.isdecimal(): return True
        self.bell()
        return False

    def on_validate_float(self, d, P, S):
        if len(P) == 0 : return True
        if (d == '1'):
            if not set(S).issubset(set(string.digits + '.Ee+-')):
                    self.bell()
                    return False
        return True

    def on_validate_vstr(self, P):
        if (len(P) <= self.vstr_len) and set(P).issubset(VISIBLE_CHARS): return True
        self.bell()
        return False

    def on_validate_objref(self, P):
        if (len(P) <= 129) and set(P).\
           issubset(string.ascii_letters + string.digits + '_/$.()@'): return True
        self.bell()
        return False

    def _on_object_change(self):
        self.event_generate('<<OnChange>>')
        
    def _before_object_change(self):
        self.event_generate('<<BeforeChange>>')

#====================================
#
#           LNType Frame
#
#====================================


class LnFrame(Frame):
    def __init__(self, data=None, **kw):
        self.ln_type = data
        Frame.__init__(self, **kw)
        self.valid_desc = (self.register(self.onDescValidate),
                           '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.valid_id = (self.register(self.onIdValidate),'%P')
        self.valid_prefix = (self.register(self.onPrefixValidate),'%P')
        self.valid_ld = (self.register(self.onLdValidate),'%P')
        self.valid_class = (self.register(self.onClassValidate),'%P')
        self.create_widgets()
        self.apply_ln()

    def configure(self, **kw):
        if 'data' in kw.keys():
            self.ln_type = kw.pop('data')
            self.apply_ln()
        if len(kw): super().configure(kw)

    def onDescValidate(self, d, i, P, s, S, v, V, W):
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed
        # %s = value of entry prior to editing
        # %S = the text string being inserted or deleted, if any
        # %v = the type of validation that is currently set
        # %V = the type of validation that triggered the callback
        #      (key, focusin, focusout, forced)
        # %W = the tk name of the widget

        if len(P)<255 and not set(P).intersection({'"', '\\'}):
            return True
        self.bell()
        return False
        
    def onClassValidate(self, P):
        if len(P)<5 and set(P).issubset(string.ascii_letters):
            return True
        self.bell()
        return False

    def onIdValidate(self, P):
        if len(P)<255 and (len(P) == 0 or \
                           re.match("[a-zA-Z_][0-9a-zA-Z_]*$",P)):
            return True
        self.bell()
        return False

    def onPrefixValidate(self, P):
        if len(P)<MAX_PREFIX_LEN and (len(P) == 0 or \
                           re.match("[a-zA-Z][0-9a-zA-Z_]*$",P)):
            return True
        self.bell()
        return False

    def onLdValidate(self, P):
        if len(P)<MAX_LD_LEN and (len(P) == 0 or \
                           re.match("[A-Za-z0-9][0-9A-Za-z_]*$",P)):
            return True
        self.bell()
        return False

    def create_widgets(self):
        global icons
        if icons is None: icons = Do_images()

        # captions
        ttk.Separator(master = self, orient = HORIZONTAL)\
                             .grid(column = 0, row = 0, columnspan = 3, stick = 'nsew', pady = 0)

        Label(master = self, bg = 'white', text = 'id', state = DISABLED).grid(column = 0, row = 1, stick="nsew")
        Label(master = self, bg = 'white', text = 'Class', state = DISABLED).grid(column = 1, row = 1, stick="nsew")
        Label(master = self, bg = 'white', text = 'Namespace', state = DISABLED).grid(column = 2, row = 1, stick="nsew")
        ttk.Separator(master = self, orient = HORIZONTAL)\
                             .grid(column = 0, row = 2, columnspan = 3, stick = 'nsew', pady = (0,5))
        # Id
        self._w_id = Entry(master = self, validate="key", validatecommand=self.valid_id)
        self._w_id.bind('<Return>', self._on_id)
        self._w_id.bind('<Escape>', self._on_esc_id)
        self._w_id.grid(column = 0, row = 3, stick="nsew", padx = (2,0))
        # Class - select or entry
        self._w_class = ttk.Combobox(master = self, width = 6,
                                     validate="key", validatecommand=self.valid_class)
        self._w_class.grid(column = 1, row = 3, stick="nsew")
        self._w_class.bind('<<ComboboxSelected>>', self._on_class)
        self._w_class.bind('<Return>', self._on_ret_class)
        self._w_class.bind('<Escape>', self._on_esc_class)
        # Namespace - select
        self._w_ns = ttk.Combobox(master = self, width = 20, state='readonly')
        self._w_ns.grid(column = 2, row =3, stick = 'nsew', padx = (0,3))
        self._w_ns.bind('<<ComboboxSelected>>', self._on_ns)                                  
        # Description
        self._w_desc = Entry(master = self, validate="key", validatecommand=self.valid_desc)
        self._w_desc.bind('<Return>', self._on_desc)
        self._w_desc.bind('<Escape>', self._on_esc_desc)
        self._w_desc.grid(column = 0, row = 4, columnspan = 3, stick="nsew", padx = (2,3))
        # column
        self.columnconfigure(0, weight = 1)
        # special ln attributes
        attr_frame = Frame(master = self)
        Label(master = attr_frame, text = 'Prefix:', state = DISABLED, anchor = 'w')\
                     .grid(column = 0, row = 0, stick="nsew", padx = (0,3))
        Label(master = attr_frame, text = 'LD:', state = DISABLED)\
                     .grid(column = 2, row = 0, stick="nsew", padx = (0,3))
        Label(master = attr_frame, text = 'License:', state = DISABLED, anchor = 'w')\
                     .grid(column = 0, row = 1, stick="nsew", padx = (0,3))

        # - prefix
        self._wa_prefix = Entry(master = attr_frame, validate="key", validatecommand=self.valid_prefix)
        self._wa_prefix.bind('<Return>', self._on_prefix)
        self._wa_prefix.bind('<Escape>', self._on_esc_prefix)
        self._wa_prefix.grid(column = 1, row = 0, stick="nsew", pady = (0,5))
        # - target LD
        self._wa_ld = Entry(master = attr_frame, validate="key", validatecommand=self.valid_ld)
        self._wa_ld.bind('<Return>', self._on_ld)
        self._wa_ld.bind('<Escape>', self._on_esc_ld)
        self._wa_ld.grid(column = 3, row = 0, stick="nsew", pady = (0,5))
        # - license ID
        self._wa_lic = ttk.Combobox(master = attr_frame, state='readonly')
        self._wa_lic.grid(column = 1, row = 1, stick="nsew")
        self._wa_lic.bind('<<ComboboxSelected>>', self._on_lic)
        attr_frame.columnconfigure(1, weight = 1)
        attr_frame.columnconfigure(3, weight = 1)
        attr_frame.grid(column = 0, row = 5, columnspan = 3, stick = "nsew", padx = 5, pady = 5)
        

    def apply_ln(self):
        state = DISABLED if self.ln_type is None else NORMAL
        self._w_id.configure(state = NORMAL)
        self._w_id.delete(0, 'end')
        if state == NORMAL: self._w_id.insert(0, self.ln_type.get('id'))
        self._w_id.configure(state = state)
        #desc
        self._w_desc.configure(state = NORMAL)
        self._w_desc.delete(0, 'end')
        if state == NORMAL: self._w_desc.insert(0, self.ln_type.get('desc'))
        self._w_desc.configure(state = state)
        #ns
        self._w_ns.configure(state = 'readonly', values = [''])
        self._w_ns.current(0)
        if state == NORMAL:
            spaces = [c for c in scl.get_nsd_of_ln_class(self.ln_type.get('lnClass'))]
            self._w_ns.configure(values = spaces)
            self._w_ns.current(spaces.index(self.ln_type.get('{%(emt)s}lnNs' % ns)))
        else: self._w_ns.configure(state = DISABLED)
        #class
        self._w_class.configure(state = NORMAL, values = [''])
        self._w_class.current(0)
        if state == NORMAL:
            classes = scl.get_ln_classes(self.ln_type.get('{%(emt)s}lnNs' % ns))
            self._w_class.configure(values = classes)
            self._w_class.current(classes.index(self.ln_type.get('lnClass')))
        else: self._w_class.configure(state = DISABLED)
        #prefix
        self._wa_prefix.configure(state = NORMAL)
        self._wa_prefix.delete(0, 'end')
        if state == NORMAL: self._wa_prefix.insert(0, self.ln_type.get('{%(emt)s}lnPrefix' % ns))
        self._wa_prefix.configure(state = state)
        #ld
        self._wa_ld.configure(state = NORMAL)
        self._wa_ld.delete(0, 'end')
        if state == NORMAL: self._wa_ld.insert(0, self.ln_type.get('{%(emt)s}ldInst' % ns))
        self._wa_ld.configure(state = state)
        #license
        self._wa_lic.configure(state = 'readonly', values = [''])
        self._wa_lic.current(0)
        if state == NORMAL:
            licenses = list(scl.settings.licenses.keys())
            self._wa_lic.configure(values = licenses)
            self._wa_lic.current(licenses.index(self.ln_type.get('{%(emt)s}license' % ns)))
        else: self._wa_lic.configure(state = DISABLED)

    def _on_lic(self, event):
        new_lic = event.widget.get()
        if new_lic == self.ln_type.get('{%(emt)s}license' % ns): return
        self._before_ln_change()
        self.ln_type.set('{%(emt)s}license' % ns, new_lic)
        self._on_ln_change()

    def _on_class(self, event):
        new_class = event.widget.get()
        if new_class == self.ln_type.get('lnClass'): return
        self._before_ln_change()
        self.ln_type.set('lnClass', new_class)
        for data_object in self.ln_type.findall('./61850:DO', ns):
            scl.fix_do_namespace(data_object)
        self._on_ln_change()

    def _on_esc_class(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.ln_type.get('lnClass'))

    def _on_ret_class(self, event):
        classes = scl.get_ln_classes(self.ln_type.get('{%(emt)s}lnNs' % ns))
        new_class = event.widget.get().upper()
        event.widget.delete(0, 'end')
        event.widget.insert(0, new_class) #this for uppercase update
        if new_class in classes: return self._on_class(event)
        if len(new_class) != 4 :
            self.bell()
            return self._on_esc_class(event)
        # add class to private namespace
        scl.add_private_node(new_class) # this action are not stored or undoredoed
        # change ln namespace and class
        self._before_ln_change()
        self.ln_type.set('lnClass', new_class)
        self.ln_type.set('{%(emt)s}lnNs' % ns, scl.private_namespace())
        for data_object in self.ln_type.findall('./61850:DO', ns):
            scl.fix_do_namespace(data_object)
        self._on_ln_change()

    def _on_ns(self, event):
        new_ns = event.widget.get()
        if new_ns == self.ln_type.get('{%(emt)s}lnNs' % ns): return
        self._before_ln_change()
        self.ln_type.set('{%(emt)s}lnNs' % ns, new_ns)
        for data_object in self.ln_type.findall('./61850:DO', ns):
            scl.fix_do_namespace(data_object)
        self._on_ln_change()

    def _on_id(self, event):
        new_id = event.widget.get()
        if new_id == self.ln_type.get('id'): return
        if new_id == '' or (self.ln_type.getparent().
                          find('./61850:LNodeType[@id="%s"]' % new_id, ns) is not None):
            self.bell()
            return self._on_esc_id(event)
        self._before_ln_change()
        self.ln_type.set('id', new_id)
        self._on_ln_change()

    def _on_esc_id(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.ln_type.get('id'))

    def _on_prefix(self, event):
        prefix = event.widget.get()
        if prefix == self.ln_type.get('{%(emt)s}lnPrefix' % ns): return
        self._before_ln_change()
        self.ln_type.set('{%(emt)s}lnPrefix' % ns, prefix)
        self._on_ln_change()

    def _on_esc_prefix(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.ln_type.get('{%(emt)s}lnPrefix' % ns))

    def _on_ld(self, event):
        ld_inst = event.widget.get()
        if ld_inst == self.ln_type.get('{%(emt)s}ldInst' % ns): return
        self._before_ln_change()
        self.ln_type.set('{%(emt)s}ldInst' % ns, ld_inst)
        self._on_ln_change()

    def _on_esc_ld(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.ln_type.get('{%(emt)s}ldInst' % ns))

    def _on_desc(self, event):
        desc = event.widget.get()
        if desc == self.ln_type.get('desc'): return
        self._before_ln_change()
        self.ln_type.set('desc', desc)
        self._on_ln_change()

    def _on_esc_desc(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.ln_type.get('desc'))

    def _before_ln_change(self):
        self.event_generate('<<BeforeLnChange>>')

    def _on_ln_change(self):
        self.event_generate('<<LnChange>>')

#====================================
#
#      Data Object Frame
#
#====================================

class DoFrame(Frame):
    def __init__(self, data = None, fix_ns = False, **kw):
        self.data_object = data
        #kw.update({'text': self.data_object.get('name')})
        kw.update({'cursor': 'arrow',
                   'takefocus': True,
                   'highlightthickness': 1,
                   'highlightcolor': 'blue'})
        Frame.__init__(self, **kw)
        self.valid_desc = (self.register(self.onDescValidate), '%P')
        self.valid_name = (self.register(self.onNameValidate),'%P')
        if fix_ns: scl.fix_do_namespace(self.data_object)
        self.create_widgets()
        self.apply_do()

    def configure(self, **kw):
        if 'data' in kw.keys():
            self.data_object = kw.pop('data')
            #kw.update({'text': self.data_object.get('name')})
            self.apply_do()
        if len(kw): super().configure(kw)

    def onDescValidate(self, P):
        if len(P)<255 and not set(P).intersection({'"', '\\'}):
            return True
        else:
            self.bell()
            return False

    def onNameValidate(self, P):
        if len(P) <= MAX_DO_NAME_LEN and\
           (len(P) == 0 or re.match("[A-Z][0-9A-Za-z]*$",P)):
            return True
        else:
            self.bell()
            return False
        
    def create_widgets(self):
        self._w_name = Entry(master = self, width = 20,
                             validate="key", validatecommand=self.valid_name)
        self._w_name.bind('<Return>', self._on_name)
        self._w_name.bind('<Escape>', self._on_esc_name)
        self._w_name.grid(column = 1, row = 0, rowspan = 2, stick="nsew")
        #cdc - select
        self._w_cdc = ttk.Combobox(master = self, width = 15, state='readonly')
        self._w_cdc.bind('<<ComboboxSelected>>', self._on_cdc)
        self._w_cdc.grid(column = 2, row = 0, stick="nsew")
        #type/id - select
        self._w_type = ttk.Combobox(master = self, width = 17, state = 'readonly')
        self._w_type.bind('<<ComboboxSelected>>', self._on_type)
        self._w_type.grid(column =3, row = 0, stick="nsew")
        #description - edit
        self._w_desc = Entry(master = self,
                             validate="key", validatecommand=self.valid_desc)
        self._w_desc.bind('<Return>', self._on_desc)
        self._w_desc.bind('<Escape>', self._on_esc_desc)
        self._w_desc.grid(column = 2, row = 1, columnspan = 5, stick="nsew")
        #process - select
        self._w_process = ttk.Combobox(master = self, width = 13, state = 'readonly')
        self._w_process.grid(column = 4, row = 0, stick="nsew")
        self._w_process.bind('<<ComboboxSelected>>', self._on_process)
        #dataNs - RO
        self._w_ns = Entry(master = self, width = 20)
        self._w_ns.grid(column = 5, row = 0, stick="nsew")
        #pc - RO
        self._w_pc = Entry(master = self, width = 12)
        self._w_pc.grid(column = 6, row = 0, stick="nsew")

    def apply_do(self):
        #simple values
        self._w_name.delete(0, 'end')
        self._w_name.insert(0, self.data_object.get('name'))
        self._w_desc.delete(0, 'end')
        self._w_desc.insert(0, self.data_object.get('desc'))
        #complicated values
        space, cdc, pc = scl.get_do_attrs(self.data_object.getparent().get('lnClass'),
                                          self.data_object.getparent().get('{%(emt)s}lnNs' % ns),
                                          self.data_object.get('name'))
        #cdc
        do_cdc = scl.dodas.find('./61850:DOType[@id="%s"]'%
                                self.data_object.get('type'), ns).get('cdc')
        assert do_cdc in cdc
        self._w_cdc.configure(values = cdc)
        self._w_cdc.current(cdc.index(do_cdc))
        #ns/pc
        assert self.data_object.get('{%(emt)s}dataNs' % ns) == space
        self._w_ns.configure(state = NORMAL)
        self._w_ns.delete(0, END)
        self._w_ns.insert(0, space)
        self._w_ns.configure(state = DISABLED)
        self._w_name.configure(fg = 'red4' if pc is None else 'black')
        self._w_pc.configure(state = NORMAL)
        self._w_pc.delete(0, END)
        self._w_pc.insert(0, 'n/a' if pc is None else pc)
        self._w_pc.configure(state = DISABLED)
        #type
        self._w_type.configure(values = scl.CDC_types[do_cdc])
        self._w_type.current(scl.CDC_types[do_cdc].
                             index(self.data_object.get('type')))
        #process
        if self.data_object.get('{%(emt)s}process' % ns):
            self._w_process.configure(state = 'readonly', values = PROC_VALUES)
            self._w_process.current(PROC_VALUES.index(self.data_object.get('{%(emt)s}process' % ns)))
        else:
            self._w_process.configure(state = NORMAL, values = ['n/a'])
            self._w_process.current(0)
            self._w_process.configure(state = DISABLED)
            
        
    def _on_name(self, event):
        name = event.widget.get()
        if name == self.data_object.get('name'): return
        if name == '' or (self.data_object.getparent().
                          find('./61850:DO[@name="%s"]' % name, ns) is not None):
            self.bell()
            return self._on_esc_name(event)
        self._before_object_change()
        #self.configure(text = name)
        self.data_object.set('name', name)
        #update ns, cdc, type, pc
        space, cdc, pc = scl.get_do_attrs(self.data_object.getparent().get('lnClass'),
                                          self.data_object.getparent().get('{%(emt)s}lnNs' % ns),
                                          self.data_object.get('name'))
        #ns/pc
        if self.data_object.get('{%(emt)s}dataNs' % ns) != space:
            self.data_object.set('{%(emt)s}dataNs' % ns, space)
        self._w_ns.configure(state = NORMAL)
        self._w_ns.delete(0, END)
        self._w_ns.insert(0, space)
        self._w_ns.configure(state = DISABLED)
        self._w_name.configure(fg = 'red4' if pc is None else 'black')
        self._w_pc.configure(state = NORMAL)
        self._w_pc.delete(0, END)
        self._w_pc.insert(0, 'n/a' if pc is None else pc)
        self._w_pc.configure(state = DISABLED)
        #cdc
        current_cdc = scl.dodas.find('./61850:DOType[@id="%s"]'%
                                     self.data_object.get('type'), ns).get('cdc')
        if not (current_cdc in cdc):
            current_cdc = cdc[0]
            # reconfigure type and process
            self._reconfig_type(current_cdc)
        self._w_cdc.configure(values = cdc)
        self._w_cdc.current(cdc.index(current_cdc))
        self._on_object_change()
        self.event_generate('<FocusIn>')# to update DA panel


    def _on_esc_name(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.data_object.get('name'))
        
    def _on_desc(self, event):
        desc = event.widget.get()
        if desc == self.data_object.get('desc'): return
        self._before_object_change()
        self.data_object.set('desc', desc)
        self._on_object_change()

    def _on_esc_desc(self, event):
        event.widget.delete(0, 'end')
        event.widget.insert(0, self.data_object.get('desc'))

    def _on_process(self, event):
        proc = event.widget.get()
        if proc == self.data_object.get('{%(emt)s}process' % ns): return
        self._before_object_change()
        self.data_object.set('{%(emt)s}process' % ns, proc)
        self._on_object_change()
        
    def _on_cdc(self, event):
        cdc = event.widget.get()
        if cdc == scl.dodas.find('./61850:DOType[@id="%s"]'%
                                 self.data_object.get('type'), ns).\
                                 get('cdc'): return
        self._before_object_change()
        # reconfigure type and process
        self._reconfig_type(cdc)
        self.event_generate('<FocusIn>')# to update DA panel
        self._on_object_change()


    def _on_type(self, event):
        dotype = event.widget.get()
        if dotype == self.data_object.get('type'): return
        self._before_object_change()
        self.data_object.set('type', dotype)
        # update da values
        scl.populate_da_values(self.data_object)
        self.event_generate('<FocusIn>')# to update DA panel
        # reconfigure process
        self._reconfig_process()
        self._on_object_change()

    def _reconfig_type(self, cdc):
        ''' helper subroutine for type value and followed update
        '''
        type_vals = scl.CDC_types[cdc]
        new_val = next((v for v in type_vals if self.data_object.get('name') in v),
                       type_vals[0])
        self._w_type.configure(values = type_vals)
        self._w_type.current(type_vals.index(new_val))
        self.data_object.set('type',new_val)
        # update da values
        scl.populate_da_values(self.data_object)
        # reconfigure process
        self._reconfig_process()

    def _reconfig_process(self):
        ''' helper subroutine for process value update
        '''
        proc = self.data_object.get('{%(emt)s}process' % ns)
        if scl.is_process(self.data_object):
            if proc is None:
                self.data_object.set('{%(emt)s}process' % ns, PROC_VALUES[0])
                self._w_process.configure(state = 'readonly', values = PROC_VALUES)
                self._w_process.current(0)
        elif proc is not None:
            self.data_object.attrib.pop('{%(emt)s}process' % ns)
            self._w_process.configure(state = NORMAL, values = ['n/a'])
            self._w_process.current(0)
            self._w_process.configure(state = DISABLED)

    def get_new(self):
        node = self.data_object.getparent()
        pos = node.index(self.data_object)
        do_name = self.data_object.get('name')
        #generate new name
        for k in range(1,len(do_name)+1):
            if not do_name[-k].isdigit(): break
        try:
            base = do_name[:-(k-1)]
            index = int(do_name[-(k-1):])+1
        except ValueError:
            base = do_name
            index = 1
        while True:
        #check no do with same name
            while True:
                same_name = node.find(
                    './61850:DO[@name="%s"]' % (base + str(index)), ns)
                if same_name is None: break
                pos = node.index(same_name)# for insert 5 after 4, etc
                index +=1
            #check name length
            if len(base + str(index)) <= MAX_DO_NAME_LEN: break
            else:
                letters = string.digits
                base = 'Foo' + ''.join(random.choice(letters) for i in range(8))
                index = 0
                pos = node.index(self.data_object)
                self.bell()        
        #duplicating
        node.insert(pos+1, deepcopy(self.data_object))
        node[pos+1].set('name', base + str(index))
        #fix dataNs, type, values
        return DoFrame(master = self.master, data = node[pos+1], fix_ns = True), pos+1

    def get_clone(self):
        return DoFrame(master = self.master, data = self.data_object)

    def exec_del(self):
        node = self.data_object.getparent()
        if len(node.findall('./61850:DO', ns)) == 1: return False
        self._before_object_change()
        node.remove(self.data_object)
        self._on_object_change()
        return True

    def exec_up(self):
        node = self.data_object.getparent()
        pos = node.index(self.data_object)
        if not pos: return False
        self._before_object_change()
        node.insert(pos-1, self.data_object)
        self._on_object_change()
        return True

    def exec_dn(self):
        node = self.data_object.getparent()
        pos = node.index(self.data_object)
        if pos >= (len(node)-1): return False
        self._before_object_change()
        node.insert(pos+2, self.data_object)
        self._on_object_change()
        return True

    def _on_object_change(self):
        self.event_generate('<<OnChange>>')
        
    def _before_object_change(self):
        self.event_generate('<<BeforeChange>>')
        
        

  
        
        
