#-*- coding:utf8 -*-
#!/usr/bin/env python


########################################################################
#author:liutaihua
#email: defage@gmail.com
#
#########################################################################

import time
import smtplib, mimetypes, base64 
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from readconf import *
import scaning
  


def sendEmail(smtpServer,smtpUser,smtpPwd,fromMail,toMail):
    ISOTIMEFORMAT='%Y-%m-%d-%H:%M'
    mailTime = time.strftime(ISOTIMEFORMAT,time.localtime())
    msg = MIMEMultipart()
    msg['Subject'] = "磁盘扫描邮件[%s]"%scaning.getLocalIp()
    txt = MIMEText("At time:%s, Machine:[%s],disk idle:%s  start to scanning disk."%(mailTime, scaning.getLocalIp(), int(scaning.check_disk_used())))
    msg.attach(txt)


    fileName = r'/tmp/daemon.pid'
    ctype, encoding = mimetypes.guess_type(fileName)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    att1 = MIMEImage((lambda f: (f.read(), f.close()))(open(fileName, 'rb'))[0], _subtype = subtype)
    att1.add_header('Content-Disposition', 'attachment', filename = fileName)
#    msg.attach(att1)
    xiaoxi = msg.as_string()
    try:
        smtp = smtplib.SMTP()  
        smtp.connect(smtpServer)  
        #smtp.login('%s'%smtpUser, '%s'%smtpPwd)  
        #smtp.sendmail(fromMail, toMail, xiaoxi)  
        #smtp.quit()  
        smtp.docmd("AUTH LOGIN", base64.b64encode(smtpUser))
        smtp.docmd(base64.b64encode(smtpPwd), "")
        smtp.sendmail(fromMail, toMail, xiaoxi)
        smtp.close
        return True
    except Exception, e:
        print str(e)
        return False



#if __name__ == "__main__":
#    sendEmail(smtpServer,smtpUser,smtpPwd,fromMail,toMail)
