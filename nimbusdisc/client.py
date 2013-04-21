import os
import sys
import getpass
import pyacd
import logging
from optparse import OptionParser

#------------------------------------------------------------
# setup logging
#------------------------------------------------------------
logger = logging.getLogger(__name__)

#------------------------------------------------------------
# exceptions
#------------------------------------------------------------
class NimbusException(Exception):
    pass

#------------------------------------------------------------
# nimbus client
#------------------------------------------------------------
class NimbusClient(object):
    ''' A simple wrapper around the pyacd client. The supported
    methods are:

    * list
    * create_dir
    * get_file
    * create_file
    * move
    * delete
    '''

    def __init__(self, session, options):
        ''' Initialize a new nimbus client

        :param session: The underlying session to nimbus
        :param options: The user supplied options
        '''
        self.session = session
        self.options = options

    def create_file(self, path, save):
        ''' Given a nimbus file path, upload the specified
        file to that path.

        :param path: The nimbus path to create a file at
        :param save: The local file to save to nimbus
        :returns: True if successful, False otherwise
        '''
        if path[0]  != '/': path = '/' + path
        if path[-1] != '/': path = path + '/'
        try:
            logger.debug("uploading file from(%s) to(%s)", save, path)
            dest = pyacd.api.get_info_by_path(path)
            if dest.Type == pyacd.types.FILE:
                logger.error("supplid path is not a directory %s", path)
                return False

            name = os.path.basename(save)
            with open(save, 'r') as handle:
                data = handle.read()
            logger.debug("creating file path(%s)", path)
            handle = pyacd.api.create_by_path(path, name)
            upload = pyacd.api.get_upload_url_by_id(handle.object_id, len(data))

            endpoint  = upload.http_request.end_point
            params    = upload.http_request.parameters
            store_key = upload_url.storage_key
            object_id = upload_url.object_id
            logger.debug("starting file upload(%s)", name)
            pyacd.api.upload(endpoint, params, name, data)
            logger.debug("finishing file upload(%s)", name)
            pyacd.api.complete_file_upload_by_id(object_id, store_key)
            return True
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("problem uploading file")
        return False

    def create_dir(self, path):
        ''' Given a nimbus file path, create a directory.

        :param path: The nimbus path to create a directory at
        :returns: True if successful, False otherwise
        '''
        if path[0] != '/': path = '/' + path
        parent, folder = os.path.split(path)
        try:
            logger.debug("creating directory at(%s)", path)
            pyacd.api.create_by_path(parent, folder, Type=pyacd.types.FOLDER)
            return True
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("directory already exists")
        return False

    def list(self, path):
        ''' Given a nimbus file path, list the files at
        that path.

        :param path: The nimbus path to lits the files at
        :returns: The listing of objects at that directory
        '''
        if path[0] != '/': path = '/' + path
        try:
            logger.debug("listing directory at(%s)", path)
            patho = pyacd.api.get_info_by_path(path)
            if patho.Type == pyacd.types.FILE:
                return [patho]
            return pyacd.api.list_by_id(patho.object_id).objects
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("directory already exists")
        return []

    def list_tree(self, root='/'):
        ''' List the entire cloud drive tree.

        :returns: {'path' -> file-object}
        '''
        tree  = {}
        queue = [root]
        while queue:
            for entry in self.list(queue.pop()):
                path = entry.path + entry.name
                tree[path] = entry
                if entry.Type == pyacd.types.FOLDER:
                    queue.append(path)
        return tree

    def get_file(self, path):
        ''' Given a nimbus file path, download it.

        :param path: The nimbus path to download
        :returns: The file data or None if error
        '''
        if path[0] != '/': path = '/' + path
        try:
            logger.debug("downloading file from(%s)", path)
            patho = pyacd.api.get_info_by_path(path)
            if patho.Type != pyacd.types.FILE:
                logger.error("supplid file to get is a directory %s", path)
                return False
            return pyacd.api.download_by_id(patho.object_id)
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("file not found on nimbus")
        return None

    def delete(self, path):
        ''' Given a nimbus file path, delete it.

        :param path: The nimbus path to delete.
        :returns: True if successful, False otherwise
        '''
        if path[0] != '/': path = '/' + path
        try:
            logger.debug("deleting file(%s)", path)
            patho = pyacd.api.get_info_by_path(path)
            if (patho.Type != pyacd.types.FILE) and (patho.Type != pyacd.types.FOLDER):
                logger.error("supplid file(%s) is a special entity %s", path, patho.Type)
                return False
            pyacd.api.recycle_bulk_by_id([patho.object_id])
            return True
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("file not found on nimbus")
        return False

    def move(self, source, dest):
        ''' Given a nimbus file path, download it.

        :param source: The path to move from
        :param dest: The path to move to
        :returns: True if successful, False otherwise
        '''
        parent, name = os.path.split(dest)
        try:
            logger.debug("moving file from(%s) to(%s)", source, dest)
            sourceo = pyacd.api.get_info_by_path(source)
            desto   = pyacd.api.get_info_by_path(parent)
            pyacd.api.move_by_id(sourceo.object_id, desto.object_id, name)
            return True
        except pyacd.PyAmazonCloudDriveApiException, ex:
            logger.exception("error with nimbus api")
        except pyacd.PyAmazonCloudDriveError, ex:
            logger.exception("error moving the specified file")
        return False

#------------------------------------------------------------
# local helper methods
#------------------------------------------------------------
def create_options():
    '''
    '''
    parser=OptionParser()
    parser.add_option(
        "--domain", dest="domain", action="store", default="www.amazon.com",
        help="domain of Amazon [default: %default]")
    parser.add_option(
        "-e", dest="email", action="store", default=None,
        help="email address for Amazon")
    parser.add_option(
        "-p", dest="password", action="store", default=None,
        help="password for Amazon")
    parser.add_option(
        "-s", dest="session", action="store", default=None, metavar="FILE",
        help="save/load login session to/from FILE") 
    parser.add_option(
        "-d",dest="debug",action="store_true",default=False,
        help="show verbose debug messages")
    opts, args = parser.parse_args(sys.argv[1:])
    return opts

def create_session(opts):
    ''' Given a collection of options, attempt to recreate the
    pyacd session.

    :param opts: The authentication options
    :returns: An authenticated session
    '''
    session = None
    # attempt to load a previous session
    if opts.session:
        try:
            logger.debug("loading session from(%s)", opts.sesssion)
            session = pyacd.Session.load_from_file(opts.session)
        except: session = pyacd.Session()

    # attempt to login with the supplied session information
    try:
        if opts.email and opts.password and session:
            logger.debug("creating session with email(%s)", opts.email)
            session = pyacd.login(opts.email, opts.password, session=session)
        elif opts.email and opts.password:
            logger.debug("creating session with email(%s)", opts.email)
            session = pyacd.login(opts.email, opts.password)
        else:
            logger.debug("creating session with session(%s)", opts.session)
            session = pyacd.login(session=session)
    except Exception, ex:
        logger.exception("error creating user session")
        session = None

    # check if we failed to login
    if not session:
        logger.error("unable to create session with email(%s)", opts.email)
        raise NimbusException("unable to create user session")

    # save current session to file
    if not opts.session:
        opts.session = os.path.expanduser("~/.nimbus")
    logger.debug("saving session file to(%s)", opts.session)
    session.save_to_file(opts.session)

    # debug print some useful information about the session
    logger.debug("session information: %s", session)
    #if opts.debug: session.print_debug()
    return session

def validate_options(opts):
    ''' Given a collection of parsed options, validate
    that they are correct and apply global settings.

    :param opts: The options to validate
    :returns: True if valid, false otherwise
    '''
    pyacd.set_amazon_domain(opts.domain)

    # update options of authentication
    if opts.email:
        if not opts.password:
            opts.password = getpass.getpass()

    # check if we need debug logging
    if opts.debug:
        logging.basicConfig()
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)

    # check options of authentication
    if (opts.email and opts.password) or opts.session:
        return True
    raise NimbusException("missing neccessary session options")

def create_client():
    ''' A helper method to create a nimbus client

    :returns: An initialized nimbus client
    '''
    options = create_options()
    validate_options(options)
    session = create_session(options)
    return NimbusClient(session, options)

base   = "/tmp/testing"
client = create_client()
result = client.list_tree()
for path, obj in result.items():
    if obj.Type == pyacd.types.FOLDER:
        path = os.path.join(base, path[1:])
        os.mkdir(path)
    elif obj.Type == pyacd.types.FILE:
        data = client.get_file(path)
        path = os.path.join(base, path[1:])
        with open(path, 'w') as handle:
            handle.write(data)
        

