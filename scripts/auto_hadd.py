#!/usr/bin/python
import os
import argparse
import random
import cPickle as pickle
import base64, zlib
import collections
import threading
import glob
import itertools
import time
import logging
import subprocess
import tempfile
import signal
import shutil
import errno

# don't ask, it was cold outside...
EPILOGUES = pickle.loads(zlib.decompress(base64.b64decode("""eJyNVLtuwzAM3PMV2pIpRN9zp7ZDp04FBAjZiyBDRqLfXvKOdGjngdoQRZF3FEWb2vwc7lZf675v/Tj4tH/Ofd+P2lobNjSHL8yknIYWH3BJamHETBhJWuw5g2Q7xlAKPnWejb5frw73q50frh+RjScfiUHdQo48V4vDTQgSBan37mYB3XRkLIET2JWeCQ+2LWS4NTw2QWoEczMi2PPL2IXiIWQqBVytfUcKmVPv0wbhrBQPYQhWxVxVR5l6np4uXYKieq1kcKbPlgsQvsND+Q5eXeGJh+SatrRSqxi35HeUSlkGG9PmFUeNARg+7ecb1bhzDfxl2HP6Mmjd/jL71tlPbKvjI+sYzdquCTSMvjZV/XTx4eLNxbsLdxBiH/m6AMR+Evtbb0uk9jRvNchTc9WrI9tq2D8qbCOek60kdEX7GMkAouGRthnwhwsdYj5l2bx6FgT/r+kspsZl8JwZznNa5HjBERx0FSakTIgETtAs/gaQJLMpbkWeoBGV6bMLg+NAkFg/RVXIkVAZop2ijFqDUgSmh5uGF1Rsk94syctqt/0DkxWXvA==""")))

CLI = argparse.ArgumentParser(
	formatter_class=argparse.RawDescriptionHelpFormatter,
	description="AMIGHA - Automatic, Multiprocessing, Iterative, meGalomaniacal merging via HAdd",
	epilog=random.choice(EPILOGUES),
)
CLI.add_argument("out_file", help="file to write final output to")

CLI_input = CLI.add_argument_group("file merging", "which files to merge")
CLI_input.add_argument("--file-globs", nargs="+", help="shell glob pattern(s) to check for files")
CLI_input.add_argument("--glob-interval", default=2, type=float, help="Interval for checking for files via globs. [Default: %(default)s]")

CLI_merge = CLI.add_argument_group("merge settings", "how to merge files")
CLI_merge.add_argument("-m", "--mergers", default=1, type=int, help="Maximum number of parallel merge process. [Default: %(default)s]")
CLI_merge.add_argument("-b", "--batch-size", default=4, type=int, help="Number of files to merge at once, if possible. [Default: %(default)s]")
CLI_merge.add_argument("-d", "--tmp-dir", default="/tmp/", help="Temporary directory for intermediate files. [Default: <tempdir>]")

CLI_break = CLI.add_argument_group("break conditions", "when to stop automatic search")
CLI_break.add_argument("-f", "--max-files", default=float("inf"), type=int, help="Stop after finding this many files. [Default: %(default)s]")
CLI_break.add_argument("-t", "--timeout", default=float("inf"), type=int, help="Stop after this much time has passed. [Default: %(default)s]")
CLI_break.add_argument("-s", "--signal", nargs="*", default=["SIGQUIT", "SIGTERM", "SIGINT"], help="Stop after receiving this signal. [Default: %(default)s]")
CLI_break.add_argument("-p", "--pid", nargs="*", default=[], help="Stop after all these processes have finished. [Default: %(default)s]")


class ThreadMaster(object):
	"""
	Restartable, stopable thread
	"""
	def __init__(self, daemon=True):
		self._shutdown = threading.Event()
		self._thread = None
		self._daemon = daemon
		self._logger = logging.getLogger(self.__class__.__name__)

	def start(self):
		if self._thread is not None and self._thread.is_alive():
			return
		self._thread = threading.Thread(target=self.run)
		self._thread.daemon = self._daemon
		self._thread.start()

	def stop(self):
		self._shutdown.set()

	def join(self, timeout=None):
		if self._thread is None:
			return True
		self._thread.join(timeout)
		return not self._thread.is_alive()


class Terminator(ThreadMaster):
	"""
	Stops the automatic processing
	"""
	def __init__(self, max_files, timeout, signals, pids, file_providers, merger):
		ThreadMaster.__init__(self, daemon=False)
		self.timeout = timeout
		self.max_files = max_files
		self._pids = dict.fromkeys(pids, True)
		self._sig_caught = 0
		self._start_time = time.time()
		self._file_count = 0
		self._slaves = list(file_providers) + [merger]
		for provider in file_providers:
			provider.subscribe(self)
		# register termination signals
		for term_sig in signals:
			try:
				signum = int(term_sig)
			except ValueError:
				signum = getattr(signal, term_sig)
			signal.signal(signum, self.signal_handler)

	def report(self):
		return "%s<files=%d/%.0f, time=%.1f/%.1f, pids=%d/%d>" % (self.__class__.__name__, self._file_count, self.max_files, time.time() - self._start_time, self.timeout, len([val for val in self._pids.values() if val]), len(self._pids))

	def run(self):
		while not self._shutdown.wait(1.0):
			if time.time() - self._start_time >= self.timeout:
				self._logger.debug("Timout reached (%.1fs/%.1fs)", time.time() - self._start_time, self.timeout)
				break
			if self._file_count >= self.max_files:
				self._logger.debug("All files processed (%d/%.0f)", self._file_count, self.max_files)
				break
			if not self._check_pids():
				self._logger.debug("All parents finished")
				break
		self._shutdown_all()

	def signal_handler(self, signalnum, frame):
		del frame
		self._sig_caught += 1
		if self._sig_caught == 1:
			self._shutdown_all()
		else:
			os._exit(signalnum)

	def _check_pids(self):
		for pid in self._pids:
			if self._pids[pid]:
				try:
					os.kill(pid, 0)
				except OSError as err:
					if err.errno is errno.EPERM:
						continue
					if err.errno is errno.ESRCH:
						self._pids[pid] = False
					raise
		return not self._pids or any(self._pids.values())

	def _shutdown_all(self):
		for slave in self._slaves:
			slave.stop()
		self.stop()

	def extend(self, elems):
		self._file_count += len(elems)


class FileGlobProvider(ThreadMaster):
	"""
	Searches for files based on static glob patterns
	"""
	def __init__(self, file_globs, glob_interval):
		ThreadMaster.__init__(self, daemon=True)
		self.file_globs = file_globs
		self.glob_interval = glob_interval
		self._subscribers = []
		self._files_found = set()
		self._files_queue = []

	def report(self):
		return "%s<files=%d>" % (self.__class__.__name__, len(self._files_found))

	def run(self):
		while not self._shutdown.wait(self.glob_interval):
			self._reap_files()

	def subscribe(self, recipient):
		self._subscribers.append(recipient)

	def _reap_files(self):
		all_files = set().union(*[glob.glob(file_glob) for file_glob in self.file_globs])
		new_files = all_files - self._files_found
		self._files_found.update(new_files)
		self._files_queue.extend(new_files)
		for subscriber in self._subscribers:
			subscriber.extend(new_files)
		for new_file in new_files:
			self._logger.info("Merging file '%s'", new_file)

	def __iter__(self):
		# yield a new file until we have to shutdown
		curr_idx = 0
		while not self._shutdown.wait(0.2):
			try:
				yield self._files_queue[curr_idx]
			except IndexError:
				continue
			else:
				curr_idx += 1

	def __len__(self):
		return len(self._files_found)


class FileMerger(ThreadMaster):
	"""
	Merges found files iteratively
	"""
	def __init__(self, out_file, file_provider, mergers=1, batch_size=4, work_dir_prefix='/tmp/'):
		ThreadMaster.__init__(self, daemon=False)
		assert mergers >= 1, "Need at least one merger"
		assert batch_size >= 2, "Must merge at least 2 files"
		self.out_file = out_file
		self.mergers = mergers
		self.batch_size = batch_size
		self.work_dir = tempfile.mkdtemp(prefix=work_dir_prefix)
		self._merge_procs = []
		self.src_file_queue = collections.deque()
		self.tmp_file_queue = collections.deque()
		file_provider.subscribe(self.src_file_queue)

	def report(self):
		return "%s<src=%d, tmp=%d, procs=%d/%d>" % (self.__class__.__name__, len(self.src_file_queue), len(self.tmp_file_queue), len(self._merge_procs), self.mergers)

	def run(self):
		tmp_file_name = lambda: os.path.join(self.work_dir, "tmp_merge_%X_%X.root" % (time.time() * 1000000, random.getrandbits(64)))
		# merge until there are no more outstanding files/procs
		while not self._shutdown.wait(0.5) or self._merge_procs or self.src_file_queue or self.tmp_file_queue:
			# merge in batches of new/temporary
			if (len(self.src_file_queue) < self.batch_size and len(self.tmp_file_queue) < self.batch_size):
				# still aggregating scr files, wait for more
				if not self._shutdown.is_set():
					continue
				# all merge steps done, exit...
				if not self.src_file_queue and not self._merge_procs and len(self.tmp_file_queue) == 1:
					break
				# enough tmp files incomming to reach batch size
				if len(self.src_file_queue) + len(self.tmp_file_queue) + len(self._merge_procs) >= self.batch_size:
					continue
				# not enough files to merge right now
				if len(self.src_file_queue) + len(self.tmp_file_queue) < 2:
					continue
			src_files = [self.src_file_queue.popleft() for _ in xrange(min(self.batch_size, len(self.src_file_queue)))]
			tmp_files = [self.tmp_file_queue.popleft() for _ in xrange(min(self.batch_size - len(src_files), len(self.tmp_file_queue)))]
			self._dispatch_merge(src_files=src_files, tmp_files=tmp_files, out_file=tmp_file_name())
		shutil.move(self.tmp_file_queue[0], self.out_file)
		shutil.rmtree(self.work_dir)

	def _dispatch_merge(self, src_files, tmp_files, out_file):
		while len(self._merge_procs) >= self.mergers:
			time.sleep(0.5)
		self._logger.debug("Merging  %3ds + %3d => '%s'", len(src_files), len(tmp_files), out_file)
		# start merger, fork monitor so that we can resume
		merge_proc = subprocess.Popen(["hadd", out_file] + list(src_files) + list(tmp_files), stdout=open("/dev/null", "w"), stderr=open("/dev/null", "w"))
		self._merge_procs.append(merge_proc)
		threading.Thread(target=self._monitor_merge, args=(merge_proc, tmp_files, out_file)).start()

	def _monitor_merge(self, merge_proc, tmp_files, out_file):
		merge_proc.wait()
		self._merge_procs.remove(merge_proc)
		for tmp_file in tmp_files:
			os.unlink(tmp_file)
		self.tmp_file_queue.append(out_file)
		self._logger.debug("Merged   ??? + ??? => '%s'", out_file)


logging.basicConfig()
logging.getLogger().level = logging.DEBUG


if __name__ == "__main__":
	opts = CLI.parse_args()
	start_time = time.time()
	provider = FileGlobProvider(file_globs=opts.file_globs, glob_interval=opts.glob_interval)
	merger = FileMerger(out_file=opts.out_file, file_provider=provider, mergers=opts.mergers, batch_size=opts.batch_size, work_dir_prefix=opts.tmp_dir)
	terminator = Terminator(max_files=opts.max_files, timeout=opts.timeout, signals=opts.signal, pids=opts.pid, file_providers=[provider], merger=merger)
	provider.start()
	merger.start()
	terminator.start()
	try:
		while not merger.join(5):
			print  provider.report(), merger.report(), terminator.report()
	except KeyboardInterrupt:
		print "interrupt..."
		os._exit(1)
	print "done", "(%.2fs)" % (time.time() - start_time)
