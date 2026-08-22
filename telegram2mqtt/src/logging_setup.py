#!/usr/bin/env python

import copy
import json
import logging
import os

LOGGER_BASE_NAME = 'telegram2mqtt'


def get_logger(module_name: str = None) -> logging.Logger:
  if module_name is None:
    return logging.getLogger(LOGGER_BASE_NAME)
  return logging.getLogger(f'{LOGGER_BASE_NAME}.{module_name}')


def configure_logging(config_dict: dict, debug_enabled: bool, mask_passwords_fn):
  logging.basicConfig(
    level=logging.WARNING,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
  )
  # logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(message)s',)
  # logging.basicConfig(level=logging.WARNING, format='%(message)s',)

  logger = get_logger()
  logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
  logger.info('Starting')

  if debug_enabled:
    print()
    logger.debug('ENVIRONMENT:')
    print(json.dumps(mask_passwords_fn(dict(os.environ)), indent=4))
    logger.debug('OPTIONS:')
    print(json.dumps(mask_passwords_fn(copy.deepcopy(config_dict)), indent=4))
    print()

  return logger
