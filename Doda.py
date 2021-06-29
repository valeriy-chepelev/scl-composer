from tkinter import *
import tkinter.ttk as ttk
import tkinter.messagebox as msg
from scrolled_tree import ScrolledTree
import lxml.etree as ET
import scl_engine as scl
from scl_engine import ns, nsURI, nsMap
import resources
from copy import deepcopy
from new_ln_dialog import NewLnDialog
from ui_panels import DoFrame, LnFrame, DaFrame
from dynamic_grid import DynamicGrid
from t_logger import T_logger
from logger_dialog import LoggerDialog
import logger_dialog as log
import logging
from undoredo import UndoRedo
from settings_dialog import SettingsDialog

# TODO list
# -- misc's --
# settings dialog and data
# work with licenses
# salt, integrity, nsd signing
# detect files change
# comments, versioning, status(draft/test/active/obsolete)
# code clear, exe, setup, code signing
# -- data processing --
# DONE check dodas-changes processings
# DONE change ln class
# DONE private ns for unknown ln's
# DONE custom ln class for private ns
# export to document
# export to NSD
# -- interface --
# DONE colorize namespace in tree
# ln stats: rate of private, rate of mandatory, rate of values
# keyboard shortcuts
# do tiles
# update entries on focus-out
# size and pos restoring
# win icons

def fixed_map(option):
    # Fix for setting text colour for Tkinter 8.6.9
    # From: https://core.tcl.tk/tk/info/509cafafae
    #
    # Returns the style map for 'option' with any styles starting with
    # ('!disabled', '!selected', ...) filtered out.

    # style.map() returns an empty list for missing options, so this
    # should be future-safe.
    return [elm for elm in style.map('Treeview', query_opt=option) if
        elm[:2] != ('!disabled', '!selected')]
style = ttk.Style()
style.map('Treeview', foreground=fixed_map('foreground'), background=fixed_map('background'))
# fix end

class Do_images():
    def __init__(self):
        self.do_ins = PhotoImage(data=resources.ICO_DO_INS)
        self.do_dup = PhotoImage(data=resources.ICO_DO_DUP)
        self.do_del = PhotoImage(data=resources.ICO_DO_DEL)
        self.gear = PhotoImage(data=resources.ICO_GEAR)
        self.log = PhotoImage(data=resources.ICO_LOG)
        self.log_r = PhotoImage(data=resources.ICO_LOG_RED)
        self.nsd = PhotoImage(data=resources.ICO_NSD)
        self.csv = PhotoImage(data=resources.ICO_CSV)
        self.undo = PhotoImage(data=resources.ICO_UNDO)
        self.redo = PhotoImage(data=resources.ICO_REDO)

icons = None


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+S+E+W)
        self.create_widgets()

    def start_app(self):
        #configure logging
        global log
        self.log_form = LoggerDialog(self)
        log.logger = logging.getLogger(__name__)
        log.logger.setLevel(logging.DEBUG)
        log.logger.addHandler(self.log_form.logging_handler)
        log.logger.info('Application start')
        #load scl engine
        self.save_block = not scl.init()
        #application start
        self.master.title('Doda - LN creation tool')
        self.master.minsize(600, 500)
        self.fill_ln_tree()
        self.undo_redo = UndoRedo(scl.ln_file)
        self.ur_ops = None
        log.logger.info('Start complete')
        self.after(2000, self.check_log)
        self.mainloop()
    

    def create_widgets(self):
        top=self.winfo_toplevel()
        top.rowconfigure(0, minsize=500, weight=1)
        top.columnconfigure(0, minsize=600, weight=1)

        self.main_pane = PanedWindow(master = self,
                                     bd=2,
                                     orient=HORIZONTAL,
                                     sashrelief = 'groove')
        self.objects_pane = PanedWindow(master = self.main_pane,
                                        bd=2,
                                        orient=VERTICAL,
                                        sashrelief = 'groove')

        ln_pane = Frame(master = self.main_pane)
        
        self.ln_tree = ScrolledTree(master=ln_pane,
                                    show='tree headings',
                                    selectmode='browse')
        self.ln_tree['columns']=('desc')
        self.ln_tree.column("#0", width=150, minwidth=100, stretch=NO)
        self.ln_tree.column("desc", width=150, minwidth=100 )
        self.ln_tree.heading("#0",text="Class",anchor=W)
        self.ln_tree.heading("desc", text="Description",anchor=W)
        self.ln_tree.bind("<<TreeviewSelect>>", self.on_ln_select)
        self.ln_tree.pack(side = BOTTOM, fill = BOTH, expand=True, padx=3)
        # Top-left buttons
        global icons
        if icons is None: icons = Do_images()
        ln_ctrl = LabelFrame(master = ln_pane, text = 'LNodeType')
        Button(master = ln_ctrl, image = icons.do_ins, relief = 'flat',
               cursor = 'hand2', takefocus = 0,
               command = self.on_ln_new).\
               grid(column = 0, row = 0, stick="nsew", padx = (3,0))
        self._b_dup = Button(master = ln_ctrl, image = icons.do_dup, relief = 'flat',
                             cursor = 'hand2', takefocus = 0,
                             state = DISABLED, command = self.on_ln_dup)
        self._b_dup.grid(column = 1, row = 0, stick="nsew")
        self._b_del = Button(master = ln_ctrl, image = icons.do_del, relief = 'flat',
                             cursor = 'hand2', takefocus = 0,
                             state = DISABLED, command = self.on_ln_del)
        self._b_del.grid(column = 2, row = 0, stick="nsew")

        #column 3 is free for space
        #columns 4,5 for undo/redo btns
        self._b_undo = Button(master = ln_ctrl, image = icons.undo, relief = 'flat', takefocus = 0,
               cursor = 'hand2', command = self.on_undo, state = DISABLED)
        self._b_undo.grid(column = 5, row = 0, stick="nsew")
        self._b_redo = Button(master = ln_ctrl, image = icons.redo, relief = 'flat', takefocus = 0,
               cursor = 'hand2', command = self.on_redo, state = DISABLED)
        self._b_redo.grid(column = 4, row = 0, stick="nsew")
        
        Button(master = ln_ctrl, image = icons.gear, relief = 'flat',
               cursor = 'hand2', takefocus = 0, command = self.on_settings).\
               grid(column = 9, row = 0, stick="nsew", padx = (0,5))
        self._b_log = Button(master = ln_ctrl, image = icons.log, cursor = 'hand2', 
                             relief = 'flat', takefocus = 0, command = self.on_log)
        self._b_log.grid(column = 8, row = 0, stick="nsew")
        Button(master = ln_ctrl, image = icons.nsd, relief = 'flat', takefocus = 0,
               cursor = 'hand2', command = self.on_log, state = DISABLED).\
               grid(column = 7, row = 0, stick="nsew", padx = (0,5))
        Button(master = ln_ctrl, image = icons.csv, relief = 'flat', takefocus = 0,
               cursor = 'hand2', command = self.on_log, state = DISABLED).\
               grid(column = 6, row = 0, stick="nsew")
  
        self.ln_info = LnFrame(master = ln_ctrl)
        self.ln_info.bind("<<BeforeLnChange>>", self.push_undo)
        self.ln_info.bind("<<LnChange>>", self.on_change)
        self.ln_info.grid(column = 0, row = 1, columnspan = 10, stick="nsew")
        ln_ctrl.columnconfigure(3, weight = 1)
        ln_ctrl.pack(side = TOP, fill = X, pady = (2,5), padx = 2)

         
        self.panel = DynamicGrid(master = self.objects_pane,
                                 text = 'Data Objects',
                                 controls = 1)
        self.panel.bind('<<FrameFocus>>', self.fill_da)
        self.panel.bind('<<BeforeChange>>', self.push_undo)
        self.panel.bind('<<OnChange>>', self.on_change)
        
        self.da_panel = DynamicGrid(master = self.objects_pane,
                                    text = 'Predefined values',
                                    controls = 2)
        self.da_panel.bind('<<BeforeChange>>', self.push_undo)
        self.da_panel.bind('<<OnChange>>', self.on_change)
        
        self.main_pane.add(ln_pane, minsize=300, width=300)
        self.main_pane.add(self.objects_pane, minsize=200, width = 700)
        self.objects_pane.add(self.panel, minsize=100)
        self.objects_pane.add(self.da_panel, height=100, minsize=100)

        self.main_pane.grid(column=0, row=0, sticky='nesw')
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def on_log(self):
        self.log_form.show()

    def check_log(self):
        if self.log_form.log_status: self._b_log.configure(image = icons.log_r)
        else: self._b_log.configure(image = icons.log)
        if self.save_block: self.show_critical_stop()
        else: self.after(5000, self.check_log)

    def on_settings(self):
        scl.update_licenses()
        d = SettingsDialog(self).show(scl.settings)

    def show_critical_stop(self):
        msg.showerror(title='Critical error',
                      message='Data have critical errors or misses.\n'+\
                      'See log for details.\n'+\
                      'Correct settings and restart.\n'+\
                      'DO NOT make any changes to project, saving blocked.')   
        
    # ================================
    #    UNDO/REDO/SAVE
    # ================================

    def push_undo(self, event):
        '''call before changes to be made
        to store data to the undo stack
        '''
        ######################
        # this options fixed before the operation, and
        # saved to the previous undo stack position
        #######################
        self.ur_ops = {'lnfocus' : self.ln_tree.focus(),
                       'dofocus' : self.panel.data_object.get('name')\
                       if self.panel.data_object is not None else None,
                       'lnvsb' : self.ln_tree.yview()[0],
                       'dovsb' : self.panel.text.yview()[0],
                       'davsb' : self.da_panel.text.yview()[0]}

    def on_change(self, event):
        # update integrity
        if self.ln_info.ln_type is not None:
            self.ln_info.ln_type.set('{%(emt)s}integrity' % ns,
                                     scl.hash_ln(self.ln_info.ln_type))
        # update tree if needed
        if event is not None and event.widget is self.ln_info:
            self.update_tree(event)
        # create state after-options for redo
        ops = {'lnfocus' : self.ln_tree.focus(),
               'dofocus' : self.panel.data_object.get('name')\
               if self.panel.data_object is not None else None,
               'lnvsb' : self.ln_tree.yview()[0],
               'dovsb' : self.panel.text.yview()[0],
               'davsb' : self.da_panel.text.yview()[0]}
        #save data, push undoredo and update buttons
        if self.save_block:
            self.bell()
            self.show_critical_stop()
            return
        scl.save_lns()
        self.undo_redo.push(scl.ln_file, op_before = self.ur_ops, op_after = ops)
        self._b_undo.configure(state = NORMAL)
        self._b_redo.configure(state = DISABLED)

    def on_undo(self):
        self.exec_undoredo(self.undo_redo.undo())
        scl.save_lns()
        self._b_undo.configure(state = NORMAL if self.undo_redo.can_undo()\
                               else DISABLED)
        self._b_redo.configure(state = NORMAL if self.undo_redo.can_redo()\
                               else DISABLED)

    def on_redo(self):
        self.exec_undoredo(self.undo_redo.redo())
        scl.save_lns()
        self._b_undo.configure(state = NORMAL if self.undo_redo.can_undo()\
                               else DISABLED)
        self._b_redo.configure(state = NORMAL if self.undo_redo.can_redo()\
                               else DISABLED)

    def exec_undoredo(self, param):
        file, options = param
        #load lntypes
        scl.q_load_lns(file)
        #refill tree
        self.fill_ln_tree()
        #execute options
        if options is None:
            self.ln_tree.selection()
            self.fill_panel(None)
        else:
            self.ln_tree.yview_moveto(options['lnvsb'])
            self.ln_tree.focus(options['lnfocus'])
            self.ln_tree.selection_set(options['lnfocus'])
            self.update()
            self.panel.text.yview_moveto(options['dovsb'])
            w = next((name for name in self.panel.text.window_names()\
                      if self.nametowidget(name).data_object.get('name')\
                      == options['dofocus']), None)
            if w is not None: self.nametowidget(w).focus_set()
            self.update()
            self.da_panel.text.yview_moveto(options['davsb'])


        
    # ================================
    #    LN Events handlers
    # ================================

    def on_ln_select(self, event):
        state = NORMAL
        try:
            ln_id = event.widget.focus().split('.')[1]
            data = scl.lntypes.find('./61850:LNodeType[@id="%s"]' % ln_id, ns)
        except IndexError:
            data = None
            state = DISABLED
        self.ln_info.configure(data = data)
        self._b_dup.configure(state = state)
        self._b_del.configure(state = state)
        self.fill_panel(data)

    def on_ln_new(self):
        d = NewLnDialog(self).show()
        if d[0] is None: return
        self.push_undo(None)
        #create LNodeType
        index = 1
        while scl.lntypes.find('./61850:LNodeType[@id="%s"]' % (d[2].lower() + str(index)), ns) is not None:
            index +=1
        ln_id = d[2].lower() + str(index)
        ln_type = ET.SubElement(scl.lntypes, nsURI+'LNodeType', nsmap = nsMap )
        ln_type.attrib.update({'lnClass' : d[2],
                               'id' : ln_id,
                               'desc' : '',
                               '{%(emt)s}lnNs' % ns : d[1],
                               '{%(emt)s}lnPrefix' % ns : '',
                               '{%(emt)s}ldInst' % ns : '',
                               '{%(emt)s}license' % ns : 'None'})
        #fill data objects
        for obj in scl.get_nsd_object(d[1], d[2]):
            if (d[0] == 'Mandatory' and obj['pres'][:2] in ('M', 'MO', 'MF'))\
               or d[0] == 'All' and obj['pres'] != 'F':
                do_type = scl.dodas.find('./61850:DOType[@cdc="%s"]' % obj['cdc'], ns)
                if do_type is None:
                    log.logger.warning('CDC "%s" for DO "%s" in lnClass "%s" (namespace "%s") missed in datatypes, DO ignored.',
                                       obj['cdc'], obj['name'], d[2], d[1])
                else:
                    do_id = next((type_id for type_id in scl.CDC_types[obj['cdc']]\
                                 if obj['name'] in type_id), do_type.get('id'))
                    do_desc = scl.dodas.find('./61850:DOType[@id="%s"]' %
                                             do_id, ns).get('desc')
                    data_object = ln_type.find('./61850:DO[@name="%s"]' % obj['name'], ns) # in case of extension
                    if data_object is None:
                        data_object = ET.SubElement(ln_type, nsURI+'DO', nsmap = nsMap )
                    data_object.attrib.update({'name' : obj['name'],
                                               'type' : do_id,
                                               'desc' : '' if do_desc is None else do_desc,
                                               '{%(emt)s}dataNs' % ns : obj['space']})
                    if scl.is_process(data_object):
                        data_object.attrib.update({'{%(emt)s}process' % ns : 'model'})
                    scl.populate_da_values(data_object)
        ln_type.set('{%(emt)s}integrity' % ns, scl.hash_ln(ln_type))
        #update tree
        if not self.ln_tree.exists(d[2]):
            self.ln_tree.insert(parent = '',
                                index = END,
                                iid = d[2],
                                text = d[2])
            self.resort_tree()
        ln_iid = d[2] + '.' + ln_id
        self.ln_tree.insert(parent = d[2],
                            index = END,
                            iid = ln_iid, text = ln_id,
                            values = (''),
                            tags = [d[1]])
        self.resort_tree(d[2])
        self.ln_tree.see(ln_iid)
        self.ln_tree.focus(ln_iid)
        self.ln_tree.selection_set(ln_iid)
        self.on_change(None)

    def on_ln_dup(self):
        ln_type = self.ln_info.ln_type
        ln_id = ln_type.get('id')
        #generate new ln_id
        for k in range(1,len(ln_id)+1):
            if not ln_id[-k].isdigit(): break
        try:
            base = ln_id[:-(k-1)]
            index = int(ln_id[-(k-1):])+1
        except ValueError:
            base = ln_id
            index = 1
        #check no ln_id with same name
        while scl.lntypes.find('./61850:LNodeType[@id="%s"]' % (base + str(index)), ns) is not None:
            index +=1
        #duplicating
        self.push_undo(None)
        new_type = deepcopy(ln_type)
        ln_id = base + str(index)
        new_type.set('id', ln_id)
        new_type.set('{%(emt)s}integrity' % ns, scl.hash_ln(new_type))
        ln_type.getparent().append(new_type)
        #update tree
        iid = self.ln_tree.focus()
        new_iid = iid.split('.')[0] + '.' + ln_id
        self.ln_tree.insert(parent = self.ln_tree.parent(iid),
                            index = self.ln_tree.index(iid)+1,
                            iid = new_iid, text = ln_id,
                            values = self.ln_tree.item(iid, 'values'),
                            tags = self.ln_tree.item(iid, 'tags'))
        self.resort_tree(new_iid.split('.')[0])
        self.ln_tree.see(new_iid)
        self.ln_tree.focus(new_iid)
        self.do_vsb_pos = 0.0
        self.ln_tree.selection_set(new_iid)
        self.on_change(None)

    def on_ln_del(self):
        self.push_undo(None)
        self.ln_info.ln_type.getparent().remove(self.ln_info.ln_type)
        #tree update
        iid = self.ln_tree.focus()
        ln_class = iid.split('.')[0]# focus to ln class
        if len(self.ln_tree.get_children(ln_class)) == 1:
            # ln class should be deleted also, no new focus
            self.ln_tree.delete(ln_class)
            self.ln_info.configure(data = None)
            self._b_dup.configure(state = DISABLED)
            self._b_del.configure(state = DISABLED)

            self.fill_panel(None)
        else:
            self.ln_tree.delete(iid)
            self.ln_tree.see(ln_class)
            self.ln_tree.focus(ln_class)
            self.ln_tree.selection_set(ln_class)
        self.on_change(None)

    # ================================
    #    LN Tree routines
    # ================================

    def update_tree(self, event):
        new_id = event.widget.ln_type.get('id')
        new_cls = event.widget.ln_type.get('lnClass')
        new_iid = new_cls + '.' + new_id
        iid = self.ln_tree.focus()
        cls, _ = iid.split('.')
        if new_iid != iid:
            if not self.ln_tree.exists(new_cls):
                self.ln_tree.insert(parent = '',
                                    index = END,
                                    iid = new_cls,
                                    text = new_cls)
                self.resort_tree()
            self.ln_tree.insert(parent = new_cls,
                                index = END,
                                iid = new_iid,
                                text = new_id,
                                values = [event.widget.ln_type.get('desc')],
                                tags = [event.widget.ln_type.get('{%(emt)s}lnNs' % ns)])
            if len(self.ln_tree.get_children(cls)) == 1:
                self.ln_tree.delete(cls)
            else: self.ln_tree.delete(iid)
            self.resort_tree(new_cls)
            self.ln_tree.see(new_iid)
            self.ln_tree.focus(new_iid)
            self.ln_tree.selection_set(new_iid)
        elif not event.widget.ln_type.get('desc') in self.ln_tree.item(iid, 'values'):
            self.ln_tree.item(iid, values = [event.widget.ln_type.get('desc')])
        else:
            self.ln_tree.item(iid, tags = [event.widget.ln_type.get('{%(emt)s}lnNs' % ns)])
            self.ln_tree.see(new_iid)
            self.ln_tree.focus(new_iid)
            self.ln_tree.selection_set(new_iid)

    def fill_ln_tree(self):
        self.ln_tree.delete(*self.ln_tree.get_children())
        self.ln_tree.tag_configure(scl.private_namespace(), foreground = 'red4')

        ln_classes = sorted({ item.get('lnClass') for item in
                              scl.lntypes.findall('./61850:LNodeType', ns)})
        for ln_class in ln_classes:
            pos = self.ln_tree.insert(parent = '',
                                      index = END,
                                      iid = ln_class,
                                      text = ln_class,
                                      open = True)
            for ln_type in scl.lntypes.findall('./61850:LNodeType[@lnClass="%s"]'%ln_class, ns):
                self.ln_tree.insert(parent = pos,
                                    index = END,
                                    iid = ln_class + '.' + ln_type.get('id'),
                                    text = ln_type.get('id'),
                                    values = [ln_type.get('desc')],
                                    tags = [ln_type.get('{%(emt)s}lnNs' % ns)] )
            self.resort_tree(ln_class)
                
    def resort_tree(self, ln_class=''):
        def pair(val):
            for k in range(1,len(val)+1):
                if not val[-k].isdigit(): break
            try:
                a = val[:-(k-1)]
                b = int(val[-(k-1):])
            except ValueError:
                a = val
                b = 0
            return (a,b)
        if ln_class == '':
            nodes = sorted(self.ln_tree.get_children(ln_class))
        else:
            nodes = sorted(self.ln_tree.get_children(ln_class),key=lambda lnt: pair(lnt.split('.')[1]))
        for index, item in enumerate(nodes):
            self.ln_tree.move(item, ln_class, index)

    # ================================
    #    DO panel routines
    # ================================

    def fill_panel(self, ln_type):
        self.panel.clear()
        self.fill_da()
        if ln_type is None: return
        for data_object in ln_type.findall('./61850:DO', ns):
            do_frame = DoFrame(master = self.panel.text, data = data_object)
            self.panel.add_frame(do_frame)
        self.panel.finalize()#fix correct scrolling to last frame


    # ================================
    #    DA panel routines
    # ================================

    def fill_da(self, event = None):
        self.da_panel.clear()
        if (event is not None) and (event.widget.data_object is not None):
            self.da_panel.configure(text = event.widget.data_object.\
                                    get('name') + ' predefined values')
            for bda_data in scl.get_bda(event.widget.data_object,
                                                        ['CF', 'SE', 'SG', 'SP', 'DC']):
                if bda_data['bda'].get('name') == 'dU': continue
                self.da_panel.add_frame(DaFrame(master = self.da_panel.text,
                                                data = event.widget.data_object,
                                                bda_data = bda_data))
        else: self.da_panel.configure(text = 'Predefined values')

        

app = Application()
app.start_app()
