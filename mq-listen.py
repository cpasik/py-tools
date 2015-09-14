#coding=utf-8

import CMQC
import pymqi
import sys
import os
import uuid


queue_manager = "U01FLO100"
channel = "APP"
host = "mq-dev"
port = "1414"

conn_info = "%s(%s)" % (host, port)


if len(sys.argv) != 3: # generating some usage info, if there's not enought parameters
	print "MQ read messages from DTCC UAT"	    
	print "Usage: python " + sys.argv[0] + " [queue] [directory] \n\t[queue] - queue name to read\n\t[directory]\tDirectory to save files"
	sys.exit(1)


queue_name  = sys.argv[1]
folder = sys.argv[2]

if not os.path.isdir(folder):
	print "[%s] is not a folder" % folder
	sys.exit(1)


# Message Descriptor
md = pymqi.MD()

# Get Message Options
gmo = pymqi.GMO()
gmo.Options = CMQC.MQGMO_WAIT | CMQC.MQGMO_FAIL_IF_QUIESCING
gmo.WaitInterval = 2500 # 2.5 seconds

qmgr  = pymqi.connect(queue_manager, channel, conn_info)
queue = pymqi.Queue(qmgr, queue_name)

keep_running = True

while keep_running:
		try:
			# Wait up to to gmo.WaitInterval for a new message.
			message = queue.get(None, md, gmo)

			#save message and descr to files
			h = uuid.uuid4()
			filenameM = "%s\\%s-%s-%s.msg" % (folder, md.PutDate, md.PutTime, h)
			filenameD = "%s\\%s-%s-%s.msg.descr" % (folder, md.PutDate, md.PutTime, h)

			print "New message: %s" % filenameM

			with open(filenameM, "w") as text_file:
				text_file.write(message)
			#with open(filenameD, "w") as text_file:
			#	text_file.write("%s" % md)        

			md.MsgId    = CMQC.MQMI_NONE
			md.CorrelId = CMQC.MQCI_NONE
			md.GroupId  = CMQC.MQGI_NONE

		except pymqi.MQMIError, e:
				if e.comp == CMQC.MQCC_FAILED and e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
					# No messages, that's OK, we can ignore it.
					pass
				else:
					# Some other error condition.
					raise

queue.close()
qmgr.disconnect()
