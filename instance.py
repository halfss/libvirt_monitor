#!/usr/bin/env python2.7
#coding= utf8

import libvirt
import time
import Queue,threading
import os,sys
import MySQLdb
import traceback
import conf
from  my_libvirt_lib import *

queue=Queue.Queue()
MAXTHREAD=5
log_dir=sys.path[0]

uri='qemu+tcp:///system'
def get_node_info():
	global MAXTHREAD
	conn=libvirt.open(uri)
	doms=conn.listDomainsID()
	if doms==[]:
		while True:
			doms=conn.listDomainsID()
			if doms==[]:
				time.sleep(60)
	for dom_id in doms:
		queue.put(dom_id)
		class get_dom_info(threading.Thread):
			global queue
			def run(self):
				while not queue.empty():
					dom_id=queue.get()
					vm_status='down'
					block_status0={}
					block_status1={}
					net_status0={}
					net_status1={}
					block_info=[]
					block_status=' '
					nic_status=' '
					try:
						dom=conn.lookupByID(dom_id)
						dom_info=dom.info()
						disks=get_devices(dom,"devices/disk/target","dev")
						nics=get_devices(dom,"devices/interface/target","dev")
						for block in disks:
							block_status0[block]=dom.blockStats(block)
						for nic in nics:
							net_status0[nic]=[os.popen("cat /proc/net/dev |grep '"+nic+"' |awk '{print $10}'").readlines()[0][:-1],os.popen("cat /proc/net/dev |grep '"+nic+"' |awk '{print $2}'").readlines()[0][:-1]]
						Lstart_time=time.time()*1000000000
						Dstart_time=dom.info()[4]
						time.sleep(2)
						Dstop_time=dom.info()[4]
						Lstop_time=time.time()*1000000000
						for block in disks:
							block_status1[block]=dom.blockStats(block)
						for nic in nics:
							net_status1[nic]=[os.popen("cat /proc/net/dev |grep '"+nic+"' |awk '{print $10}'").readlines()[0][:-1],os.popen("cat /proc/net/dev |grep '"+nic+"' |awk '{print $2}'").readlines()[0][:-1]]
						for block in get_devices(dom,"devices/disk/source","file"):
							block_info.append(dom.blockInfo(block,0))
						for nic in nics:
							try:
								nic_status+=nic+"-"+str(int(net_status1[nic][1]))+"-"+str((int(net_status1[nic][1])-int(net_status0[nic][1]))*4)+"-"+str(int(net_status1[nic][0]))+"-"+str((int(net_status1[nic][0])-int(net_status0[nic][0]))*4)+"::"
							except:
								nic_stauus=''
						i=0
						for block in get_devices(dom,"devices/disk/target","dev"):
							block_status+=block+"-"+str(block_info[i][1]/1.0/block_info[i][0]*100)[:5]+"-"+str((block_status1[block][1]-block_status0[block][1])/2048.0)+"-"+str((block_status1[block][3]-block_status0[block][3])/2048.0)+"-"+str(block_info[i][0])+"::"
							i=i+1
						cpu_usage=(Dstop_time-Dstart_time)/(Lstop_time-Lstart_time)/int(dom.info()[3])*100
						if cpu_usage>100:
							cpu_usage=100
						if dom_info[0]==1:
							vm_status='active'
						memstatus=os.popen("awk /VmRSS/'{print $2}' /proc/`ps aux | grep -v 'grep' |grep "+dom.name()+"|awk '{print $2}' `/status").readlines()[0][:-1]
						memusage=int(memstatus)*100.0/int(dom_info[2])
						if memusage>100:
							memusage=100
						name=int(dom.name().split('-')[-1],16)
					except (KeyboardInterrupt,SystemExit):
						raise
					except:
						traceback.print_exc()
						break
					db_conn=MySQLdb.connect(host=conf.db_host,user=conf.db_user,passwd=conf.db_passwd,db=conf.db)
					cursor=db_conn.cursor()
					cmd="insert into instance (instance_id,timestamp,cpu,mem,disk,net)  values ('"+str(name)+"','"+str(time.time())+"','"+str(cpu_usage)[:5]+"','"+str(memusage)+"','"+block_status+"','"+nic_status+"')"
					print cmd
					cursor.execute(cmd)
					db_conn.close()	
					queue.task_done()
	
	if queue.qsize()<MAXTHREAD:
		MAXTHREAD=queue.qsize()
	for i in xrange(0,MAXTHREAD):
		get_dom_info().start()
	queue.join()
def start():
	while True:
		get_node_info()
		time.sleep(300)

if __name__=="__main__":
	daemonize(stdout=log_dir+'/instancestdout.log', stderr=log_dir+'/instancestderr.log',pidfile=log_dir+'/monitor/pid.txt')
	start()
