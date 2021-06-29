from tkinter import *
import tkinter.ttk as ttk
from scrolled_tree import ScrolledTree
import scl_engine as scl

class NewLnDialog:
    def __init__(self, parent):
        self.parent = parent
        #form
        self.top = Toplevel(parent)
        self.top.title('New LNType')
        self.top.minsize(200, 250)
        self.top.maxsize(200, 1000)
        self.top.geometry('200x300+%s+%s' % (parent.winfo_rootx()+50 , parent.winfo_rooty()+50))
        self.top.transient(parent)
        self.top.grab_set()
        #widgets
        #action buttons
        self.controls = Frame(self.top)
        self.controls.pack(side = BOTTOM, fill = X, expand = False)
        Button(master = self.controls, text = 'Create with MANDATORY DOs', state = DISABLED, pady = 5,
               command = self.on_mandatory).pack(side = TOP, fill = X, padx = 5, pady = (5,0))
        Button(master = self.controls, text = 'Create with ALL DOs\nCautions: many objects', state = DISABLED, pady = 5,
               command = self.on_all).pack(side = TOP, fill = X, padx = 5, pady = 5)
        #tree
        f = LabelFrame(self.top, text = 'Select LN Class')
        f.pack(side = TOP, fill = BOTH, expand = True, padx = 5)
        #fill up tree with classes
        self.selected = ('','')
        self.dos = None
        t = ScrolledTree(master=f, xscroll=False, show='tree', selectmode='browse')
        for nsd in scl.NSD.keys():
            t.insert(parent='', index = END, iid = nsd, text = nsd)
            ln_classes = [cls.get('name') for cls in scl.NSD[nsd].findall('.//NSD:LNClass', scl.ns)]
            for ln_class in sorted(ln_classes):
                group_iid = nsd + '.' + ln_class[0]
                if not t.exists(group_iid):
                    t.insert(parent = nsd, index = END, iid = group_iid,
                             text = ln_class[0])
                t.insert(parent = group_iid, index = END, iid = nsd + '.' + ln_class, text = ln_class)
        t.bind("<<TreeviewSelect>>", self.on_class_select)
        t.pack(side = TOP, fill = BOTH, expand=True, padx = 5, pady = 5)

    def on_class_select(self, event):
        iid = event.widget.focus()
        val = event.widget.item(iid, 'text')
        if len(val) > 1 and ('.' in iid):
            self.selected = (iid.split('.')[0], val)
            for widget in self.controls.winfo_children():
                widget.configure(state = NORMAL)
        else:
            for widget in self.controls.winfo_children():
                widget.configure(state = DISABLED)

    def on_mandatory(self):
        self.dos = 'Mandatory'
        self.top.destroy()

    def on_all(self):
        self.dos = 'All'
        self.top.destroy()

    def show(self):
        self.top.wm_deiconify()
        self.parent.wait_window(self.top)
        return (self.dos,) + self.selected


        
