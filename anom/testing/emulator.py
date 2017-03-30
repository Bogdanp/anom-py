import logging
import os
import re
import signal
import shlex
import subprocess

from queue import Empty, Queue
from threading import Thread


#: The command to run in order to start the emulator.
_emulator_command = "gcloud beta emulators datastore start --consistency={consistency:0.2f} --no-store-on-disk"

#: The regexp that is used to search for env vars in the emulator output.
_env_var_re = re.compile(r"export ([^=]+)=(.+)")

#: The string that is used to determine when the Emulator has finished starting up.
_log_marker = "Dev App Server is now running"


class Emulator:
    """Runs the Cloud Datastore emulator in a subprocess for testing purposes.

    Parameters:
      consistency(float): A value between 0.0 and 1.0 representing the
        percentage of datastore requests that should succeed.

    Example::

      from anom.testing import Emulator

      @pytest.fixture(scope="session")
      def emulator():
        emulator = Emulator()
        emulator.start(inject=True)
        yield
        emulator.stop()
    """

    def __init__(self, *, consistency=1):
        self._emulator_command = shlex.split(_emulator_command.format(
            consistency=consistency
        ))

        self._logger = logging.getLogger("Emulator")
        self._proc = None
        self._queue = Queue()
        self._thread = Thread(target=self._run, daemon=True)

    def start(self, *, timeout=15, inject=False):
        """Start the emulator process and wait for it to initialize.

        Parameters:
          timeout(int): The maximum number of seconds to wait for the
            Emulator to start up.
          inject(bool): Whether or not to inject the emulator env vars
            into the current process.

        Returns:
          dict: A dictionary of env vars that can be used to access
          the Datastore emulator.
        """
        try:
            self._thread.start()

            env_vars = self._queue.get(block=True, timeout=timeout)
            if inject:
                os.environ.update(env_vars)

            return env_vars
        except Empty:  # pragma: no cover
            raise RuntimeError("Timed out while waiting for Emulator to start up.")

    def stop(self):
        """Stop the emulator process.

        Returns:
          int: The process return code or None if the process isn't
          currently running.
        """
        if self._proc is not None:
            if self._proc.poll() is None:
                os.killpg(self._proc.pid, signal.SIGTERM)
                _, returncode = os.waitpid(self._proc.pid, 0)
                self._logger.debug("Emulator process exited with code %d.", returncode)
                return returncode
            return self._proc.returncode  # pragma: no cover
        return None  # pragma: no cover

    def _run(self):
        self._proc = subprocess.Popen(
            self._emulator_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )

        env_vars = {}
        while self._proc.poll() is None:
            line = self._proc.stdout.readline().strip().decode("utf-8")
            self._logger.debug(line)

            match = _env_var_re.search(line)
            if match:
                name, value = match.groups()
                env_vars[name] = value

            # If no env vars were found this will eventually cause
            # `start` to time out which is what we want since running
            # tests w/o the env vars set up could prove dangerous.
            if _log_marker in line and env_vars:
                self._queue.put(env_vars)
