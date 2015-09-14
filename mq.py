#coding=utf-8
import os
import pymqi
import CMQC
import logging
import sys


class MQ:
	def __init__ (self, host, port, qManager, channel):
		self.queue_manager = qManager
		self.channel = channel
		self.host = host
		self.port = port
		self.connectionString = "%s(%s)" % (self.host, self.port)


	def connect(self):
		print "Connecting to \t%s,\n QueueManagerName =\t%s,\n Channel =\t%s\n" % (self.connectionString, self.queue_manager, self.channel)
		self.qmgr = pymqi.connect(self.queue_manager, self.channel, self.connectionString)

	def disconnect(self):
		self.qmgr.disconnect()


	def get(self, queue):
		q = pymqi.Queue(self.qmgr, queue)
		md = pymqi.MD()
		try:
			message = q.get(None, md)
		except pymqi.MQMIError, e:
			if e.comp == CMQC.MQCC_FAILED and e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
				return
		print "md = %s\n" % (md)
		q.close()
		return message
		

	def put (self, queue, message, replyTo = '', ApplIdentityData = ''):

		od = pymqi.od()
		od.ObjectName = queue

		q = pymqi.Queue(self.qmgr)
		q.open(od, CMQC.MQOO_OUTPUT | CMQC.MQOO_SET_ALL_CONTEXT)		

		pmo = pymqi.pmo()
		pmo.Options = CMQC.MQPMO_SET_ALL_CONTEXT

		md = pymqi.MD()

		md.ReplyToQ         = replyTo
		md.ReplyToQMgr      = self.queue_manager
		md.ApplIdentityData = ApplIdentityData
		md.Format           = 'MQSTR'

		q.put(message, md, pmo)
		q.close()





def main():
	logging.basicConfig(level=logging.INFO)
    
	if len(sys.argv) != 3: # generating some usage info, if there's not enought parameters
	    print "MQ send file to DTCC UAT"	    
	    print "Usage: python " + sys.argv[0] + " %ccommand% %in_file_name% \n\t%command% - 'put' or 'get'\n\t%in_file_name%\tfull file name to sent"
	    sys.exit(1)

	command  = sys.argv[1]
	in_file  = sys.argv[2]

	if command not in ['get', 'put']:
		print 'Invalid command: %s' % command
		sys.exit(1)
  

	#queue_manager = "U01FLO100"
	queue_manager = "QM2"
	channel = "APP"
	#host = "mq-dev"
	#port = "1414"
	host = "vm-gkradecky"
	port = "5505"
	conn_info = "%s(%s)" % (host, port)

	#queue_name = "FPML_CREDITS_OUT"
	#replyToQueue = "FPML_CREDITS_IN"

	#queue_name = "FPML_COMMODITY_OUT"
	#replyToQueue = "FPML_COMMODITY_IN"

	#queue_name = "FPML_FX_OUT"
	#replyToQueue = "FPML_FX_IN"

	#queue_name   = "FPML_EQUITY_OUT"
	#replyToQueue = "FPML_EQUITY_IN"

	#queue_name = "FPML_INTRATES_OUT"	
#	replyToQueue = "FPML_INTRATES_IN"
	queue_name   = "SEND.Q"
	replyToQueue = "LOCAL.Q3"
	
	identity = '01FLO100JEKA5r7F'


	if command == 'put':
		if os.path.isfile(in_file) == False: # chech if input file exists
			print "ERROR: file [" + in_file + "] doesn't exists"
			sys.exit(1)
		with open (in_file, "r") as myfile:
			message_text = myfile.read()


	mq = MQ(host, port, queue_manager, channel)
	mq.connect()

	if command == 'put':
		mq.put(queue_name, message_text, replyToQueue, identity)
	if command == 'get':
		msg = mq.get(replyToQueue)
		if msg:
			with open(in_file, "w") as text_file:
				text_file.write(msg)
		else:
			print "No messages found in queue [%s]" % replyToQueue

	mq.disconnect()	


	


if __name__ == '__main__':
	main()
