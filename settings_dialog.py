from tkinter import *
import tkinter.ttk as ttk
import tkinter.messagebox as msg
from scrolled_tree import ScrolledTree
import os
import string
import logger_dialog as log
import resources
import base58

LIC_CHARS = set(string.ascii_letters + string.digits + '_')

class SettingsDialog:
    def __init__(self, parent):
        self.parent = parent
        #form
        self.top = Toplevel(parent)
        self.top.title('Settings')
        self.top.minsize(600, 440)
        self.top.maxsize(600, 440)
        self.top.geometry('600x440+%s+%s' % (parent.winfo_rootx()+50 , parent.winfo_rooty()+50))
        self.top.transient(parent)
        self.top.grab_set()
        self.create_widgets()

    def create_widgets(self):
        # icons
        self.ico_new = PhotoImage(data=resources.ICO_DO_INS)
        self.ico_del = PhotoImage(data=resources.ICO_DO_DEL)
        self.ico_lic = PhotoImage(data=resources.ICO_LIC)
        self.ico_lic_used = PhotoImage(data=resources.ICO_LIC2)
        # validators
        self.valid_lic = (self.top.register(self.on_validate_lic),'%P')
        
        #control variables
        self.cv_dodas = StringVar()
        self.cv_lntypes = StringVar()
        self.cv_nsd = StringVar()
        self.cv_private = StringVar()
        self.cv_s_dodas = StringVar()
        self.cv_s_lntypes = StringVar()
        self.cv_s_nsd = StringVar()
        #files
        f = LabelFrame(self.top, text = 'Files', padx = 5, pady = 5)
        Label(f, text = 'LN types file:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 0, columnspan  = 2, stick="nsew")
        Entry(f, width = 15, textvariable = self.cv_lntypes)\
                 .grid(column = 0, row = 1, stick="nsew")
        Button(f, text = 'Browse').grid(column = 1, row = 1, stick="nsew")
        Label(f, text = 'DO/DA database file:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 2, columnspan  = 2, stick="nsew")
        Entry(f, width = 15, textvariable = self.cv_dodas)\
                 .grid(column = 0, row = 3, stick="nsew")
        Button(f, text = 'Browse').grid(column = 1, row = 3, stick="nsew")
        Label(f, text = 'NSD folder:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 4, columnspan  = 2, stick="nsew")
        Entry(f, width = 15, textvariable = self.cv_nsd)\
                 .grid(column = 0, row = 5, stick="nsew")
        Button(f, text = 'Browse').grid(column = 1, row = 5, stick="nsew")
        f.columnconfigure(0, weight = 1)
        f.grid(column = 0, row = 0, stick="nsew", padx = 5)
        
        #private namespace
        f = LabelFrame(self.top, text = 'Namespace', padx = 5, pady = 5)
        Label(f, text = 'Private namespace id:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 0, stick="nsew")
        Entry(f, width = 20, textvariable = self.cv_private)\
                 .grid(column = 0, row = 1, stick="nsew")
        Button(f, text = 'Default', command = self.on_def_ns)\
                  .grid(column = 1, row = 1, stick="nsew")
        f.columnconfigure(0, weight = 1)
        f.grid(column = 0, row = 1, stick="nsew", padx = 5)

        #salt
        f = LabelFrame(self.top, text = 'Security', padx = 5, pady = 5)
        Label(f, text = 'WARNING! Affects data compatibility!\nDo not change without manner!').\
                 grid(column = 0, row = 0, columnspan = 3, stick="nsew")
        Label(f, text = 'LN types:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 1, stick="nsew")
        Label(f, text = "DO/DA's:", state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 2, stick="nsew")
        Label(f, text = 'NSDs:', state = DISABLED, anchor = 'w').\
                 grid(column = 0, row = 3, stick="nsew")
        Entry(f, textvariable = self.cv_s_lntypes).grid(column = 1, row = 1, stick="nsew")
        Button(f, text = 'New', command = self.on_s_lntypes).grid(column = 2, row = 1, stick="nsew")
        Entry(f, textvariable = self.cv_s_dodas).grid(column = 1, row = 2, stick="nsew")
        Button(f, text = 'New', command = self.on_s_dodas).grid(column = 2, row = 2, stick="nsew")
        Entry(f, textvariable = self.cv_s_nsd).grid(column = 1, row = 3, stick="nsew")
        Button(f, text = 'New', command = self.on_s_nsd).grid(column = 2, row = 3, stick="nsew")
        f.columnconfigure(1, weight = 1)
        f.rowconfigure(0, weight = 1)
        f.grid(column = 0, row = 2, stick="nsew", padx = 5)

        #licensing
        f = LabelFrame(self.top, text = 'Licenses', padx = 5, pady = 5)
        Label(f, text = 'Note: Used licenses can not be changed or deleted.',
              anchor = 'w', justify = LEFT, state = DISABLED).\
                 grid(column = 0, row = 0, columnspan = 3, stick="nsew")
        
        self._w_lic_edit = Entry(f, state = DISABLED,
                                 validate="key", validatecommand=self.valid_lic)
        self._w_lic_edit.grid(column = 0, row = 1, stick="nsew")
        self._w_lic_edit.bind('<Return>', self.on_lic_change)
        self._w_lic_edit.bind('<Escape>', self.on_lic_esc)

        self._b_lic_new = Button(master = f, image = self.ico_new, relief = 'flat',
                                 cursor = 'hand2', takefocus = 0,
                                 command = self.on_lic_new)
        self._b_lic_new.grid(column = 1, row = 1, stick = 'nsew')
        self._b_lic_del = Button(master = f, image = self.ico_del, relief = 'flat',
                                 cursor = 'hand2', takefocus = 0,
                                 state = DISABLED, command = self.on_lic_del)
        self._b_lic_del.grid(column = 2, row = 1, stick = 'nsew')

        self._w_lic = ScrolledTree(master = f, xscroll = False,
                                   show='tree',
                                   selectmode='browse')
        self._w_lic.grid(column = 0, row = 2, columnspan = 3, stick = 'nsew')
        self._w_lic.bind("<<TreeviewSelect>>", self.on_lic_select)
        self._w_lic.tag_configure('used', image = self.ico_lic_used)
        self._w_lic.tag_configure('lic', image = self.ico_lic)
        
        f.columnconfigure(0, weight = 1)
        f.rowconfigure(2, weight = 1)
        f.grid(column = 1, row = 0, rowspan = 3, stick="nsew", padx = (0,5))

        #action buttons
        self.controls = Frame(self.top)
        self.controls.grid(column = 0, row = 3, columnspan = 2, stick="nsew")
        Button(master = self.controls, text = 'Apply', state = DISABLED, pady = 5, padx = 10,
               command = self.on_apply).pack(side = RIGHT, fill = X, padx = 5, pady = 5)
        
        self.top.columnconfigure(0, weight = 1)
        self.top.columnconfigure(1, weight = 1)
        self.top.rowconfigure(2, weight = 1)

    def fill_settings(self, settings):
        self.cv_dodas.set(settings.settings['dodas'])
        self.cv_lntypes.set(settings.settings['lntypes'])
        self.cv_nsd.set(settings.settings['nsd'])
        self.cv_private.set(settings.settings['private_ns'])
        self.cv_s_dodas.set(settings.settings['s_dodas'])
        self.cv_s_lntypes.set(settings.settings['s_lntypes'])
        self.cv_s_nsd.set(settings.settings['s_nsd'])
        for lic, lic_used in settings.licenses.items():
            self._w_lic.insert(parent = '',
                               index = END,
                               text = lic,
                               tags = ['used'] if lic_used or lic == 'None' else ['lic'])

    def on_apply(self):
        #self.dos = 'All'
        self.top.destroy()

    def show(self, settings):
        self.fill_settings(settings)
        self.top.wm_deiconify()
        self.parent.wait_window(self.top)
        #return (self.dos,) + self.selected

    #==============================
    #       LIC HANDLERS
    #==============================

    def on_validate_lic(self, P):
        if set(P).issubset(LIC_CHARS):
            return True
        self.top.bell()
        return False
    
    def on_lic_select(self, event):
        self._w_lic_edit.configure(state = NORMAL)
        self._w_lic_edit.delete(0,END)
        self._w_lic_edit.insert(0, self._w_lic.item(self._w_lic.focus(), 'text'))
        if 'used' in self._w_lic.item(self._w_lic.focus(), 'tags'):
            self._w_lic_edit.configure(state = DISABLED)
            self._b_lic_del.configure(state = DISABLED)
        else:
            self._b_lic_del.configure(state = NORMAL)

    def on_lic_change(self, event):
        new_lic = event.widget.get()
        if new_lic == self._w_lic.item(self._w_lic.focus(), 'text'): return
        if new_lic in [self._w_lic.item(iid, 'text')\
           for iid in self._w_lic.get_children()] or new_lic == '':
            self.top.bell()
            return self.on_lic_esc(event)
        self._w_lic.item(self._w_lic.focus(), text = new_lic)
        self.resort_lic()
        

    def on_lic_esc(self, event):
        self._w_lic_edit.delete(0,END)
        self._w_lic_edit.insert(0, self._w_lic.item(self._w_lic.focus(), 'text'))
        self._w_lic_edit.select_range(0, END)

    def on_lic_new(self):
        names = [self._w_lic.item(iid, 'text') for iid in self._w_lic.get_children()]
        index = 1
        while 'New_'+str(index) in names: index +=1
        iid = self._w_lic.insert(parent = '',
                                 index = END,
                                 text = 'New_'+str(index),
                                 tags = ['lic'])
        self.resort_lic()
        self._w_lic.see(iid)
        self._w_lic.focus(iid)
        self._w_lic.selection_set(iid)

    def on_lic_del(self):
        iid = self._w_lic.next(self._w_lic.focus())
        if iid == '': iid = self._w_lic.prev(self._w_lic.focus())
        self._w_lic.delete(self._w_lic.focus())
        self._w_lic.see(iid)
        self._w_lic.focus(iid)
        self._w_lic.selection_set(iid)

    def resort_lic(self):
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
        nodes = sorted(self._w_lic.get_children(), key = lambda lic: pair(self._w_lic.item(lic, 'text')))
        for index, item in enumerate(nodes):
            self._w_lic.move(item, '', index)

    def on_def_ns(self):
        self.cv_private.set('MT NPP:2021A')

    #==============================
    #       SALT HANDLERS
    #==============================

    def on_s_dodas(self):
        if msg.showwarning(title = 'WARNING',
                           message='You are going to change a security value\n'+\
                           'of DO/DA database.\n'+\
                           'That leads to data incompatibility.\n'+\
                           'Sure proceed ?',
                           type = 'yesno') == 'yes':
            self.cv_s_dodas.set(base58.b58encode(os.urandom(8)))

    def on_s_lntypes(self):
        if msg.showwarning(title = 'WARNING',
                           message='You are going to change a security value\n'+\
                           'of LN types files.\n'+\
                           'That leads to data incompatibility.\n'+\
                           'Sure proceed ?',
                           type = 'yesno') == 'yes':
            self.cv_s_lntypes.set(base58.b58encode(os.urandom(8)))

    def on_s_nsd(self):
        if msg.showwarning(title = 'WARNING',
                           message='You are going to change a security value\n'+\
                           'of NSD files.\n'+\
                           'That leads to data incompatibility.\n'+\
                           'Sure proceed ?',
                           type = 'yesno') == 'yes':
            self.cv_s_nsd.set(base58.b58encode(os.urandom(8)))

def main():
    #testing
    s = SettingsValues('test_set.xml')
    #s.save()
    s.load(do_log = False)
    print(type(s.settings), s.settings)
    print(s.lic_list)

if __name__ == '__main__':
    main()


        
