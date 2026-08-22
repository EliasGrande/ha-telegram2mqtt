#!/usr/bin/env python

import logging
import signal
import sys
import threading
from logging_setup import get_logger

LOGGER = get_logger('lifecycle')


class SigtermInterrupt(Exception):
  @staticmethod
  def handle(_signo, _stack_frame):
    raise SigtermInterrupt


class Disposable:

  _disposable_instances = []
  _disposing_all = False
  _lock = threading.Lock()

  def __init__(self, name):
    self._disposed = False
    self._disposing = False
    self.name = name
    Disposable._disposable_instances.append(self)

  def _dispose(self):
    pass

  def dispose(self):
    Disposable._lock.acquire()
    if self._disposed:
      return
    LOGGER.debug(f'Disposing {self.name}')
    self._disposing = True
    try:
      self._dispose()
    except:
      LOGGER.exception('Dispose failed')
    self._disposing = False
    self._disposed = True
    if not Disposable._disposing_all:
      Disposable._disposable_instances.remove(self)
    Disposable._lock.release()

  @staticmethod
  def dispose_all():
    LOGGER.debug('Disposing all...')
    Disposable._disposing_all = True
    for x in Disposable._disposable_instances:
      x.dispose()
    Disposable._disposable_instances = []
    Disposable._disposing_all = False
    LOGGER.debug('All disposed')


CLEANUP_BEFORE_EXIT_CALLED = False


def cleanup_before_exit():
  global CLEANUP_BEFORE_EXIT_CALLED
  if CLEANUP_BEFORE_EXIT_CALLED:
    return
  CLEANUP_BEFORE_EXIT_CALLED = True
  Disposable.dispose_all()


def exit_app(exit_code=0):
  cleanup_before_exit()
  sys.exit(exit_code)


def register_sigterm_handler():
  signal.signal(signal.SIGTERM, SigtermInterrupt.handle)
