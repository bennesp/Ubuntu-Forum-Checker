from phpbb import phpBB
import gtk, gobject
import time
import threading
import pickle
import webbrowser
import subprocess

class UbuntuForumChecker:
  def __init__(self):
    self.icon = gtk.StatusIcon()
    self.icon.set_from_file("data/images/refresh.png")
    self.icon.set_tooltip("Authenticating...")
    self.icon.set_visible(True)
   
    self.menu = gtk.Menu()
    exit = gtk.MenuItem("Exit")
    exit.connect("activate", gtk.main_quit)
    self.menu.append(exit)
    self.menu.show_all()
    self.icon.connect("activate", self.show_menu)

    self.settings_filename = "settings"
    self.user_id="1"
    self.usr=None
    self.pwd=None
    self.stop=False
    self.submenus=[]

  def auth(self):
    #self.log("In auth")
    while self.usr==None and self.pwd==None:
      #self.log("Waiting in auth...")
      time.sleep(.1)
    self.p=phpBB("http://forum.ubuntu-it.org/")
    try:
      self.user_id=self.p.login(self.usr, self.pwd)
    except:
      pass
    if(self.user_id=="1"):
      self.log("Something went wrong during authentication. Please, check user and password")
      self.show_settings(error="User or Password Wrong")
    else:
      self.log("Authenticated with user n."+self.user_id)

  def load(self):
    try:
      self.usr, self.pwd = pickle.Unpickler(file(self.settings_filename, "r")).load()
      return True
    except:
      return False

  def save(self, widget=None):
    #self.log("In save")
    self.usr=self.ue.get_text()
    self.pwd=self.pe.get_text()
    pickle.Pickler(file(self.settings_filename, "w"), pickle.HIGHEST_PROTOCOL).dump((self.usr, self.pwd))
    self.settings.destroy()

  def cancel(self, widget=None, event=None):
    gtk.main_quit()

  def show_settings(self, error=None):
    #self.log("In show_settings")
    self.settings = gtk.Window()
    self.settings.set_title("Ubuntu Forum Checker Settings")
    self.settings.connect("delete-event", self.cancel)
    container = gtk.HBox()
    vbox1 = gtk.VBox()
    vbox2 = gtk.VBox()
    vbox3 = gtk.VBox()
    hbox1 = gtk.HBox()
    hbox2 = gtk.HBox()
    ul = gtk.Label("Username: ")
    pl = gtk.Label("Password: ")
    self.ue = gtk.Entry()
    self.pe = gtk.Entry()
    self.pe.set_visibility(False)
    b1 = gtk.Button("Ok")
    b2 = gtk.Button("Cancel")

    b1.connect("clicked", self.save)
    b2.connect("clicked", self.cancel)

    if(error!=None):
      l = gtk.Label()
      l.set_markup("<span color='red'>"+error+"</span>")
      vbox1.pack_start(l)

    vbox2.pack_start(ul)
    vbox2.pack_start(pl)
    vbox3.pack_start(self.ue)
    vbox3.pack_start(self.pe)
    
    hbox2.pack_start(b1)
    hbox2.pack_start(b2)

    hbox1.pack_start(vbox2)
    hbox1.pack_start(vbox3)

    vbox1.pack_start(hbox1)
    vbox1.pack_start(hbox2)
    container.pack_start(vbox1)
    self.settings.add(container)
    self.settings.show_all()
    #self.log("Out of show_settings")

  def show_menu(self, widget):
    self.menu.popup(None, None, None, 0, 0)

  def log(self, s):
    print "[Thread "+str(threading.current_thread().name)+"]["+time.strftime("%a %b %d %H:%M:%S %Y")+"] "+s

  def click_topic(self, widget):
    webbrowser.open(widget.get_label())
    self.submenus.remove(widget.get_label())
    self.menu.remove(widget)
    if len(self.menu.get_children())==1:
      self.icon.set_from_file("data/images/ok.png")

  def update_topics(self, topics):
    #self.log("In update_topics")
    for topic in topics[-5:]:
      if(self.p.retTopic(topic) in self.submenus):
        continue
      try:
        subprocess.call(["mplayer", "data/sounds/notif.mp3"])
      except OSError: 
        # mplayer not installed. You'll not hear sounds.
        pass
      mi = gtk.MenuItem(self.p.retTopic(topic))
      mi.connect("activate", self.click_topic)
      self.submenus.append(self.p.retTopic(topic))
      self.menu.prepend(mi)
      self.menu.show_all()

  def check(self):
    #self.log("In check")
    while self.stop is False:
      while(self.user_id=="1"):
        #self.log("Waiting in check...")
        time.sleep(.1)
      r=0
      try:
        gobject.idle_add(self.icon.set_from_file, "data/images/refresh.png")
        list_topic=self.p.getOwnTopics(100)
      except AttributeError, ex:
        self.log("Exception: "+str(ex))
        break
      except Exception, ex:
        self.log("Exception occurred. Retrying in 10 seconds... ("+str(ex)+")")
        time.sleep(10)
        continue
      unread_topics=[]
      for topic in list_topic:
        if 'view' in topic and topic['view']=="unread":
          r+=1
          unread_topics.append(topic)
      if r>0:
        self.log("There is/are "+str(r)+" thread/s to be read")
        gobject.idle_add(self.icon.set_from_file, "data/images/new.png")
        if r==1: gobject.idle_add(self.icon.set_tooltip, "There is a thread to be read")
        else: gobject.idle_add(self.icon.set_tooltip, "There are " + r + " threads to be read")
        gobject.idle_add(self.update_topics, unread_topics)
      else:
        self.log("All threads read")
        gobject.idle_add(self.icon.set_from_file, "data/images/ok.png")
        gobject.idle_add(self.icon.set_tooltip, "All threads read")
      time.sleep(60)

  def main(self):
    if(self.load()==False):
      self.show_settings()
    t1=threading.Thread(target=self.auth)
    t2=threading.Thread(target=self.check)
    t1.start()
    t2.start()

if(__name__=="__main__"):
  gtk.gdk.threads_init()
  u=UbuntuForumChecker()
  u.main()
  gtk.main()
  u.stop = True
  print "Application terminated"
