import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ------------------------------------------------------------
# initialize logging
# ------------------------------------------------------------
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# ------------------------------------------------------------
# drive event handler
# ------------------------------------------------------------
class LoggingEventHandler(FileSystemEventHandler):
  '''Logs all the events captured.'''

  def on_moved(self, event):
    super(LoggingEventHandler, self).on_moved(event)

    what = 'directory' if event.is_directory else 'file'
    logging.info("Moved %s: from %s to %s", what, event.src_path,
                 event.dest_path)

  def on_created(self, event):
    super(LoggingEventHandler, self).on_created(event)

    what = 'directory' if event.is_directory else 'file'
    logging.info("Created %s: %s", what, event.src_path)

  def on_deleted(self, event):
    super(LoggingEventHandler, self).on_deleted(event)

    what = 'directory' if event.is_directory else 'file'
    logging.info("Deleted %s: %s", what, event.src_path)

  def on_modified(self, event):
    super(LoggingEventHandler, self).on_modified(event)

    what = 'directory' if event.is_directory else 'file'
    logging.info("Modified %s: %s", what, event.src_path)

def create_watcher(options):
    ''' A helper method to start the file system watcher
    daemon.
    '''
    handler  = LoggingEventHandler()
    observer = Observer()
    observer.schedule(handler, path=options.path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
