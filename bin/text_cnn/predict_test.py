#! /usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/2 16:52
# @Author  : HouJP
# @Email   : houjp1992@gmail.com


import ConfigParser
import json
import sys

from data_helpers import *
from ..utils import DataUtil
from .clayers.Scale import Scale
from keras.models import model_from_json


def save_prediction(pred_fp, preds, id2label, que_ids_test):
    pred_f = open(pred_fp, 'w')
    for line_id, p in enumerate(preds):
        label_id_sorted = sorted(list(enumerate(p)), key=lambda s: s[1], reverse=True)
        label_sorted = [id2label[str(kv[0])] for kv in label_id_sorted[:5]]
        pred_f.write("%s,%s\n" % (que_ids_test[line_id], ','.join(label_sorted)))
        if 0 == line_id % 10000:
            LogUtil.log('INFO', '%d lines prediction done' % line_id)
    pred_f.close()

    pred_all_f = open(pred_fp + '.all', 'w')
    for p in preds:
        pred_all_f.write('%s\n' % ','.join([str(num) for num in p]))
    pred_all_f.close()


def predict_test(config, part_id):
    LogUtil.log('INFO', 'part_id=%d' % part_id)

    version = config.get('TITLE_CONTENT_CNN', 'version')
    text_cnn = __import__('bin.text_cnn.%s.text_cnn' % version, fromlist = ["*"])
    data_loader = __import__('bin.text_cnn.%s.data_loader' % version, fromlist = ["*"])
    LogUtil.log('INFO', 'version=%s' % version)

    # init text cnn model
    model, word_embedding_index, char_embedding_index = text_cnn.init_text_cnn(config)

    # load question ID for online dataset
    qid_on_fp = '%s/%s.online.csv' % (config.get('DIRECTORY', 'dataset_pt'), 'question_id')
    qid_on = DataUtil.load_vector(qid_on_fp, 'str')
    LogUtil.log('INFO', 'load online question ID done')

    # load hash table of label
    id2label_fp = '%s/%s' % (config.get('DIRECTORY', 'hash_pt'), config.get('TITLE_CONTENT_CNN', 'id2label_fn'))
    id2label = json.load(open(id2label_fp, 'r'))

    ### load model
    ##model_fp = config.get('DIRECTORY', 'model_pt') + 'text_cnn_%03d' % part_id
    ##model.load(model_fp, {'Scale':Scale})
    # load model
    model_fp = config.get('DIRECTORY', 'model_pt') + 'text_cnn_%03d' % part_id
    # load json and create model
    json_file = open('%s.json' % model_fp, 'r')
    model_json = json_file.read()
    json_file.close()
    model = model_from_json(model_json, {'Scale':Scale})
    # load weights into new model
    model.load_weights('%s.h5' % model_fp)
    LogUtil.log('INFO', 'load model (%s) from disk done' % model_fp)

    # load test data set
    test_dataset = data_loader.load_dataset_from_file(config,
                                                      'online',
                                                      word_embedding_index,
                                                      char_embedding_index,
                                                      range(len(qid_on)))
    # predict for test data set
    test_preds = model.predict(test_dataset[:-1], batch_size=32, verbose=True)
    LogUtil.log('INFO', 'prediction of online data, shape=%s' % str(test_preds.shape))
    # save prediction
    pred_fp = '%s/pred.csv.%d' % (config.get('DIRECTORY', 'pred_pt'), part_id)
    save_prediction(pred_fp, test_preds, id2label, qid_on)


if __name__ == '__main__':
    config_fp = sys.argv[1]
    part_id = int(sys.argv[2])
    config = ConfigParser.ConfigParser()
    config.read(config_fp)

    predict_test(config, part_id)
