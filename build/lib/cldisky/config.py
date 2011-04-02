###################
#同一个配置的多个元素之间请用空格分开
#若配置SP = 1 则需要python模块：paramiko
##################


[general]
#磁盘可用阀值百分比
feedback = 20

#文件大小,单位兆
size = 10     

#离now的之前的文件，单位小时
intervalTime = 24

#等待上次压缩完成的时间,单位分钟；若您的日志单个文件最大在10G左右，此处填30，若单个日志文件超过25G，此处填60,以此类推。
wait_time = 30

#打包文件存放目录
tar_path = /tmp

#指定扫描目录
ScanPath = /opt      

#不打包，直接进行删除操作,1代表不打包，0为打包进行
RP = 0


ISOTIMEFORMAT=%Y%m%d%H%M


[filter]
#扩展名 ,暂时无视这个配置
ext = .liutaihua .defage .gz 

#排除的目录
exclude_path = /etc /var /mnt /bin /sbin /boot /dev /lib lib64 /misc /lost+found /media /proc /root /selinux /srv /sys /tmp /usr  

#每条正则语法使用||符号隔开
reList = (.*\.log)\.\d{4}-\d{1,2}-\d{1,2}(\.\d{1,2})?


[sftp]
#sftp开关
SP = 1  

#是否保留打包文件,1为保留
SL = 0

SftpHost = 10.127.26.241
SftpPort = 58422
SftpHostUser = root
SftpHostPwd = WD#sd7258

[mail]
#mail开关
SM = 0  

smtpServer = mail.snda.com
smtpUser = ptwarn@snda.com
smtpPwd = 8ikju76yh
fromMail = ptwarn@snda.com
toMail = liutaihua@snda.com defage@gmail.com
