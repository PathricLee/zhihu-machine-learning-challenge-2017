#! /usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/21 23:54
# @Author  : HouJP
# @Email   : houjp1992@gmail.com


import ConfigParser
import os
import time
from os.path import isfile

import xgboost as xgb
from sklearn.externals import joblib
from sklearn.linear_model import LogisticRegression as skl_logistic_regression

from ..utils import LogUtil


class Model(object):
    valid_model_name = ['XGB']

    @staticmethod
    def new(model_name, config_fp):
        assert model_name in Model.valid_model_name, 'Wrong model_name(%s)' % model_name
        return eval(model_name)(config_fp)

    def __init__(self, config_fp):
        # load configuration file
        if isinstance(config_fp, str):
            self.config = ConfigParser.ConfigParser()
            self.config.read(config_fp)
        else:
            self.config = config_fp
        self.model = None

    def __load_parameters(self):
        assert False, 'Please override function: Model.__load_parameters()'

    def save(self, model_fp):
        assert False, 'Please override function: Model.save()'

    def load(self, model_fp):
        assert False, 'Please override function: Model.load()'

    def fit(self, train_fs, train_labels, valid_fs, valid_labels):
        assert False, 'Please override function: Model.fit()'

    def predict(self, features, labels=None):
        assert False, 'Please override function: Model.predict()'

    def __lock(self):
        lock_name = self.config.get('MODEL', 'lock_name')
        lock_time = self.config.getint('MODEL', 'lock_time')
        lock_pt = self.config.get('MODEL', 'lock_pt')
        if '' != lock_name:
            lock_fp = '%s/%s.lock' % (lock_pt, lock_name)
            while isfile(lock_fp):
                LogUtil.log('INFO', 'model is running, lock_name=%s, waiting %d ...' % (lock_name, lock_time))
                time.sleep(lock_time)
            f = open(lock_fp, 'w')
            f.close()
        LogUtil.log('INFO', 'generate lock, lock_name=%s' % lock_name)

    def __unlock(self):
        lock_name = self.config.get('MODEL', 'lock_name')
        lock_pt = self.config.get('MODEL', 'lock_pt')
        lock_fp = '%s/%s.lock' % (lock_pt, lock_name)
        if isfile(lock_fp):
            os.remove(lock_fp)
            LogUtil.log('INFO', 'delete lock, lock_name=%s' % lock_name)
        else:
            LogUtil.log('WARNING', 'missing lock, lock_name=%s' % lock_name)


class XGB(Model):
    def __init__(self, config_fp):
        Model.__init__(self, config_fp)
        self.params = self.__load_parameters()

    def __load_parameters(self):
        params = dict()
        params['booster'] = self.config.get('XGB_PARAMS', 'booster')
        params['objective'] = self.config.get('XGB_PARAMS', 'objective')
        params['eval_metric'] = self.config.get('XGB_PARAMS', 'eval_metric')
        params['eta'] = float(self.config.get('XGB_PARAMS', 'eta'))
        params['max_depth'] = self.config.getint('XGB_PARAMS', 'max_depth')
        params['subsample'] = float(self.config.get('XGB_PARAMS', 'subsample'))
        params['colsample_bytree'] = float(self.config.get('XGB_PARAMS', 'colsample_bytree'))
        params['min_child_weight'] = self.config.getint('XGB_PARAMS', 'min_child_weight')
        params['silent'] = self.config.getint('XGB_PARAMS', 'silent')
        params['num_round'] = self.config.getint('XGB_PARAMS', 'num_round')
        params['early_stop'] = self.config.getint('XGB_PARAMS', 'early_stop')
        params['nthread'] = self.config.getint('XGB_PARAMS', 'nthread')
        params['scale_pos_weight'] = float(self.config.get('XGB_PARAMS', 'scale_pos_weight'))
        params['gamma'] = float(self.config.get('XGB_PARAMS', 'gamma'))
        params['verbose_eval'] = self.config.getint('XGB_PARAMS', 'verbose_eval')
        return params

    def save(self, model_fp):
        self.model.save_model(model_fp)

    def load(self, model_fp):
        self.model = xgb.Booster(self.params)
        self.model.load_model(model_fp)

    def fit(self,
            train_fs, train_labels,
            valid_fs, valid_labels):
        rank_k = self.config.getint('RANK', 'rank_k')

        train_DMatrix = xgb.DMatrix(train_fs, label=train_labels)
        train_DMatrix.set_group([rank_k] * (len(train_labels) / rank_k))
        valid_DMatrix = xgb.DMatrix(valid_fs, label=valid_labels)
        valid_DMatrix.set_group([rank_k] * (len(valid_labels) / rank_k))

        watchlist = [(train_DMatrix, 'train'), (valid_DMatrix, 'valid')]
        # self.__lock()
        self.model = xgb.train(self.params,
                               train_DMatrix,
                               self.params['num_round'],
                               watchlist,
                               early_stopping_rounds=self.params['early_stop'],
                               verbose_eval=self.params['verbose_eval'])
        LogUtil.log('INFO', 'best_ntree_limit=%d' % self.model.best_ntree_limit)
        # self.__unlock()
        valid_preds = self.model.predict(valid_DMatrix, ntree_limit=self.model.best_ntree_limit)
        return valid_preds

    def predict(self, features, labels=None):
        preds = self.model.predict(xgb.DMatrix(features, label=labels), ntree_limit=self.model.best_ntree_limit)
        return preds

    def sort_features(self):
        find2score = self.model.get_fscore()

        # 加载特征
        fn2find = {}
        ind = 0
        feature_pt = self.config.get('DIRECTORY', 'feature_pt')
        feature_names = self.config.get('FEATURE', 'feature_selected').split()
        for fn in feature_names:
            f = open('%s/%s.%s.smat' % (feature_pt, fn, 'train'))
            line = f.readline()
            subs = line.strip().split()
            col_num = int(subs[1])
            f.close()
            for ind_0 in range(col_num):
                fn2find['%s_%d' % (fn, ind_0)] = 'f%d' % (ind + ind_0)
            ind += col_num

        fn2score = {}
        for fn in fn2find:
            find = fn2find[fn]
            score = find2score.get(find, 0)
            fn2score[fn] = score

        fn2score_sorted = sorted(fn2score.iteritems(), key=lambda d: d[1], reverse=True)
        for kv in fn2score_sorted:
            print '%s\t%d' % (kv[0], kv[1])

