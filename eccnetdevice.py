"""
eccnet网络自动化功能库.

远程访问设备库
"""

import pexpect
import sys
import re

class eccDevice:
	'''
	######################################################################
	用途:
		远程访问网络设备底层库。
	功能:
		远程访问网络设备底层库。只对pexpect进行简单包装，不区分设备类型，
		需要人工判断，
	######################################################################
	'''	
	def __init__(self, v_tel_ssh, v_host, v_port, v_username, v_password, v_enable_password, v_prompt, v_page_prompt, v_timeout1, v_timeout2):
		'''
		######################################################################
		名称:
			__init__
		参数:
			v_tel_ssh: 	远程访问方法，值是'telnet' or 'ssh'
			v_host:		设备ip地址
			v_port:		设备端口
			v_username:	用户
			v_password:	密码
			v_enable_password:	超级用户密码
			v_prompt:	命令行提示符
			v_page_prompt:	分页提示符
			v_timeout1:	短超时，用于命令行交互
			v_timeout2:	长超时，用于传文件等需要长时间等待的命令
		返回:
			对象
		用途:
			构造函数
		######################################################################
		'''
		
		if v_tel_ssh == 'telnet':
			self.tel_ssh = 'telnet'
			self.remote_cmd = '/usr/bin/telnet'
		elif v_tel_ssh == 'ssh':
			self.tel_ssh = 'ssh'
			self.remote_cmd = '/usr/bin/ssh'
		else:
			sys.exit()
		self.host = v_host
		self.port = v_port
		self.username = v_username
		self.password = v_password
		self.enable_password = v_enable_password
		self.prompt = v_prompt
		self.page_prompt = v_page_prompt
		self.timeout1 = v_timeout1
		self.timeout2 = v_timeout2
		self.connected = False
		self.output_str = ''
		self.output_strings = []
		self._connect = None
		
		
	def connect(self):
		'''
		######################################################################
		名称:
			connect
		参数:
			无
		返回:
			数组[flag, str].
				flag:1, 成功；0，失败
				如果flag是1，str是''；如果flag是0，str是失败原因
		用途:
			通过ssh或telnet连接远程设备
		######################################################################
		'''		
		if self.tel_ssh == 'ssh':
			v_cmd = '%s -p %d -l %s %s' % (self.remote_cmd, self.port, self.username, self.host)
			try:
				self._connect = pexpect.spawn(v_cmd)
				v_index = self._connect.expect([r'to\scontinue\sconnecting\s\(yes\/no\)\?', r'(P|p)assword\:'], self.timeout1)
				if v_index == 0:
					self._connect.sendline('yes')
				elif v_index == 1:
					self._connect.sendline(self.password)
					try:
						v_index = self._connect.expect([self.prompt], self.timeout1)
					except pexpect.exceptions.TIMEOUT:
						self._connect.close()
						return[0, '登录失败']
			except pexpect.exceptions.TIMEOUT:
				self._connect.close()
				return[0, '登录失败']

				try:
					v_index = self._connect.expect([r'(P|p)assword\:'], self.timeout1)
					self._connect.sendline(self.password)
					v_index = self._connect.expect([self.prompt], self.timeout1)
				except  pexpect.exceptions.TIMEOUT:
					self._connect.close()
					return[0, '登录失败']			
		elif self.tel_ssh == 'telnet':
			v_cmd = '%s %s %d' % (self.remote_cmd, self.host, self.port)
			try:
				self._connect = pexpect.spawn(v_cmd)
				v_index = self._connect.expect([r'sername\:($|\s$)'], self.timeout1)
				self._connect.sendline(self.username)
				v_index = self._connect.expect([r'assword\:($|\s$)'], self.timeout1)
				self._connect.sendline(self.password)
				v_index = self._connect.expect([self.prompt], self.timeout1)
			except pexpect.exceptions.TIMEOUT:
				self._connect.close()
				return[0, '登录失败']
		else:
			return[0, '未知的远程访问方式']
			
		return[1, '']
		
	def disconnect(self):
		'''
		######################################################################
		名称:
			disconnect
		参数:
			无
		返回:
			无
		用途:
			断开连接
		######################################################################
		'''			
		self._connect.close()
		
	def command(self, v_cmd, v_timeout = 1):
		'''
		######################################################################
		名称:
			command
		参数:
			v_cmd:		要执行的命令
			v_timeout:	选择timeout。如果是1，选择timeout1，其他选择timeout2.
						缺省是timeout1。
		返回:
			数组[flag, str].
				flag:1, 成功；0，失败
				如果flag是1，str是''；如果flag是0，str是失败原因
		用途:
			向远程设备发送命令
		######################################################################
		'''	
		self.output_str = ''
		self.output_string = []
		try:
			self._connect.sendline(v_cmd)
			if v_timeout == 1:
				v_tmout = self.timeout1
			else:
				v_tmout = self.timeout2
							
			v_flag = 1
			while v_flag == 1:
				v_index = self._connect.expect([self.prompt, self.page_prompt], v_tmout)					
				if v_index == 0:
					self.output_str += self._connect.before.decode()
					self.output_str = re.sub(r'\x08', '', self.output_str) #处理特殊字符
					#self.output_str = re.sub(r'\e', '', self.output_str)
					self.output_strings = self.output_str.split('\r\n')
					print('=====nopage')
					print()
					v_flag = 0
				elif v_index == 1:  #如果是分页符
					self.output_str += self._connect.before.decode()
					print('=====page')
					print(self._connect.before.decode())
					self._connect.send(' ')
		except pexpect.exceptions.EOF:
			return[0, 'EOF']
		except pexpect.exceptions.TIMEOUT:
			return[0, 'TIMEOUT']
			
		return[1, '']
		
	def setPrompt(self, v_prompt):
		'''
		######################################################################
		名称:
			setPrompt
		参数:
			v_prompt:	提示符
		返回:
			无
		用途:
			设置提示符
		######################################################################
		'''		
		self.prompt = v_prompt
	
	def setPagePrompt(self, v_page_prompt):
		'''
		######################################################################
		名称:
			setPagePrompt
		参数:
			v_page_prompt:	分页提示符
		返回:
			无
		用途:
			设置分页提示符
		######################################################################
		'''		
		self.page_prompt = v_page_prompt
		
	def setUsername(self, v_username):
		'''
		######################################################################
		名称:
			setUsername
		参数:
			v_username:	用户名
		返回:
			无
		用途:
			设置用户名
		######################################################################
		'''			
		self.username = v_username
		

class eccDeviceIA(eccDevice):
	'''
	######################################################################
	用途:
		远程访问网络设备中层库。
	功能:
		远程访问网络设备中层库。能够判断设备厂商、类型、操作系统、版本，并
		进行相应的交互设置（如提示符、分页符、enable等）。
	######################################################################
	'''	
	def __init__(self, v_tel_ssh, v_host, v_port, v_username, v_password, v_enable_password, v_timeout1 = 5, v_timeout2 = 60):
		'''
		######################################################################
		名称:
			__init__
		参数:
			v_tel_ssh: 	远程访问方法，值是'telnet' or 'ssh'
			v_host:		设备ip地址
			v_port:		设备端口
			v_username:	用户
			v_password:	密码
			v_enable_password:	超级用户密码
			v_timeout1:	短超时，用于命令行交互，缺省是10s。
			v_timeout2:	长超时，用于传文件等需要长时间等待的命令。缺省是60s。
		返回:
			对象
		用途:
			构造函数
		######################################################################
		'''
		
		'''
		命令提示符设置
		思科: 	'主机名#' '<主机名>'
		华三:	'<主机名>'
		'''
		v_prompt = r'[\r\n][<]{0,1}[\w\-]{4,}(#$|#\s|>$|>\s$)'
		'''
		分页符设置
		思科:	'--More--'
		华三:	'---- More ----'
		'''
		v_page_prompt = r'(--More--|----\sMore\s----)'	
		
		eccDevice.__init__(self, v_tel_ssh, v_host, v_port, v_username, v_password, v_enable_password, v_prompt, v_page_prompt, v_timeout1, v_timeout2)
		
		self.vendor = ''
		self.type = ''
		self.model = ''
		self.os = ''
		self.version1 = ''
		self.version2 = ''
		
	def connect(self):
		v_ret = []
		v_ret = eccDevice.connect(self)
		if v_ret[0] == 0:
			eccDevice.setUsername(self, self.username + '@boc')
			v_ret = eccDevice.connect(self)
		if v_ret[0] == 0:
			return[0, '登录失败']
		'''
		用查看版本号的方法判断设备类型
		思科:
			show version
			需要处理的出错信息
				% Bad IP address or host name% Unknown command or computer name, or unable to find computer address
				% Type "show ?" for a list of subcommands
				% Invalid input detected at '^' marker.
		华三:
			display version
			需要处理的出错信息
				 % Unrecognized command found at '^' position.
		华为:
			display version
			需要处理的出错信息
				Error: Unrecognized command found at '^' position.
				Error:Incomplete command found at '^' position.
		'''
		# cisco设备处理
		eccDevice.command(self, 'show version')
		if re.findall(r'(C|c)isco', self.output_str, re.S): #判断是否是cisco
			self.vendor = 'cisco'
			if re.findall(r'IOS-XE', self.output_str, re.S): #判断是否是ios-xe
				self.os = 'ios-xe'
			elif re.findall(r'IOS', self.output_str, re.S): #判断是否是ios
				self.os = 'ios'
				v_v1 = re.findall(r'Version\s+([0-9\.]+)', self.output_str, re.S) #获取版本号
				if v_v1: 
					self.version1 = v_v1[0]
		if self.vendor != '' and self.os != '':
			return[1, '']
			
		# h3c设备处理
		eccDevice.command(self, 'display version')
		if re.findall(r'H3C', self.output_str, re.S): #判断是否是h3c
			self.vendor = 'h3c'
			if re.findall(r'Comware', self.output_str, re.S): #判断是否是comware
				self.os = 'comware'
				v_v1 = re.findall(r'Version\s+([0-9\.]+)', self.output_str, re.S) #获取版本号
				if v_v1: 
					self.version1 = v_v1[0]
		if self.vendor != '' and self.os != '':
			return[1, '']
			
		# h3c设备处理
		eccDevice.command(self, 'display version')
		if re.findall(r'H3C', self.output_str, re.S): #判断是否是h3c
			self.vendor = 'h3c'
			if re.findall(r'Comware', self.output_str, re.S): #判断是否是comware
				self.os = 'comware'
				v_v1 = re.findall(r'Version\s+([0-9\.]+)', self.output_str, re.S) #获取版本号
				if v_v1: 
					self.version1 = v_v1[0]
		if self.vendor != '' and self.os != '':
			return[1, '']			

		# huawei设备处理
		eccDevice.command(self, 'display version')
		if re.findall(r'(H|h)uawei', self.output_str, re.S): #判断是否是h3c
			self.vendor = 'huawei'
			if re.findall(r'VRP', self.output_str, re.S): #判断是否是comware
				self.os = 'vrp'
				v_v1 = re.findall(r'Version\s+([0-9\.]+)', self.output_str, re.S) #获取版本号
				if v_v1: 
					self.version1 = v_v1[0]
		if self.vendor != '' and self.os != '':
			return[1, '']	

		return[0, '']