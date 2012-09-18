#-*- coding:utf8 -*-
#!/usr/bin/env python


########################################################################
#author:liutaihua
#email: defage@gmail.com
#
#########################################################################

import string
import re
import os
import sys
import syslog
import time
import types
import logging
import threading, Queue
from threading import Thread
import tarfile
import statvfs
from daemoned import Daemon
from mail import *
from readconf import *





threshold = 8 + avail
ISOTIMEFORMAT='%Y-%m-%d-%H:%M'
re_word4exclude = re.compile("lib.*|dev|media|etc|var|proc|selinux|lost\+found|sys|srv|cdrom|run|bin|sbin|boot|share|include|man|kernel|libexec|git")
logger = logging.getLogger("/var/log/cldisky.log")



'''work thread pool'''
# working thread  
class Worker(Thread):  
    worker_count = 0  
    def __init__( self, workQueue, resultQueue, timeout = 0, **kwds):  
        Thread.__init__( self, **kwds )  
        self.id = Worker.worker_count  
        Worker.worker_count += 1  
        self.setDaemon( True )  
        self.workQueue = workQueue  
        self.resultQueue = resultQueue  
        self.timeout = timeout  
  
    def run( self ):  
        ''' the get-some-work, do-some-work main loop of worker threads '''  
        while True:  
            try:  
                callable, args, kwds = self.workQueue.get(timeout=self.timeout)  
                res = callable(*args, **kwds)  
                #print "worker[%2d]: %s" % (self.id, str(res) )  
                self.resultQueue.put( res )  
            except Queue.Empty:  
                break  
            #except :  
                #print 'worker[%2d]' % self.id, sys.exc_info()[:2]  
            #    pass
                  
class WorkerManager:  
    def __init__( self, num_of_workers=10, timeout = 0):  
        self.workQueue = Queue.Queue()  
        self.resultQueue = Queue.Queue()  
        self.workers = []  
        self.timeout = timeout  
        self._recruitThreads( num_of_workers )  
  
    def _recruitThreads( self, num_of_workers ):  
        for i in range( num_of_workers ):  
            worker = Worker( self.workQueue, self.resultQueue, self.timeout )  
            self.workers.append(worker)  
  
    def start(self):  
        for worker in self.workers:  
            worker.start()  
  
    def wait_for_complete( self):  
        # ...then, wait for each of them to terminate:  
        while len(self.workers):  
            worker = self.workers.pop()  
            worker.join( )  
            if worker.isAlive() and not self.workQueue.empty():  
                self.workers.append( worker )  
        print "All jobs are are completed."  
  
    def add_job( self, callable, *args, **kwds ):  
        self.workQueue.put( (callable, args, kwds) )  
  
    def get_result( self, *args, **kwds ):  
        return self.resultQueue.get( *args, **kwds )


def IsTxtFile(file_list, blocksize = 512):
    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    for file in file_list:
        if filter(lambda x:file.endswith(x), [".tar.gz",".gz",".tar",".tar.bz2"]):
            try:
                tar = tarfile.TarFile.open(file)
            except Exception,e:
                #txtfile_list.append(file)
                #syslog.syslog(e)
                logger.debug("handle IsTxtFile func:%s"%e)
                continue
            tarFileList = tar.getnames()
            allTarFile_num = len(tarFileList)
            tar_text_file_num = 0

            for f in tarFileList:
                try:
                    _type = type(tar.extractfile(f))
                except Exception,e:
                   continue
                if _type is types.NoneType: continue

                data = tar.extractfile(f).read(blocksize)
                if "\0" in data:
                    continue
                if not data:  # Empty files are considered text
                    tar_text_file_num += 1
                    continue

                # Get the non-text characters (maps a character to itself then
                # use the 'remove' option to get rid of the text characters.)
                t = data.translate(_null_trans, text_characters)

                # If more than 30% non-text characters, then
                # this is considered a binary file
                if len(t)/len(data) > 0.30:
                    continue
                tar_text_file_num += 1
            if float(tar_text_file_num)/float(allTarFile_num) > 0.8:
                yield file
        else:
            s = open(file).read(blocksize)
            if "\0" in s:
                continue
            if not s:  # Empty files are considered text
                yield file
                continue

            # Get the non-text characters (maps a character to itself then
            # use the 'remove' option to get rid of the text characters.)
            t = s.translate(_null_trans, text_characters)

            # If more than 30% non-text characters, then
            # this is considered a binary file
            if len(t)/len(s) > 0.30:
                continue
            yield file

        
def ReMatch(file_list):
    for file in file_list:
        for COMPILE in dest_reList:
            p = re.compile(COMPILE)
            result = p.match(file)
            if result:
                yield result.group()


def Compress(file_list, tar_name, compression='gz'):
    global dest_path
    if compression:
        dest_ext = '.' + compression
    else :
        dest_ext = ''

    if compression:
        dest_cmp = ':' + compression
    else :
        dest_cmp = ''
    arcname = tar_name
    dest_name = '%s.tar%s' % (arcname,dest_ext)
    dest_path = '%s/'%path4save_tar + dest_name
    out = tarfile.TarFile.open(dest_path, 'w'+dest_cmp)
    for tar in file_list:
        if re.match('\d{4}-\d{2}-\d{2}-\d{2}\:\d{2}\.tar\.gz',os.path.basename(tar)):
            continue
        elif get_disk_idl() < threshold :
            logger.info("tar file and to delete: %s"%tar)
            out.add(tar)
            try:
                os.remove(tar)
            except OSError:
                logger.debug("when rm the file:%s,is error.check user Permission."%tar)
                break
        else :
            out.close()
            break
    out.close()
    return dest_path


def get_disk_idl():
    vfs = os.statvfs("/")
    available = vfs[statvfs.F_BAVAIL]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)
    total = vfs[statvfs.F_BLOCKS]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)
    used = total - available
    usage = (float(used)/float(total))*100
    idle = (float(available)/float(total))*100
    return idle

def get_opened_fd():
    pids=os.listdir('/proc')
    open_files = {}
    fd_list = []
    for pid in sorted(pids):
        try:
            int(pid)
        except ValueError:
            continue
        fd_dir=os.path.join('/proc', pid, 'fd')
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for file in fds:
            try:
                link=os.readlink(os.path.join(fd_dir, file))
            except OSError:
                continue
            fd_list.append(link)
    for file in fd_list:
        try:
            if os.path.exists(file):
                yield file
        except Exception, e:
            continue

def getfilelist(path4scan):
    global global_Filelist
    file_list = []

    for root, dirs, files in os.walk(path4scan):
        if re_word4exclude.findall(root):continue
        for file in files:
            fullFilePath = os.path.join(root, file)
            if os.path.exists(fullFilePath) and float(os.path.getsize(fullFilePath))/1024/1024 > size:
                file_list.append(fullFilePath)

    '''for judge file is a plain text file?'''
    if file_list:
        file_list = [ i for i in IsTxtFile(file_list)]
    else:
        #print path4scan,"is empty."
        pass

    '''for judge file is match the Regular of config specified'''
    if file_list:
        file_list = filter(None, [ i for i in ReMatch(file_list)])

    global_Filelist += file_list



def processer(global_Filelist):
    global IGNORE_SCAN_ACTION
    fileTime_dict = {}
    destFile_list = []
    

    '''remove file from destFile_list,if the file had opened with in some program'''
    openedFile_list = filter(lambda x:x in [ i for i in get_opened_fd()], global_Filelist)
    map(lambda x:global_Filelist.remove(x), openedFile_list)

    '''sort by time for filelist'''
    for file in global_Filelist:
        fileTime_dict[file] = os.stat(file).st_mtime
    map(lambda x:destFile_list.append(x[0]), sorted(fileTime_dict.items(),key=lambda d:d[1]))

    if Delete and destFile_list:
        for file in destFile_list:
            if get_disk_idl() < threshold and int(time.time()) - int(intervalTime)*86400 > int(os.stat(file).st_mtime):
                try:
                    logger.info('1.0delete file: %s'%file)
                    os.remove(file)
                except Exception,e:
                    logger.debug("when delete file:%s"%e)
                else:
                    IGNORE_SCAN_ACTION = False
            elif get_disk_idl() <= 10 and int(time.time()) - 600 > int(os.stat(file).st_mtime):
                try:
                    logger.info('2.0delete file: %s'%file)
                    os.remove(file)
                except Exception,e:
                    logger.debug("when 2.0 delete file:%s"%e)
                else:
                    IGNORE_SCAN_ACTION = False
            else:
                IGNORE_SCAN_ACTION = True
    if Delete and openedFile_list and get_disk_idl() <= 2:
        IGNORE_SCAN_ACTION = True
        for file in openedFile_list:
            try:
                logger.info("Flush file: %s"%file)
                open(file,'w').close()
            except Exception, e:
                logger.debug("Flush file:%s break some error"%file)
                continue
    if not Delete and destFile_list:
        map(lambda x:file4compress_list.append(x), [i for i in destFile_list])
   

class Compresser(Thread):
    def __init__(self, file_list, tar_name):
        Thread.__init__(self)
        self.file_list = file_list
        self.tar_name = tar_name
    def run(self):
        Compress(self.file_list, self.tar_name)


def main(path='/'):
    global IGNORE_SCAN_NUM
    global global_Filelist
    global_Filelist = []
    if IGNORE_SCAN_ACTION and IGNORE_SCAN_NUM <= 3:
        IGNORE_SCAN_NUM += 1
        logger.info("Cache last scan..., ignore scan Num:%s"%IGNORE_SCAN_NUM)
        return
    else:
        IGNORE_SCAN_NUM = 0

    dir_list = filter(lambda x:os.path.isdir(x),[os.path.join(path,i) for i in os.listdir(path)])

    '''exclude system dir NO1'''
    dir_list = filter(lambda x:not re_word4exclude.findall(x), dir_list)

    second_dir_list = []
    path4scan_list = []
    for subdir in dir_list:
        for i in os.listdir(subdir):
            subpath = os.path.join(subdir,i)
            if os.path.isdir(subpath) and os.path.exists(subpath):
                second_dir_list.append(subpath)

    '''枚举出第3层目录'''
    third_dir_list = map(lambda x:os.listdir(x), second_dir_list)
    for index, root in enumerate(second_dir_list):
        for dir in third_dir_list[index]:
            path4scan_list.append(os.path.join(root,dir))

    '''exclude the system dir again'''
    path4scan_list = filter(lambda x:not re_word4exclude.findall(x), path4scan_list)
    
    '''start multi threading for scan work, from above info path4scan_list'''
    wm = WorkerManager(10)
    for path4scan in path4scan_list:
        wm.add_job(getfilelist, path4scan)
    wm.start()
    wm.wait_for_complete()
    processer(global_Filelist)
   

def send2sftp():
    if SP:
        cmd = 'mkdir -p /opt/logbackup/%s && chown -R logbackup.logbackup /opt/logbackup/%s'%(getLocalIp(),getLocalIp())
        LocalPath = dest_path
        RemotePath = '/opt/logbackup/%s'%getLocalIp() + '/' +  tar_name + '.tar.gz'
        
        sshCommand(SftpHost, cmd, SftpHostUser, SftpHostPwd, SftpPort)
        sftpFile(SftpHost, LocalPath, RemotePath, SftpHostUser, SftpHostPwd, SftpPort)
        if True:
            os.remove(dest_path)

def send2mail():
    if SM:
        try:
            sendEmail(smtpServer,smtpUser,smtpPwd,fromMail,toMail)
        except Exception, e:
            #syslog.syslog("sendEmail error: %s"%e)
            logger.debug("sendEmail error: %s"%e)


def sshCommand(host,cmd,user='root',passwd='XXXXXX',myport=58422):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    privatekeyfile = os.path.expanduser('%s'%rsa_key)
#    mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
    ssh.connect(host,port=myport,username=user,password=passwd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    a = stdout.readlines()
    stdout = "Successful on:[%s],exec_commands: [%s]"%(host,cmd) + " result is: " + str(a)
    return stdout


def sftpFile(host,LocalPath,RemotePath,user = 'root',passwd = 'XXXXXX',port = 58422):
    import paramiko
    ssh = paramiko.SSHClient()
    try:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#        ssh.load_host_keys(os.path.expanduser(os.path.join("~",".ssh","known_hosts")))
#        if usekey == 1:
#             privatekeyfile = os.path.expanduser('%s'%id_rsa)
#             mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
#             ssh.connect(ip,username=user,pkey=mykey)
#        elif usekey == 0:
        ssh.connect(host,username=user,password=passwd,port=port )
#        else :
#             pass
        sftp = ssh.open_sftp()
        sftp.put('%s'%LocalPath,'%s'%RemotePath)
        time.sleep(3)
        sftp.close()
        ssh.close()
    except Exception, e:
        #syslog.syslog(e)
        logger.debug("sftpFile func error:%s"%e)
        ssh.close()


def getLocalIp():
    from socket import socket, SOCK_DGRAM, AF_INET
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('8.8.8.8',0))
    LocalIp = s.getsockname()[0]
    s.close()
    return LocalIp

def InitLog():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("/var/log/cldisky.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)


'''daemon 类'''

#if __name__ == "__main__":
#   main()
class MyDaemon(Daemon):
    def run(self):
        global IGNORE_SCAN_ACTION, IGNORE_SCAN_NUM
        IGNORE_SCAN_ACTION = False
        IGNORE_SCAN_NUM = 0
        InitLog()
        while True:
            dl = get_disk_idl()
            if dl < avail :
                if IGNORE_SCAN_NUM == 0:
                    logger.info('1:Disk Idle:%s, Scan disk.(files %s days ago.)'%(int(dl),intervalTime))
                file4compress_list = []
                main(ScanPath)
                if not Delete:
                    tar_name = time.strftime(ISOTIMEFORMAT,time.localtime())
                    TH = Compresser(file4compress_list, tar_name)
                    TH.start()
                    while TH.isAlive():
                        time.sleep(3)
                    logger.info("tar process have to complete!@_@")
            else:
                logger.info("Disk Idle:%s, to sleep."%int(get_disk_idl()))
            time.sleep(600)
