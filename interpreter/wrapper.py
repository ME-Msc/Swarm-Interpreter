import threading
import time
import copy

LogLock = threading.Lock()


class Wrapper:
	def __init__(self) -> None:
		self.home = {}

	def copy(self):
		new_wrapper = self.__class__()
		new_wrapper.home = copy.deepcopy(self.home)
		return new_wrapper
	
	def set_home(self, agents_list:list):
		group = len(self.home)
		for i in range(len(agents_list)):
			vhcl_nm = agents_list[i]
			pose = (group, i*2, 0)
			self.home[vhcl_nm] = pose
		time.sleep(2)