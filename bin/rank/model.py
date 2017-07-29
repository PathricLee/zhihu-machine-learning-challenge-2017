#! /usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/30 00:33
# @Author  : HouJP
# @Email   : houjp1992@gmail.com


import xgboost as xgb
import sys
import ConfigParser
from ..utils import DataUtil


def load_parameters(config):
    params = dict()
    params['booster'] = config.get('XGB_PARAMS', 'booster')
    params['objective'] = config.get('XGB_PARAMS', 'objective')
    params['eval_metric'] = config.get('XGB_PARAMS', 'eval_metric')
    params['eta'] = float(config.get('XGB_PARAMS', 'eta'))
    params['max_depth'] = config.getint('XGB_PARAMS', 'max_depth')
    params['subsample'] = float(config.get('XGB_PARAMS', 'subsample'))
    params['colsample_bytree'] = float(config.get('XGB_PARAMS', 'colsample_bytree'))
    params['min_child_weight'] = config.getint('XGB_PARAMS', 'min_child_weight')
    params['silent'] = config.getint('XGB_PARAMS', 'silent')
    params['num_round'] = config.getint('XGB_PARAMS', 'num_round')
    params['early_stop'] = config.getint('XGB_PARAMS', 'early_stop')
    params['nthread'] = config.getint('XGB_PARAMS', 'nthread')
    params['scale_pos_weight'] = float(config.get('XGB_PARAMS', 'scale_pos_weight'))
    params['gamma'] = float(config.get('XGB_PARAMS', 'gamma'))
    # params['alpha'] = float(config.get('XGB_PARAMS', 'alpha'))
    # params['lambda'] = float(config.get('XGB_PARAMS', 'lambda'))
    params['verbose_eval'] = config.getint('XGB_PARAMS', 'verbose_eval')
    return params


def stand_path(s):
    return '/' + '/'.join(filter(None, s.split('/')))


def train(config, argv):
    dtrain_fp = stand_path('%s/%s_train.libsvm' % (config.get('DIRECTORY', 'dataset_pt'), config.get('RANK', 'dmatrix_name')))
    group_train_fp = dtrain_fp + '.group'
    dtrain = xgb.DMatrix(dtrain_fp)
    dtrain.set_group(DataUtil.load_vector(group_train_fp, 'int'))

    dvalid_fp = stand_path('%s/%s_valid.libsvm' % (config.get('DIRECTORY', 'dataset_pt'), config.get('RANK', 'dmatrix_name')))
    group_valid_fp = dvalid_fp + '.group'
    dvalid = xgb.DMatrix(dvalid_fp)
    dvalid.set_group(DataUtil.load_vector(group_valid_fp, 'int'))

    watchlist = [(dtrain, 'train'), (dvalid, 'valid')]
    params = load_parameters(config)
    model = xgb.train(params,
                      dtrain,
                      params['num_round'],
                      watchlist,
                      early_stopping_rounds=params['early_stop'],
                      verbose_eval=params['verbose_eval'])


if __name__ == '__main__':
    config_fp = sys.argv[1]
    config = ConfigParser.ConfigParser()
    config.read(config_fp)
    func = sys.argv[2]
    argv = sys.argv[3:]

    eval(func)(config, argv)
