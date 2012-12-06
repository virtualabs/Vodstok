#!/usr/bin/python

import gtk,sys,gobject
from time import time
from downup.manager import DownUpManager

gobject.threads_init()

class MainManager:
    
    """
    Vodstok UI stream manager
    
    This class implements our UI upload/download operations.
    This is a proxy to DownUpManager, with some UI interactions
    added.
    """
    
    def __init__(self):
        self.m = DownUpManager()
        self.m.registerListener(self)
        self.task = None
        self.kind = ''
        self.start = time()

    def __getattr__(self, attr):
        """
        Proxy implementation
        
        Every attribute not defined in this class but defined
        in the DownUpManager will be forwarded to its single
        instance.
        """
        if hasattr(self.m, attr):
            return getattr(self.m, attr)
        else:
            raise AttributeError()
            
    def onTaskDone(self, task):
        """
        Task completed callback
        """
        pass

    def onTaskProgress(self, task, progress):
        """
        Task progress callback
        """
        pass

    def onTaskCancel(self,task):
        """
        Task canceled callback (implemented but never called since we do not allow task cancelation)
        """
        return

    def onTaskError(self, task):
        """
        Task error callback.

        Stop everything if an error occured.
        """
        pass
        
    def onTaskCreated(self, task):
        return
        
    def onTaskStarted(self, task):
        return

class MainWindow(gtk.Window):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.active_dl = 0
        self.active_ul = 0
        
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
        self.ul_lbl = gtk.Label('Uploads (%d)'%self.active_ul)
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
        self.dl_lbl = gtk.Label('Downloads (%d)' % self.active_dl)
        hbox_lbl.pack_start(self.dl_lbl, False, True, 5)
        vbox2.pack_start(hbox_lbl, False, False, 0)
        vbox2.pack_start(sw2)

        # Create vertical panels
        self.panels = gtk.VPaned()
        self.panels.add1(vbox1)
        self.panels.add2(vbox2)
        self.vbox.pack_start(self.panels)

    def refreshNbDl(self):
        self.dl_lbl.set_text('Downloads (%d)' % self.active_dl)

    def refreshNbUl(self):
        self.ul_lbl.set_text('Uploads (%d)' % self.active_ul)

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
        self.active_ul += 1
        self.refreshNbUl()
        self.up_store.append(('','Test.exe',20,'10 min'))
        
    def addDownload(self, action):
        self.active_dl += 1
        self.refreshNbDl()
        self.down_store.append(('','Test.exe',20,'10 min'))
    
    def onServersManagement(self, action):
        pass
        
    def onPreferences(self, action):
        pass
        
    def onHelp(self, action):
        pass
        
    def onVersion(self, action):
        pass

    def onQuit(self, action):
        task = self.manager.m.getTask(self.up_store[0][0])
        sys.stdout.write('Task progress: %0.2f\n'%task.progress)
        gtk.main_quit()
        
        
if __name__ == '__main__':
    MainWindow()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()