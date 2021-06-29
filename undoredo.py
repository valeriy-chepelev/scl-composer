import tempfile
import os
import lxml.etree as ET
import json
import shutil

class UndoRedo():
    '''Implements an undo - redo file stack
    with temporary files for undo/redo retrieving.
    History is a list of tempfiles.
    working schema:
    1) change added
    0 1 2 3 4 5 6 7 8 9 <-new change append
                      ^
                     pos=high(history)
          
    2) undo/redo
    0 1 2 3 4 5 6 7 8 9 ->out data from pos
                ^
        undo<- pos ->redo
          
    3) change added after undo
    0 1 2 3 4 5 6 <- del items pos to high, new change append
                ^
               pos
    '''    
    def __init__(self, file, limit = 100):
        self.history = list()
        self.limit = limit
        self.pos = 0
        self.push(file)

    def __del__(self):
        for item in self.history:
            os.remove(item[1])
            os.remove(item[1] + '.et')

    def can_undo(self):
        return self.pos

    def can_redo(self):
        return len(self.history) - self.pos -1

    def clear(self, file):
        for item in self.history:
            os.remove(item[1])
            os.remove(item[1] + '.et')
        self.history = list()
        self.pos = 0
        self.push(file)

    def push(self, file, op_before = None, op_after = None):
        #delete redo stack
        if len(self.history) - self.pos > 1 : #like can_redo, but at init len(h)=0
            for item in self.history[self.pos+1:]:
                os.remove(item[1])
                os.remove(item[1] + '.et')
            del self.history[self.pos+1:]
        #limiting
        if len(self.history) > self.limit:
            for item in self.history[:len(self.history) - self.limit]:
                os.remove(item[1])
                os.remove(item[1] + '.et')
            del self.history[:len(self.history) - self.limit]
        #append file
        self.history.append(tempfile.mkstemp(prefix = 'doda', text=True))
        os.close(self.history[self.pos][0])
        self.pos = len(self.history) - 1
        #save 'after' options
        op_j = json.dumps(op_after, separators=(',', ':'))
        with open(self.history[self.pos][1], mode = 'wt') as fd:
            fd.write(op_j)
        #save 'before' options
        if self.pos:
            op_j = json.dumps(op_before, separators=(',', ':'))
            with open(self.history[self.pos-1][1], mode = 'wt') as fd:
                fd.write(op_j)
        #copy data file
        shutil.copyfile(file, self.history[self.pos][1]+'.et')

    def undo(self):
        if self.can_undo: self.pos -= 1
        options = json.load(open(self.history[self.pos][1]))
        return self.history[self.pos][1]+'.et', options

    def redo(self):
        if self.can_redo: self.pos += 1
        options = json.load(open(self.history[self.pos][1]))
        return self.history[self.pos][1]+'.et', options

def main():
    print('tests')
    ns = {'61850': 'http://www.iec.ch/61850/2003/SCL',
          'NSD': 'http://www.iec.ch/61850/2016/NSD',
          'efsk': 'http://www.fsk-ees.ru/61850/2020',
          'emt': 'http://www.mtrele.ru/npp/2021'}
    nsURI = '{%s}' % (ns['61850'])
    nsMap = {None : ns['61850']}
    root = ET.Element(nsURI+'DataTypeTemplates', nsmap = nsMap)
    ur = UndoRedo(root)
    assert not ur.can_undo()
    assert not ur.can_redo()
    print(ur.history, ur.pos)
    print(ur.push(root))
    print(ur.push(root, options = {'op1':1, 'op2':2}))
    print(ur.push(root))
    
    assert ur.can_undo()
    assert not ur.can_redo()
    op, val = ur.undo()
    print(type(op))
    print(op, val)
    assert ur.can_undo()
    assert ur.can_redo()
    print(ur.undo())
    print(ur.undo())
    assert not ur.can_undo()
    assert ur.can_redo()
    print(ur.redo())
    print(ur.push(root))
    assert not ur.can_redo()
    print(ur.history, ur.pos)
    print('clr and repeat')
    ur.clear(root)
    assert not ur.can_undo()
    assert not ur.can_redo()
    print(ur.history, ur.pos)
    print(ur.push(root))
    print(ur.push(root))
    print(ur.push(root))
    
    assert ur.can_undo()
    assert not ur.can_redo()
    print(ur.undo())
    assert ur.can_undo()
    assert ur.can_redo()
    print(ur.undo())
    print(ur.undo())
    assert not ur.can_undo()
    assert ur.can_redo()
    print(ur.redo())
    print(ur.push(root))
    assert not ur.can_redo()
    print(ur.history, ur.pos)
    print('check limit')
    ur.clear(root)
    ur.limit = 5
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    print(len(ur.history), ur.history, ur.pos)
    ur.push(root)
    
    
        
if __name__ == '__main__':
    main()

