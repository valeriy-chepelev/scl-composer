import tkinter as tk
import tkinter.ttk as ttk
import logging

logger = None

class LoggingHandlerFrame(tk.Frame):

    class Handler(logging.Handler):

        def __init__(self, widget):
            logging.Handler.__init__(self)
            self.setFormatter(logging.Formatter("%(asctime)s: %(message)s",
                                                datefmt='%Y-%m-%d %H:%M:%S'))
            self.widget = widget
            self.widget.config(state=tk.DISABLED)
            self.widget.tag_config("INFO", foreground="black")
            self.widget.tag_config("DEBUG", foreground="grey")
            self.widget.tag_config("WARNING", foreground="saddle brown")
            self.widget.tag_config("ERROR", foreground="red")
            self.widget.tag_config("CRITICAL", foreground="red", underline=1)

        def emit(self, record):
            self.widget.config(state=tk.NORMAL)
            self.widget.insert(tk.END, self.format(record) + "\n", record.levelname)
            self.widget.see(tk.END)
            self.widget.config(state=tk.DISABLED)
            if record.levelname in ('ERROR', 'CRITICAL'):
                self.widget.event_generate('<<LogError>>')
            self.widget.update()

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        vsb = tk.Scrollbar(self)
        vsb.pack(side = tk.RIGHT, fill = tk.Y)
        text = tk.Text(self, yscrollcommand=vsb.set, wrap=tk.WORD)
        text.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
        vsb.config(command=text.yview)
        self.logging_handler = LoggingHandlerFrame.Handler(text)


class LoggerDialog:
    def __init__(self, parent):
        self.parent = parent
        #form
        self.top = tk.Toplevel(parent)
        self.top.title('Messages')
        self.top.minsize(600, 300)
        self.top.geometry('600x400+%s+%s' % (parent.winfo_rootx()+50 , parent.winfo_rooty()+50))
        self.top.protocol('WM_DELETE_WINDOW', self.close)
        
        #widgets
        frame = LoggingHandlerFrame(self.top)
        frame.pack(fill = tk.BOTH, expand = True, padx = 5, pady = 5)
        self.logging_handler = frame.logging_handler

        #signalling
        self.log_status = 0
        self.top.bind('<<LogError>>', self.mark)

    def mark(self, event):
        self.top.bell()
        self.log_status = 1

    def show(self):
        self.log_status = 0
        self.top.deiconify()

    def close(self):
        self.log_status = 0
        self.top.withdraw()


        
