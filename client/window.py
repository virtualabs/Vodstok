#!/usr/bin/python

import pygtk
import os
import sys
import re
pygtk.require('2.0')
import gtk
from time import time
from downup.manager import DownUpManager
from core.exception import IncorrectParameterError
from core.helpers import formatSpeed

gtk.gdk.threads_init()

class MainManager:
    
    """
    Vodstok UI stream manager
    """
    
    def __init__(self, callback=None):
        self.m = DownUpManager.getInstance()
        self.m.registerListener(self)
        self.task = None
        self.kind = ''
        self.start = time()
        self.callback = callback

    def upload(self, filename):
        """
        Upload a file
        """
        try:
            task = self.m.upload(filename)
            sys.stdout.write('upload: %s\n'%task)
            sys.stdout.flush()
            self.m.startTask(task)
            return task
        except IncorrectParameterError:
            return None
        
    def download(self, filename,prefix=''):
        """
        Download a file
        """
        try:
            task = self.m.download(filename)
            sys.stdout.write('upload: %s\n'%task)
            sys.stdout.flush()
            self.m.startTask(task)
            return task
        except:
            return None

    def onTaskDone(self, task):
        """
        Task completed callback
        """
        sys.stdout.write('task done: %s\n'%task)
        sys.stdout.flush()
        if self.callback:
            self.callback.onTaskDone(task)

    def onTaskProgress(self, task, progress):
        """
        Task progress callback
        """
        if self.callback:
            self.callback.updateTask(task, progress)

    def onTaskCancel(self,task):
        """
        Task canceled callback (implemented but never called since we do not allow task cancelation)
        """
        sys.stdout.write('task canceled: %s\n'%task)
        sys.stdout.flush()
        return

    def onTaskError(self, task):
        """
        Task error callback.

        Stop everything if an error occured.
        """
        """
        if self.callback:
            self.callback.cancelTask(task)
        """
        sys.stdout.write('Task error !\n')
        sys.stdout.flush()
        
    def onTaskCreated(self, task):
        sys.stdout.write('Task created\n')
        sys.stdout.flush()
        return
        
    def onTaskStarted(self, task):
        sys.stdout.write('Task started\n')
        sys.stdout.flush()
        return

    def shutdown(self):
        self.m.shutdown()

class MainWindow(gtk.Window):
    
    
    class AskUrlDialog(gtk.Dialog):
        def __init__(self, parent):
            gtk.Dialog.__init__(self, "Download from URL", parent, gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
            self.set_size_request(300, 80)
            self.set_resizable(False)
            hbox = gtk.HBox(False)
            url_lbl = gtk.Label('URL:')
            self.url_entry = gtk.Entry()
            hbox.pack_start(url_lbl, False, padding = 5)
            hbox.pack_start(self.url_entry, True, padding = 5)
            self.vbox.add(hbox)
            self.show_all()
            
        def getUrl(self):
            return self.url_entry.get_text()
            
    
    def __init__(self):
        super(MainWindow, self).__init__()

        self.manager = MainManager(self)

        self.active_dl = []
        self.active_ul = []
        
        self.connect("destroy", self.onQuit)
        self.onCreate()
        self.set_size_request(600,300)
        self.show_all()
    
    def onCreate(self):
        """
        Create the main interface
        """
        
        # Window setup
        self.set_title('Vodstok v1.2.3')
        self.connect("destroy", gtk.main_quit)

        self.vbox = gtk.VBox(False, 1)
        self.add(self.vbox)
        self.createMenuBar()

        # Create treeview
        self.createUpTreeview()
        self.createDownTreeview()
        
        vbox1 = gtk.VBox(False)
        sw1 = gtk.ScrolledWindow()
        sw1.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw1.add(self.up_treeview)
        hbox_lbl = gtk.HBox(False)
        hbox_lbl.pack_start(gtk.image_new_from_stock(gtk.STOCK_GO_UP,gtk.ICON_SIZE_SMALL_TOOLBAR), False, False, 0)
        self.ul_lbl = gtk.Label('Uploads (%d)'%len(self.active_ul))
        hbox_lbl.pack_start(self.ul_lbl, False, True, 5)
        vbox1.pack_start(hbox_lbl, False, False, 0)
        vbox1.pack_start(sw1)

        vbox2 = gtk.VBox(False)
        sw2 = gtk.ScrolledWindow()
        sw2.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw2.add(self.down_treeview)
        hbox_lbl = gtk.HBox(False)
        hbox_lbl.pack_start(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN,gtk.ICON_SIZE_SMALL_TOOLBAR), False, False, 0)
        self.dl_lbl = gtk.Label('Downloads (%d)' % len(self.active_dl))
        hbox_lbl.pack_start(self.dl_lbl, False, True, 5)
        vbox2.pack_start(hbox_lbl, False, False, 0)
        vbox2.pack_start(sw2)

        # Create vertical panels
        self.panels = gtk.VPaned()
        self.panels.add1(vbox1)
        self.panels.add2(vbox2)
        self.panels.show()
        self.vbox.pack_start(self.panels)

    def refreshUi(self):
        self.dl_lbl.set_text('Downloads (%d)' % len(self.active_dl))
        self.ul_lbl.set_text('Uploads (%d)' % len(self.active_ul))


    def createUpTreeview(self):
        self.up_store = gtk.ListStore(str, str, int, str)
        self.up_treeview = gtk.TreeView(self.up_store)
        self.up_treeview.set_headers_visible(False)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Filename",cell, text=1)
        self.up_treeview.append_column(column)
        
        cell = gtk.CellRendererProgress()
        column = gtk.TreeViewColumn("Progress", cell, value=2)
        column.set_expand(True)
        self.up_treeview.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("ETA",cell,text=3)
        self.up_treeview.append_column(column)

    def createDownTreeview(self):
        self.down_store = gtk.ListStore(str, str, int, str)
        self.down_treeview = gtk.TreeView(self.down_store)
        self.down_treeview.set_headers_visible(False)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Filename",cell, text=1)
        self.down_treeview.append_column(column)
        
        cell = gtk.CellRendererProgress()
        column = gtk.TreeViewColumn("Progress", cell, value=2)
        column.set_expand(True)
        self.down_treeview.append_column(column)
        
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("ETA",cell,text=3)
        self.down_treeview.append_column(column)
        
    def createMenuBar(self):
        
        ui = '''
        <ui>
            <menubar name="MenuBar">
                <menu action="File">
                    <menuitem action="UP"/>
                    <menuitem action="DWN"/>
                    <menuitem action="QUIT"/>
                </menu>
                <menu action="SETUP">
                    <menuitem action="SERVERS"/>
                    <menuitem action="SETTINGS"/>
                </menu>
                <menu action="ABOUT">
                    <menuitem action="HELP"/>
                    <menuitem action="VERSION"/>
                </menu>
            </menubar>
        </ui>
        '''
        
        uimanager = gtk.UIManager()
        self.accels = uimanager.get_accel_group()
        self.add_accel_group(self.accels)
        self.actiongroup = gtk.ActionGroup('VodstokUI')
        self.actiongroup.add_actions([
            ('File', None, '_File'),
            ('UP', gtk.STOCK_GO_UP, 'Upload a file', '<Control>U', None, self.addUpload),
            ('DWN', gtk.STOCK_GO_DOWN, 'Download from URL','<Control>D', None, self.addDownload),
            ('QUIT',gtk.STOCK_QUIT, 'Quit vodstok','<Control>Q', None, self.onQuit),
            ('SETUP', None, '_Settings'),
            ('SERVERS', gtk.STOCK_NETWORK, 'Servers management', '<Control>S', None, self.onServersManagement),
            ('SETTINGS', gtk.STOCK_PREFERENCES, 'Preferences', '<Control>P', None, self.onPreferences),
            ('ABOUT', None,  '_About'),
            ('HELP', gtk.STOCK_HELP, 'Help', '<Control>H', None, self.onHelp),
            ('VERSION', gtk.STOCK_INFO, 'Version info', None, None, self.onVersion),
            
        ])
        uimanager.insert_action_group(self.actiongroup, 0)
        uimanager.add_ui_from_string(ui)
        self.menubar = uimanager.get_widget('/MenuBar')
        self.vbox.pack_start(self.menubar, False, True, 0)
        
    def addUpload(self, action):
        dialog = gtk.FileChooserDialog(
            "Open..",
            None,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        )
        dialog.set_default_response(gtk.RESPONSE_OK)
        
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)        
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            sys.stdout.write(filename)
            sys.stdout.flush()
            dialog.destroy()
            if filename:
                uid = self.manager.upload(filename)
                if uid:
                    self.refreshUi()
                    task = {
                        'uid':uid,
                        'filename':filename,
                        'progress':0,
                        'eta':' - ',
                    }
                    self.active_ul.append(task)
                    self.refreshUi()
                    self.up_store.append(
                        (
                            task['uid'],
                            os.path.basename(task['filename']),
                            task['progress'],
                            task['eta']
                        )
                    )
                else:
                    error_msg = gtk.MessageDialog(
                        self,
                        gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_CLOSE,
                        'Unable to read file !'
                    )
                    error_msg.run()
                    error_msg.destroy()
        else:
            dialog.destroy()
        
    def addDownload(self, action):
        d = self.AskUrlDialog(self)
        resp = d.run()
        if resp == gtk.RESPONSE_OK:
            url = d.getUrl()
            if (re.match('^(http|https)://([^\?]+)\?(.*)$', url) is not None):
                uid = self.manager.download(d.getUrl())
                task = {
                    'uid':uid,
                    'filename':' - ',
                    'progress':0,
                    'eta':' - ',
                }
                self.active_dl.append(task)
                self.refreshUi()
                self.down_store.append(
                    (
                        task['uid'],
                        task['filename'],
                        task['progress'],
                        task['eta'],
                    )
                )
            else:
                error_msg = gtk.MessageDialog(
                    self,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_CLOSE,
                    'Bad URL !'
                )
                error_msg.run()
                error_msg.destroy()               
        d.destroy()
        #self.refreshUi()

    def onTaskDone(self, task):
        gtk.gdk.threads_enter()
        for i in range(len(self.up_store)):
            if str(self.up_store[i][0])==str(task):
                self.up_store[i][2]=100
                self.up_store[i][3]=' - '
        for i in range(len(self.down_store)):
            if str(self.down_store[i][0])==str(task):
                self.down_store[i][2]=100
                self.down_store[i][3]=' - '
        gtk.gdk.threads_leave()

    def updateTask(self, task, progress):
        gtk.gdk.threads_enter()
        t = self.manager.m.getTask(task)
        for i in range(len(self.up_store)):
            if str(self.up_store[i][0])==str(task):
                self.up_store[i][2] = progress*100.0
                self.up_store[i][3] = formatSpeed(t.speed)
        for i in range(len(self.down_store)):
            if str(self.down_store[i][0])==str(task):
                self.down_store[i][1] = t.filename
                self.down_store[i][2] = progress*100.0
                self.down_store[i][3] = formatSpeed(t.speed)

        gtk.gdk.threads_leave()
 
    def onServersManagement(self, action):
        pass
        
    def onPreferences(self, action):
        pass
        
    def onHelp(self, action):
        pass
        
    def onVersion(self, action):
        pass

    def onQuit(self, action):
        self.manager.shutdown()
        gtk.main_quit()
        
        
if __name__ == '__main__':
    MainWindow()
    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()