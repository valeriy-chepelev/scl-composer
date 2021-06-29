from tkinter import *
import tkinter.ttk as ttk

class ScrolledTree(ttk.Treeview):
    def __init__(self, master=None, xscroll=True, **kw):
        self.frame = Frame(master)

        self.vbar = Scrollbar(self.frame, orient=VERTICAL)
        kw.update({'yscrollcommand': self.vbar.set})
        self.vbar.pack(side=RIGHT, fill=Y)
        self.vbar['command'] = self.yview        

        if xscroll:
            self.hbar = Scrollbar(self.frame, orient=HORIZONTAL)
            kw.update({'xscrollcommand': self.hbar.set})
            self.hbar.pack(side=BOTTOM, fill=X)
            self.hbar['command'] = self.xview
        
        ttk.Treeview.__init__(self, self.frame, **kw)
        self.pack(side=LEFT, fill=BOTH, expand=True)
        
        tree_meths = vars(ttk.Treeview).keys()
        methods = vars(Pack).keys() | vars(Grid).keys() | vars(Place).keys()
        methods = methods.difference(tree_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)
