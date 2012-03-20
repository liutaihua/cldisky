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
import threading, Queue
from threading import Thread
import tarfile
import statvfs
from daemon import Daemon
from mail import *
from readconf import *





threshold = 8 + avail
ISOTIMEFORMAT='%Y-%m-%d-%H:%M'
re_word4exclude = re.compile("lib.*|dev|media|etc|var|proc|selinux|lost\+found|sys|srv|cdrom|run|bin|sbin|boot|share|include|man|kernel|libexec|git")



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
                syslog.syslog(e)
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
            syslog.syslog("tar file and to delete: %s"%tar)
            out.add(tar)
            try:
                os.remove(tar)
            except OSError:
                syslog.syslog("then rm the file:%s,is error.check user Permission.\n"%tar)
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
    file_list = []
    destFile_list = []
    fileTime_dict= {}

    for root, dirs, files in os.walk(path4scan):
        if re_word4exclude.findall(root):continue
        for file in files:
            fullFilePath = os.path.join(root, file)
            if os.path.exists(fullFilePath) and float(os.path.getsize(fullFilePath))/1024/1024 > size:
                file_list.append(fullFilePath)
    if file_list:
        file_list = [ i for i in IsTxtFile(file_list)]
    else:
        #print path4scan,"is empty."
        pass

    if file_list:
        file_list = filter(None, [ i for i in ReMatch(file_list)])

    '''sort by time for filelist'''
    for file in file_list:
        fileTime_dict[file] = os.stat(file).st_mtime
    map(lambda x:destFile_list.append(x[0]), sorted(fileTime_dict.items(),key=lambda d:d[1]))

    return destFile_list



def processer(path4scan):
    global ignore_scan
    destFile_list = getfilelist(path4scan)

    '''remove file from destFile_list,if the file had opened with in some program'''
    openedFile_list = filter(lambda x:x in [ i for i in get_opened_fd()], destFile_list)
    map(lambda x:destFile_list.remove(x), openedFile_list)

    if Delete and destFile_list:
        for file in destFile_list:
            if get_disk_idl() <= 10 and int(time.time()) - 600 > int(os.stat(file).st_mtime):
                try:
                    syslog.syslog('1.0delete file: %s'%file)
                    os.remove(file)
                except Exception,e:
                    syslog.syslog(e)
                else:
                    ignore_scan = False
            elif get_disk_idl() < threshold and int(time.time()) - int(intervalTime)*86400 > int(os.stat(file).st_mtime):
                try:
                    syslog.syslog('2.0delete file: %s'%file)
                    os.remove(file)
                except Exception,e:
                    syslog.syslog(e)
                else:
                    ignore_scan = False
            else:
                ignore_scan = True
    if Delete and openedFile_list and get_disk_idl() <= 3:
        ignore_scan = True
        for file in openedFile_list:
            try:
                syslog.syslog("Flush file: %s"%file)
                f = open(file,'w')
                f.flush()
                time.sleep(1)
                f.close()
            except Exception, e:
                syslog.syslog("Flush file:%s break some error"%file)
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
    global ignore_scan_num
    if ignore_scan and ignore_scan_num <= 3:
        ignore_scan_num += 1
        syslog.syslog("Cache last scan..., ignore scan Num:%s"%ignore_scan_num)
        return
    else:
        ignore_scan_num = 0

    dir_list = filter(lambda x:os.path.isdir(x),[os.path.join(path,i) for i in os.listdir(path)])

    _path4scan_list = []
    path4scan_list = []
    for subdir in dir_list:
        for i in os.listdir(subdir):
            subpath = os.path.join(subdir,i)
            if os.path.isdir(subpath):
                _path4scan_list.append(subpath)

    path4scan_subdir_lit = map(lambda x:os.listdir(x), _path4scan_list)

    '''exclude the system dir'''
    for index, root in enumerate(_path4scan_list):
        for dir in path4scan_subdir_lit[index]:
            path4scan_list.append(os.path.join(root,dir))
    path4scan_list = filter(lambda x:not re_word4exclude.findall(x), path4scan_list)
    
    wm = WorkerManager(10)
    for path4scan in path4scan_list:
        wm.add_job(processer, path4scan)
    wm.start()
    wm.wait_for_complete()
   

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
            syslog.syslog("sendEmail error: %s"%e)


def sshCommand(host,cmd,user='root',passwd='WD#sd7258',myport=58422):
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


def sftpFile(host,LocalPath,RemotePath,user = 'root',passwd = 'WD#sd7258',port = 58422):
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
        syslog.syslog(e)
        ssh.close()


def getLocalIp():
    from socket import socket, SOCK_DGRAM, AF_INET
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('8.8.8.8',0))
    LocalIp = s.getsockname()[0]
    s.close()
    return LocalIp


'''daemon 类'''

#if __name__ == "__main__":
#   main()
class MyDaemon(Daemon):
    def run(self):
        global ignore_scan, ignore_scan_num
        ignore_scan = False
        ignore_scan_num = 0
        syslog.openlog('ScanDisk',syslog.LOG_PID)
        while True:
            dl = get_disk_idl()
            if dl < avail :
                syslog.syslog('1:Disk Idle:%s, Scan disk.(files %s days ago.)'%(int(dl),intervalTime))
                file4compress_list = []
                main(ScanPath)
                if not Delete:
                    tar_name = time.strftime(ISOTIMEFORMAT,time.localtime())
                    TH = Compresser(file4compress_list, tar_name)
                    TH.start()
                    while TH.isAlive():
                        time.sleep(3)
                    syslog.syslog("tar process have to complete!@_@")
            else:
                syslog.syslog("Disk Idle:%s, to sleep."%int(get_disk_idl()))
            time.sleep(600)
