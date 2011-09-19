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
import threading
import tarfile
import statvfs
from daemon import Daemon
from mail import *
from readconf import *





threshold = 8 + avail
callBackList = []
tar_path = '/tmp/'
ISOTIMEFORMAT='%Y-%m-%d-%H:%M'
dest_exclude_path = ['/etc', '/var', '/mnt', '/bin', '/sbin', '/boot', '/dev', '/lib', '/lib64', '/home', '/misc', '/lost+found', '/media', '/proc', '/root', '/selinux', '/srv', '/sys', '/usr']


'''定义扫描'''
class ScanThread(threading.Thread):
    def __init__(self, path, size):
        threading.Thread.__init__(self)
        #self.no = no
        self.path = path
        self.size = size
        self.txtfile_list = []
        self.match_list = []
        self.tar_name = time.strftime(ISOTIMEFORMAT,time.localtime())


    def run(self):
        file_list = []
        txtfile_list = self.txtfile_list
        match_list = self.match_list
        for root , dirs , files in os.walk(self.path):
            for file in files:
                int_file = os.path.join(root,file)
                fileTime = os.stat(int_file).st_mtime
                '''
                进行时间间隔匹配过滤'''
                if check_disk_used() < 1:
                    file_list.append(int_file)
                elif float(os.path.getsize(int_file))/1024/1024 > self.size and (int(fileTime) < int(time.time() - int(intervalTime)*86400)) :
                    file_list.append(int_file)
        if file_list:
            IsTxtFile(file_list, txtfile_list)
        if txtfile_list:
            '''
            进行config内指定的re匹配规则进行匹配'''
            ReMatch(txtfile_list, match_list)
        if match_list:
            if Delete:
                for file in match_list:
                    if check_disk_used() < threshold:
                        try:
                            os.remove(file)
                            syslog.syslog('delete file: %s'%file)
                        except Exception,e:
                            syslog.syslog(e)
                    else:break
            else :
                tar(match_list, self.tar_name)
                callBcak()
        else:
            syslog.syslog("%s is empty."%self.path)

def IsTxtFile(file_list, txtfile_list, blocksize = 512):
    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    for file in file_list:
        s = open(file).read(blocksize)
        if "\0" in s:
            continue
        if not s:  # Empty files are considered text
            txtfile_list.append(file)
            continue

        # Get the non-text characters (maps a character to itself then
        # use the 'remove' option to get rid of the text characters.)
        t = s.translate(_null_trans, text_characters)

        # If more than 30% non-text characters, then
        # this is considered a binary file
        if len(t)/len(s) > 0.30:
            continue
        txtfile_list.append(file)
    return txtfile_list

        
def ReMatch(file_list, match_list):
    for file in file_list:
        for COMPILE in dest_reList:
            p = re.compile(COMPILE)
            result = p.match(file)
            if result:
                match_list.append(result.group())
    match_list = filter(None,match_list)
    return match_list


'''打包压缩'''
def tar(file_list, tar_name, compression='gz'):
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
    dest_path = '%s/'%tar_path + dest_name
    out = tarfile.TarFile.open(dest_path, 'w'+dest_cmp)
    for tar in file_list:
        if check_disk_used() < threshold :
            callBack()
            syslog.syslog("tar file and to delete: %s"%tar)
            out.add(tar)
            callBack()
            try:
                os.remove(tar)
            except OSError:
                syslog.syslog("then rm the file:%s,is error.check user Permission.\n"%tar)
                break
        else :
            out.close()
            break
    out.close()
    if SP:
        cmd = 'mkdir -p /opt/logbackup/%s && chown -R logbackup.logbackup /opt/logbackup/%s'%(getLocalIp(),getLocalIp())
        LocalPath = dest_path
        RemotePath = '/opt/logbackup/%s'%getLocalIp() + '/' +  dest_name

        sshCommand(SftpHost, cmd, SftpHostUser, SftpHostPwd, SftpPort)
        sftpFile(SftpHost, LocalPath, RemotePath, SftpHostUser, SftpHostPwd, SftpPort)
        if True:
            os.remove(dest_path)
    return nameList


'''磁盘check'''
def check_disk_used():
    vfs = os.statvfs("/")
    available = vfs[statvfs.F_BAVAIL]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)
    total = vfs[statvfs.F_BLOCKS]*vfs[statvfs.F_BSIZE]/(1024*1024*1024)
    used = total - available
    usage = (float(used)/float(total))*100
    idle = (float(available)/float(total))*100
   
    return idle



def main(path='/'):
    rootList = []
    threadList = []
    if exclude_path:
        for i in exclude_path:
            dest_exclude_path.append(i)
    for dir in os.listdir(path):
        tmp_path = ''.join(['/'+ path + '/' + dir])
        if os.path.isdir(tmp_path):
            tmp_dir = ''.join([path + dir])
            if tmp_dir not in dest_exclude_path:
                dest_dir = os.path.join(path,dir)
                rootList.append(dest_dir)
    for i in range(len(rootList)):
        #tmp_no = rootList[i].split('/')
        #no = path.replace('/','-') + '-' + tmp_no[len(tmp_no)-1]
        thread = ScanThread(rootList[i],size)
        threadList.append(thread)
    for TH in threadList:
        TH.start()
    if SM:
        sendEmail(smtpServer,smtpUser,smtpPwd,fromMail,toMail)

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


'''
建立sftp，接受参数传文件
'''
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
    except paramiko.SSHException:
     ssh.close()


def getLocalIp():
    from socket import socket, SOCK_DGRAM, AF_INET
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(('baidu.com',0))
    LocalIp = s.getsockname()[0]
    s.close()
    return LocalIp


def callBack():
    callBackList.append(time.time())


'''daemon 类'''
class MyDaemon(Daemon):
    def run(self):
        syslog.openlog('ScanDisk',syslog.LOG_PID)
        while True:
            dl = check_disk_used()
            if dl < avail :
                if callBackList:
                    if int(time.time()) - int(callBackList[len(callBackList)-1]) > wait_time*60:
                        syslog.syslog('1:free disk percent is:%s start to scanning disk.(the file that %s hour from now.)'%(int(dl),intervalTime))
                        main(ScanPath)
                    else:
                        syslog.syslog('1.1:waiting for last scanning to complete.')
                        if len(callBackList) > 100:
                            syslog.syslog("callBackList too larger than 100,so flush it.")
                else:
                    syslog.syslog('2:free disk percent is:%s start to scanning disk.(the file that %s hour from now.)'%(int(dl),intervalTime))
                    main(ScanPath)
            else:
                syslog.syslog("0:free disk percent is:%s, continue to sleep."%int(dl))
            time.sleep(300)
        
     
                

