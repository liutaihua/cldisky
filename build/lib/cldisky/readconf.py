#-*- encoding: utf8 -*- 
import ConfigParser 
import string, os, sys 


cf = ConfigParser.ConfigParser()
if os.path.exists('/etc/cldisky.conf'):
    cf.read("/etc/cldisky.conf")
else:
    #cf.read("%s/config.py"%sys.path[0])
    cf.read("skel/sample.conf")


feedback = cf.getint('general','feedback')
size = cf.getint('general','size')
intervalTime = cf.getint('general','intervalTime')
wait_time = cf.getint('general','wait_time')
tar_path = cf.get('general','tar_path')
ScanPath = cf.get('general','ScanPath')
RP = int(cf.get('general','RP'))
ISOTIMEFORMAT = cf.get('general','ISOTIMEFORMAT')


ext = cf.get('filter','ext').split()
exclude_path = cf.get('filter','exclude_path').split()
reList = [i.strip() for i in cf.get('filter','reList').split('||')]

SP = cf.getint('sftp','SP')
SL = cf.getint('sftp','SL')
SftpHost = cf.get('sftp','SftpHost')
SftpPort = cf.getint('sftp','SftpPort')
SftpHostUser = cf.get('sftp','SftpHostUser')
SftpHostPwd = cf.get('sftp','SftpHostPwd')


SM = cf.getint('mail','SM')
smtpServer = cf.get('mail','smtpServer')
smtpUser = cf.get('mail','smtpUser')
smtpPwd = cf.get('mail','smtpPwd')
fromMail = cf.get('mail','fromMail')
toMail = cf.get('mail','toMail').split()
