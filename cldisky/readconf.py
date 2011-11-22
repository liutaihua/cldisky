#-*- encoding: utf8 -*- 
import ConfigParser 
import string, os, sys 


cf = ConfigParser.ConfigParser()
if os.path.exists('/etc/cldisky.conf'):
    cf.read("/etc/cldisky.conf")
else:
    os.system('cldisky_confecho')
    cf.read("/etc/cldisky.conf")


avail = cf.getint('general','avail')
intervalTime = cf.getint('general','intervalTime')
wait_time = cf.getint('general','wait_time')
try:
    size = cf.getint('general','size')
except Exception, e:
    size = 10
try:
    ScanPath = cf.get('general','ScanPath')
except Exception,e:
    ScanPath = '/'

Delete = int(cf.get('general','Delete'))

#ext = cf.get('filter','ext').split()
try:
    exclude_path = cf.get('filter','exclude_path').split()
except Exception,e :
    exclude_path = []

try:
    dest_reList = ['(.*\\.log)\\.\\d{4}-\\d{1,2}-\\d{1,2}(\\.\\d{1,2})?', '.*\\d{4}-\\d{2}-\\d{1,2}\\.tar\\.gz', '.*\\d{4}-\\d{2}-\\d{2}(-\\d{1,2})?\\.log']
    reList = [i.strip() for i in cf.get('filter','reList').split('||')]
except Exception, e:
    reList = []
if reList:
    map(lambda x:dest_reList.append(i), reList)

try:
    SP = cf.getint('sftp','SP')
    SftpHost = cf.get('sftp','SftpHost')
    SftpPort = cf.getint('sftp','SftpPort')
    SftpHostUser = cf.get('sftp','SftpHostUser')
    SftpHostPwd = cf.get('sftp','SftpHostPwd')
except Exception, e:
    SP = 0
    SftpHost = '10.127.26.241'
    SftpPort = 58422
    SftpHostUser = 'root'
    SftpHostPwd = 'password'


try:
    SM = cf.getint('mail','SM')
    smtpServer = cf.get('mail','smtpServer')
    smtpUser = cf.get('mail','smtpUser')
    smtpPwd = cf.get('mail','smtpPwd')
    fromMail = cf.get('mail','fromMail')
    toMail = cf.get('mail','toMail').split()
except Exception, e:
    SM = 0
    smtpServer = 'mail.snda.com'
    smtpUser = 'ptwarn@snda.com'
    smtpPwd = '8ikju76yh'
    fromMail = 'ptwarn@snda.com'
    toMail = ['defage@gmail.com', 'liutaihua@snda.com']

if not SP and not Delete:
    print "WARNING! Normal,In the absence of none sftp in the case, it's best not to process Tar."
