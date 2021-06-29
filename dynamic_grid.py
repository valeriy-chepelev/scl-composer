from tkinter import *
import tkinter.ttk as ttk

import resources

class Do_images():
    def __init__(self):
        self.do_ins = PhotoImage(data=resources.ICO_DO_INS)
        self.do_up = PhotoImage(data=resources.ICO_DO_UP)
        self.do_dn = PhotoImage(data=resources.ICO_DO_DN)
        self.do_dup = PhotoImage(data=resources.ICO_DO_DUP)
        self.do_del = PhotoImage(data=resources.ICO_DO_DEL)

icons = None


class DynamicGrid(LabelFrame):
    def __init__(self, *args, **kwargs):
        self.with_ctrl = 0
        if 'controls' in kwargs.keys(): self.with_ctrl = kwargs.pop('controls')
        LabelFrame.__init__(self, *args, **kwargs)
        self.caption_text = kwargs['text'] if 'text' in kwargs.keys() else ''
        #widgets
        if self.with_ctrl == 1:
            global icons
            if icons is None: icons = Do_images()
            ctrl_frame = Frame(master = self)
            # buttons
            btn_frame = Frame(master = ctrl_frame)
            self._b_dup = Button(master = btn_frame, image = icons.do_dup, relief = 'flat',
                                 cursor = 'hand2', takefocus = 0,
                                 state = DISABLED, command = self._dup_handler)
            self._b_dup.grid(column = 0, row = 0, stick="nsew", padx = (3,0))
            self._b_del = Button(master = btn_frame, image = icons.do_del, relief = 'flat',
                                 cursor = 'hand2', takefocus = 0,
                                 state = DISABLED, command = self._del_handler)
            self._b_del.grid(column = 1, row = 0, stick="nsew")
            self._b_up = Button(master = btn_frame, image = icons.do_up, relief = 'flat',
                                cursor = 'hand2', takefocus = 0,
                                state = DISABLED, command = self._up_handler)
            self._b_up.grid(column = 2, row = 0, stick="nsew")
            self._b_dn = Button(master = btn_frame, image = icons.do_dn, relief = 'flat',
                                cursor = 'hand2', takefocus = 0,
                                state = DISABLED, command = self._dn_handler)
            self._b_dn.grid(column = 3, row = 0, stick="nsew")
            btn_frame.grid(column = 0, row = 0, columnspan = 6, stick="nsw")
            # labels
            Label(master = ctrl_frame, bg = 'white', text = 'DO name', width = 15, state = DISABLED).\
                         grid(column = 0, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'CDC', width = 16, state = DISABLED).\
                         grid(column = 1, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'Type', width = 16, state = DISABLED).\
                         grid(column = 2, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'Process', width = 16, state = DISABLED).\
                         grid(column = 3, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'Namespace', width = 18, state = DISABLED).\
                         grid(column = 4, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'PresCond', width = 9, state = DISABLED).\
                         grid(column = 5, row = 2, stick="nsew")
            ttk.Separator(master = ctrl_frame, orient = HORIZONTAL)\
                                 .grid(column = 0, row = 1, columnspan = 6, stick = 'nsew', pady = 0)
            ttk.Separator(master = ctrl_frame, orient = HORIZONTAL)\
                                 .grid(column = 0, row = 3, columnspan = 6, stick = 'nsew', pady = (0,3))

            #placement
            ctrl_frame.pack(side=TOP, fill=X)

        if self.with_ctrl == 2:
            ctrl_frame = Frame(master = self)
            # labels
            Label(master = ctrl_frame, bg = 'white', text = 'fc', width = 3, state = DISABLED).\
                         grid(column = 0, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'data attribute', width = 20, state = DISABLED).\
                         grid(column = 1, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'valKind', width = 8, state = DISABLED).\
                         grid(column = 2, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'value', width = 15, state = DISABLED).\
                         grid(column = 3, row = 2, stick="nsew")
            Label(master = ctrl_frame, bg = 'white', text = 'descriptions', width = 45, state = DISABLED).\
                         grid(column = 4, row = 2, stick="nsew")
            ttk.Separator(master = ctrl_frame, orient = HORIZONTAL)\
                                 .grid(column = 0, row = 1, columnspan = 5, stick = 'nsew', pady = 0)
            ttk.Separator(master = ctrl_frame, orient = HORIZONTAL)\
                                 .grid(column = 0, row = 3, columnspan = 5, stick = 'nsew', pady = (0,3))
            #placement
            ctrl_frame.pack(side=TOP, fill=X)
            
            
        vsb = Scrollbar(self, orient=VERTICAL)
        vsb.pack(side=RIGHT, fill=Y)
        self.text = Text(self, bg = 'SystemButtonFace', selectbackground = 'SystemButtonFace',
                         wrap='char', borderwidth=0, highlightthickness=0,
                         exportselection=0, takefocus=0,
                         cursor = 'arrow',
                         yscrollcommand = vsb.set,
                         state=DISABLED)
        vsb['command'] = self.text.yview        
        self.text.pack(side = LEFT, fill=BOTH, expand=True)
        #vars
        self.data_object = None
        self.focused_frame = None
        self._int_conf = False

    def configure(self, **kw):
        if not self._int_conf:
            if 'text' in kw.keys():
                self.caption_text = kw['text']
                if len(self.text.window_names()):
                    kw.update({'text': '[%s] %s' % (len(self.text.window_names()),
                                                    self.caption_text)})
        self._int_conf = False
        super().configure(kw)


    def _update_caption(self):
        self._int_conf = True
        self.configure(text = '[%s] %s' % (len(self.text.window_names()),
                                           self.caption_text))

    def add_frame(self, frame, pos = END, cr=False):
        self.text.configure(state=NORMAL)
        self.text.window_create(pos, window=frame)
        if cr: self.text.insert(pos, '\n')
        # bindings
        frame.bind('<FocusIn>',self._focus_frame)
        frame.bind('<<BeforeChange>>', lambda event: self.event_generate('<<BeforeChange>>'))
        frame.bind('<<OnChange>>', lambda event: self.event_generate('<<OnChange>>'))
        
        self.text.configure(state=DISABLED)
        self._update_caption()

    def finalize(self):
        self.text.configure(state=NORMAL)
        self.text.insert(END,'\n\n\n')
        self.text.configure(state=DISABLED)

    def clear(self):
        self.text.configure(state=NORMAL)
        self.text.delete('1.0',END)
        self.text.configure(state=DISABLED)
        if self.with_ctrl == 1:
            self._b_dup.configure(state = DISABLED)
            self._b_del.configure(state = DISABLED)
            self._b_up.configure(state = DISABLED)
            self._b_dn.configure(state = DISABLED)
        self._int_conf = True
        self.data_object = None
        self.focused_frame = None
        self.configure(text = self.caption_text)

    def _focus_frame(self, event):
        self.focused_frame = event.widget
        self.data_object = event.widget.data_object
        if self.with_ctrl == 1:
            self._b_dup.configure(state = NORMAL)
            self._b_del.configure(state = NORMAL)
            self._b_up.configure(state = NORMAL)
            self._b_dn.configure(state = NORMAL)
        self.event_generate('<<FrameFocus>>')

    def _dup_handler(self):
        self.event_generate('<<BeforeChange>>')
        w, pos = self.focused_frame.get_new()
        self.add_frame(w, '1.' + str(pos))
        if len(self.text.window_names())-1 == pos:
            self.text.see(END) # fix for scroll to last position
        else: self.text.see('1.' + str(pos+1))
        w.focus_set()
        self.event_generate('<<OnChange>>')

    def _del_handler(self):
        if not self.focused_frame.exec_del():
            self.bell()
            return
        self.text.configure(state=NORMAL)
        self.text.delete(self.focused_frame)
        self.text.configure(state=DISABLED)
        self._update_caption()
        self.data_object = None
        self.focused_frame = None
        if self.with_ctrl == 1:
            self._b_dup.configure(state = DISABLED)
            self._b_del.configure(state = DISABLED)
            self._b_up.configure(state = DISABLED)
            self._b_dn.configure(state = DISABLED)
        self.event_generate('<<FrameFocus>>')

    def _up_handler(self):
        if not self.focused_frame.exec_up():
            self.bell()
            return
        pos = '1.' + str(int(self.text.index(self.focused_frame).split('.')[1]) - 1)
        w = self.focused_frame.get_clone()
        self.add_frame(w, pos)
        self.text.configure(state=NORMAL)
        self.text.delete(self.focused_frame)
        self.text.configure(state=DISABLED)
        self.text.see(pos)
        w.focus_set()

    def _dn_handler(self):
        if not self.focused_frame.exec_dn():
            self.bell()
            return
        pos = int(self.text.index(self.focused_frame).split('.')[1]) + 2
        w = self.focused_frame.get_clone()
        self.add_frame(w, '1.' + str(pos))
        self.text.configure(state=NORMAL)
        self.text.delete(self.focused_frame)
        self.text.configure(state=DISABLED)
        if len(self.text.window_names()) == pos:
            self.text.see(END) # fix for scroll to last position
        else: self.text.see('1.' + str(pos+1))
        w.focus_set()
    
        
