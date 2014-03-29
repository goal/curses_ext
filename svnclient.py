import pysvn
import logging

class client:
	username = None
	password = None
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.client = pysvn.Client()
		self.client.callback_get_login = self.get_login

	def get_login(self, realm, username, may_save):
		retcode = True
		username = self.username
		password = self.password
		save = False
		return retcode, username, password, save

	def log(self, end_revision, author=None):
		end_revision = end_revision or pysvn.Revision(pysvn.opt_revision_kind.base)
		logging.debug("end_revision=%s", end_revision)

		logs = self.client.log("./", limit=50, revision_start=end_revision, discover_changed_paths=True)

		end_revision = len(logs) > 0 and logs[-1].revision
		if not author:
			return logs, end_revision
		newlogs = []
		for log in logs:
			if log.author == author:
				newlogs.append(log)
		return newlogs, end_revision

	def diff(self, revision1, revision2):
		return self.client.diff("./", '.', recurse=True, revision1=revision1, revision2=revision2, diff_options=['-u'])

if __name__ == "__main__":
	svn = client("", "")
	for log in svn.log():
		print log.author,log.date,log.message
