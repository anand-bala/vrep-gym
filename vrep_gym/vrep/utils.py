# import the vrep library
try:
    from . import vrep
except Exception:
    print('--------------------------------------------------------------')
    print('"vrep.py" could not be imported. This means very probably that')
    print('either "vrep.py" or the remoteApi library could not be found.')
    print('Make sure both are in the same folder as this file,')
    print('or appropriately adjust the file "vrep.py"')
    print('--------------------------------------------------------------')
    print('')
    raise

import atexit
import logging
import subprocess as sp
from collections import deque

PROC_LIST = deque()


@atexit.register
def cleanup():
    global PROC_LIST
    for p in PROC_LIST:  # type: _ProcInstance
        p.end()


log = logging.getLogger('VREP.API')


@atexit.register
def cleanup():
    global PROC_LIST
    for p in PROC_LIST:  # type: _ProcInstance
        p.end()


class _ProcInstance:
    def __init__(self, args):
        self.args = args
        self.inst = None
        PROC_LIST.append(self)

    def start(self):
        log.info('Starting V-REP Instance...')
        try:
            self.inst = sp.Popen(self.args)
        except EnvironmentError:
            log.error('Launching Instance, cannot find executable at', self.args[0])
            raise

        return self

    def is_alive(self):
        return True if self.inst.poll() is None else False

    def end(self):
        log.info('Terminating V-REP Instance...')
        if self.is_alive():
            self.inst.terminate()
            retcode = self.inst.wait()
        else:
            retcode = self.inst.returncode
        log.info('V-REP Instance exited with code:', retcode)
        return self


def check_ret(ret_tuple, ignore_one=False):
    """
    check return tuple, raise error if retcode is not OK,
    return remaining data otherwise
    :param ret_tuple:
    :param ignore_one:
    :return:
    """
    istuple = isinstance(ret_tuple, tuple)
    if not istuple:
        ret = ret_tuple
    else:
        ret = ret_tuple[0]

    if (not ignore_one and ret != vrep.simx_return_ok) or (ignore_one and ret > 1):
        raise RuntimeError('Return code(' + str(ret) + ') not OK, API call failed. Check the parameters!')

    return ret_tuple[1:] if istuple else None


class SimOpModes:
    # TODO: Fill out the OpModes?
    oneshot = vrep.simx_opmode_oneshot  #: Send/Recv 1 chunk (Async)
    blocking = vrep.simx_opmode_blocking  #: Send/Recv 1 chunk (Sync)

    oneshot_wait = vrep.simx_opmode_oneshot_wait
    continuous = vrep.simx_opmode_continuous
    streaming = vrep.simx_opmode_streaming

    oneshot_split = vrep.simx_opmode_oneshot_split
    continuous_split = vrep.simx_opmode_continuous_split
    streaming_split = vrep.simx_opmode_streaming_split

    # Special operation modes
    discontinue = vrep.simx_opmode_discontinue
    buffer = vrep.simx_opmode_buffer
    remove = vrep.simx_opmode_remove
