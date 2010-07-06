# Option Control Processors for our dialog.
# These are extensions to basic Control Processors that are linked with
# Outlook-Plugin options.


import win32gui, win32api, win32con, win32ui
import commctrl
import struct, array
from dlgutils import *
import xmlrpclib

import processors

verbose = 0 # set to 1 to see option values fetched and set.

# A ControlProcessor that is linked up with options.  These get a bit smarter.

class OptionControlProcessor(processors.ControlProcessor):
    def __init__(self, window, control_ids):
        processors.ControlProcessor.__init__(self, window, control_ids)

    def GetPopupHelpText(self, idFrom):
        doc = " ".join(self.option.doc().split())
        if self.option.default_value:
            doc += " (the default value is %s)" % self.option.default_value
        return doc

    # We override Init, and break it into 2 steps.
    def Init(self):
        self.UpdateControl_FromValue()

    def Done(self):
        self.UpdateValue_FromControl()
        return True

#    # Only sub-classes know how to update their controls from the value.
    def UpdateControl_FromValue(self):
        raise NotImplementedError
    def UpdateValue_FromControl(self):
        raise NotImplementedError

class ComboProcessor(OptionControlProcessor):
    def __init__(self, window, control_ids, func, args):
        self.func = func
        self.args = args
        OptionControlProcessor.__init__(self, window, control_ids)
    def OnCommand(self, wparam, lparam):
        code = win32api.HIWORD(wparam)
        if code == win32con.CBN_SELCHANGE:
            self.UpdateValue_FromControl()
    def Init(self):
        self.UpdateControl_FromValue()
    def UpdateControl_FromValue(self):
        pass
    def UpdateValue_FromControl(self):
        pass

class DBComboProcessor(ComboProcessor):
    def Init(self):
        self.UpdateControl_FromValue()

    def UpdateControl_FromValue(self):
        combo = self.GetControl()
        conn = self.func()
        list = conn.GetDBList()
        db = conn.getitem('_dbname')
        if list == -1:
            hinst = win32gui.dllhandle
            parent = self.window.hwnd
            dwStyle = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_TABSTOP | win32con.WS_BORDER | \
                        win32con.ES_AUTOHSCROLL | win32con.FF_ROMAN | win32con.FW_EXTRALIGHT

            hwndImg = win32gui.CreateWindow (
                                        "EDIT",
                                        db,
                                        dwStyle,
                                        67,80,180,20,
                                        parent,
                                        7000,
                                        0,
                                        None);
            self.active_control_id = 7000
            win32gui.ShowWindow(combo, False)
        else:
            try:
                txtbx = win32gui.GetDlgItem(self.window.hwnd, 7000)
                win32gui.DestroyWindow(txtbx)
            except Exception,e:
                pass
            win32gui.ShowWindow(combo, True)
            win32gui.SendMessage(combo, win32con.CB_RESETCONTENT,0, 0);
            for item in list:
                win32gui.SendMessage(combo, win32con.CB_ADDSTRING, 0, str(item))
            sel = win32gui.SendMessage(combo, win32con.CB_SELECTSTRING, 0, db)
            if sel == -1:
                win32gui.SendMessage(combo, win32con.CB_SETCURSEL, 0, 0)
            self.active_control_id = self.control_id

    def UpdateValue_FromControl(self):
        db = win32gui.GetDlgItemText(self.window.hwnd, self.active_control_id)
        conn = self.func()
        if conn.getitem('_dbname') != db:
            conn.setitem('_dbname', db)
            conn.setitem('_login', 'False')

class PartnersComboProcessor(ComboProcessor):
    def UpdateControl_FromValue(self):
        from manager import ustr
        combo = self.GetControl()
        conn = self.func()
        win32gui.SendMessage(combo, win32con.CB_RESETCONTENT,0, 0);
        id_list = {}
        list=[]
        try:
            list = conn.GetPartners()
            cnt=0
            for item in list:
                win32gui.SendMessage(combo, win32con.CB_ADDSTRING, 0, ustr(item[1]).encode('iso-8859-1'))
                id_list[cnt] = item[0]
                cnt+=1
            conn.setitem('partner_id_list', str(id_list))
            cnt = win32gui.SendMessage(combo, win32con.CB_GETCOUNT, 0, 0)
            win32gui.SendMessage(combo, win32con.CB_SETCURSEL, cnt-1, 0)
            return
        except xmlrpclib.Fault,e:
             msg = str(e.faultCode) or e.faultString or e.message or str(e)
        except Exception,e:
            msg = str(e)
        win32ui.MessageBox(str(e),"Partners",win32con.MB_ICONEXCLAMATION)
        win32gui.DestroyWindow(self.window.hwnd)

    def UpdateValue_FromControl(self):
        combo = self.GetControl()
        conn = self.func()
        sel = win32gui.SendMessage(combo, win32con.CB_GETCURSEL)
        conn.setitem('sel_id', sel)

class CSComboProcessor(ComboProcessor):
    def UpdateControl_FromValue(self):
        combo = self.GetControl()
        conn = self.func()
        if str(conn.getitem('_iscrm')) == 'False':
            win32gui.EnableWindow(combo, False)
            return
        try:
            list = conn.GetCSList()
            win32gui.SendMessage(combo, win32con.CB_RESETCONTENT,0, 0);
            for item in list:
                win32gui.SendMessage(combo, win32con.CB_ADDSTRING, 0, str(item))
            win32gui.SendMessage(combo, win32con.CB_SETCURSEL, 0, 0)
            return
        except xmlrpclib.Fault,e:
            win32ui.MessageBox(str(e.faultCode),"CRM Case",win32con.MB_ICONEXCLAMATION)
        except Exception,e:
            win32ui.MessageBox(str(e),"CRM Case",win32con.MB_ICONEXCLAMATION)

    def UpdateValue_FromControl(self):
        pass

class TextProcessor(OptionControlProcessor):
    def __init__(self, window, control_ids, func, args):
        self.func = func
        self.args = args
        OptionControlProcessor.__init__(self, window, control_ids)

    def UpdateControl_FromValue(self):
        args = (self,)+(self.window,) + self.args
        self.func(*args)

    def UpdateValue_FromControl(self):
        pass

class ListBoxProcessor(OptionControlProcessor):
    def __init__(self, window, control_ids, func, args):
        self.func = func
        self.args = args
        OptionControlProcessor.__init__(self, window, control_ids)

    def Init(self):
        args = (self,)+(self.window,) + self.args
        if not self.init_done:
            self.func(*args)

    def UpdateControl_FromValue(self):
        pass
    def UpdateValue_FromControl(self):
        pass

class GroupProcessor(OptionControlProcessor):
    def __init__(self, window, control_ids, func, args):
        self.func = func
        self.args = args
        OptionControlProcessor.__init__(self, window, control_ids)
    def Init(self):
        args = (self,)+(self.window,) + self.args
        self.func(*args)
    def UpdateControl_FromValue(self):
        pass
    def UpdateValue_FromControl(self):
        pass
