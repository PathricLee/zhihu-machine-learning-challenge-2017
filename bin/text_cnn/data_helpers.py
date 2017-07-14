#! /usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/1 00:27
# @Author  : HouJP
# @Email   : houjp1992@gmail.com


import numpy as np
import math
from bin.utils import LogUtil


def load_embedding(file_path):
    emb_f = open(file_path, 'r')

    shape = emb_f.readline().strip()
    emb_num, emb_size = [int(x) for x in shape.split()]
    LogUtil.log('INFO', 'embedding_shape=(%d, %d)' % (emb_num, emb_size))

    emb_index = {}
    emb_matrix = [['0.'] * emb_size, ['0.'] * emb_size]

    for line in emb_f:
        subs = line.strip().split()
        word = subs[0]
        vec = subs[1:]
        emb_index[word] = len(emb_matrix)
        emb_matrix.append(vec)
    emb_matrix = np.asarray(emb_matrix, dtype='float32')

    return emb_index, emb_matrix


def parse_dataset_line(line, emb_index, class_num, title_length, content_length, reverse):
    line = line.strip('\n')
    part = line.split("\t")
    assert 4 == len(part)

    que_id = part[0]

    title_vec = [emb_index[x] if x in emb_index else 1 for x in part[1].split(',')]
    if not reverse:
        title_vec = title_vec + [0] * (title_length - len(title_vec)) if len(title_vec) < title_length \
            else title_vec[:title_length]
    else:
        title_vec = [0] * (title_length - len(title_vec)) + title_vec if len(title_vec) < title_length \
            else title_vec[-1 * title_length:]
    cont_vec = [emb_index[x] if x in emb_index else 1 for x in part[2].split(',')]
    if not reverse:
        cont_vec = cont_vec + [0] * (content_length - len(cont_vec)) if len(cont_vec) < content_length \
            else cont_vec[:content_length]
    else:
        cont_vec = [0] * (content_length - len(cont_vec)) + cont_vec if len(cont_vec) < content_length \
            else cont_vec[-1 * content_length:]
    label_vec = [0] * class_num
    if 0 != len(part[3].strip()):
        for label_id in part[3].split(','):
            label_vec[int(label_id)] = 1

    return que_id, title_vec, cont_vec, label_vec


def parse_doc_vec(line, emb_index, vec_length, reverse):
    vec = [emb_index[x] if x in emb_index else 1 for x in line.strip('\n').split(',')]
    if not reverse:
        vec = vec + [0] * (vec_length - len(vec)) if len(vec) < vec_length \
            else vec[:vec_length]
    else:
        vec = [0] * (vec_length - len(vec)) + vec if len(vec) < vec_length \
            else vec[-1 * vec_length:]
    return vec


def load_doc_vec(file_path, emb_index, vec_length, reverse):
    return [parse_doc_vec(line, emb_index, vec_length, reverse) for line in open(file_path).readlines()]


def parse_feature_vec(line):
    vec = [0. if math.isnan(float(num)) else float(num) for num in line.strip('\n').split()]
    return vec


def load_feature_vec(file_path):
    return [parse_feature_vec(line) for line in open(file_path).readlines()]


def parse_lid_vec(line, class_num):
    lid_vec = [0] * class_num
    for lid in line.strip('\n').split(','):
        lid_vec[int(lid)] = 1
    return lid_vec


def load_lid(file_path, class_num):
    return [parse_lid_vec(line, class_num) for line in open(file_path).readlines()]


def load_dataset(tc_vecs, tw_vecs, cc_vecs, cw_vecs, btm_vecs, lid_vecs, inds):
    sub_tc_vecs = None if tc_vecs is None else np.asarray([tc_vecs[ind] for ind in inds], dtype='int32')
    sub_tw_vecs = None if tw_vecs is None else np.asarray([tw_vecs[ind] for ind in inds], dtype='int32')
    sub_cc_vecs = None if cc_vecs is None else np.asarray([cc_vecs[ind] for ind in inds], dtype='int32')
    sub_cw_vecs = None if cw_vecs is None else np.asarray([cw_vecs[ind] for ind in inds], dtype='int32')
    sub_btm_vecs = None if btm_vecs is None else np.asarray([btm_vecs[ind] for ind in inds], dtype='float32')
    sub_lid_vecs = None if lid_vecs is None else np.asarray([lid_vecs[ind] for ind in inds], dtype='int32')
    return sub_tc_vecs, sub_tw_vecs, sub_cc_vecs, sub_cw_vecs, sub_btm_vecs, sub_lid_vecs


def load_dataset_loop(tc_vecs, tw_vecs, cc_vecs, cw_vecs, btm_vecs, lid_vecs, inds, part_size):
    count = 0
    inds_len = len(inds)
    inds_part = list()
    while True:
        count += 1
        inds_part.append(inds[count % inds_len])
        if 0 == count % part_size:
            yield load_dataset(tc_vecs, tw_vecs, cc_vecs, cw_vecs, btm_vecs, lid_vecs, inds_part)
            inds_part = list()


def load_doc_vec_part(file_path, emb_index, vec_length, reverse, inds):
    doc_vecs = list()

    inds.sort()
    index_f = 0
    index_inds = 0
    f = open(file_path, 'r')
    for line in f:
        if len(inds) <= index_inds:
            break
        if index_f == inds[index_inds]:
            doc_vecs.append(parse_doc_vec(line, emb_index, vec_length, reverse))
            index_inds += 1
        index_f += 1
    f.close()

    return doc_vecs


def load_feature_vec_part(file_path, inds):
    vecs = list()

    inds.sort()
    index_f = 0
    index_inds = 0
    f = open(file_path, 'r')
    for line in f:
        if len(inds) <= index_inds:
            break
        if index_f == inds[index_inds]:
            vecs.append(parse_feature_vec(line))
            index_inds += 1
        index_f += 1
    f.close()

    return vecs


def load_lid_part(file_path, class_num, inds):
    vecs = list()

    inds.sort()
    index_f = 0
    index_inds = 0
    f = open(file_path, 'r')
    for line in f:
        if len(inds) <= index_inds:
            break
        if index_f == inds[index_inds]:
            vecs.append(parse_lid_vec(line, class_num))
            index_inds += 1
        index_f += 1
    f.close()

    return vecs


def load_dataset_from_file(tc_fp, tw_fp, cc_fp, cw_fp,
                           tc_len, tw_len, cc_len, cw_len,
                           char_emb_index, word_emb_index,
                           btm_tw_cw_fp, btm_tc_fp,
                           lid_fp, class_num, inds):
    sub_tc_vecs = np.asarray(load_doc_vec_part(tc_fp, char_emb_index, tc_len, True, inds), dtype='int32')
    LogUtil.log('INFO', 'load title char vector done')
    sub_tw_vecs = np.asarray(load_doc_vec_part(tw_fp, word_emb_index, tw_len, False, inds), dtype='int32')
    LogUtil.log('INFO', 'load title word vector done')
    sub_cc_vecs = np.asarray(load_doc_vec_part(cc_fp, char_emb_index, cc_len, True, inds), dtype='int32')
    LogUtil.log('INFO', 'load content char vector done')
    sub_cw_vecs = np.asarray(load_doc_vec_part(cw_fp, word_emb_index, cw_len, False, inds), dtype='int32')
    LogUtil.log('INFO', 'load content word vector done')
    btm_tw_cw_vecs = np.asarray(load_feature_vec_part(btm_tw_cw_fp, inds), dtype='float32')
    LogUtil.log('INFO', 'load btm title word + content word vector done')
    btm_tc_vecs = np.asarray(load_feature_vec_part(btm_tc_fp, inds), dtype='float32')
    LogUtil.log('INFO', 'load btm title char vector done')
    sub_lid_vecs = None if lid_fp is None else np.asarray(load_lid_part(lid_fp, class_num, inds), dtype='int32')
    LogUtil.log('INFO', 'load label id vector done')

    return sub_tc_vecs, sub_tw_vecs, sub_cc_vecs, sub_cw_vecs, btm_tw_cw_vecs, btm_tc_vecs, sub_lid_vecs


def load_dataset_from_file_loop(tc_fp, tw_fp, cc_fp, cw_fp,
                                tc_len, tw_len, cc_len, cw_len,
                                char_emb_index, word_emb_index,
                                btm_tw_cw_fp, btm_tc_fp,
                                lid_fp, class_num, inds, part_size):
    inds.sort()

    inds_len = len(inds)

    sub_tc_vecs = list()
    sub_tw_vecs = list()
    sub_cc_vecs = list()
    sub_cw_vecs = list()

    sub_btm_tw_cw_vecs = list()
    sub_btm_tc_vecs = list()
    sub_lid_vecs = list()

    tc_f = open(tc_fp, 'r')
    tw_f = open(tw_fp, 'r')
    cc_f = open(cc_fp, 'r')
    cw_f = open(cw_fp, 'r')
    btm_tw_cw_f = open(btm_tw_cw_fp, 'r')
    btm_tc_f = open(btm_tc_fp, 'r')
    lid_f = open(lid_fp, 'r')

    index_f = 0
    index_inds = 0

    while True:

        if inds_len <= index_inds:
            tc_f.seek(0)
            tw_f.seek(0)
            cc_f.seek(0)
            cw_f.seek(0)
            btm_tw_cw_f.seek(0)
            btm_tc_f.seek(0)
            lid_f.seek(0)
            index_f = 0
            index_inds = 0

        tc_line = tc_f.readline()
        tw_line = tw_f.readline()
        cc_line = cc_f.readline()
        cw_line = cw_f.readline()
        btm_tw_cw_line = btm_tw_cw_f.readline()
        btm_tc_line = btm_tc_f.readline()
        lid_line = lid_f.readline()

        if index_f == inds[index_inds]:
            sub_tc_vecs.append(parse_doc_vec(tc_line, char_emb_index, tc_len, True))
            sub_tw_vecs.append(parse_doc_vec(tw_line, word_emb_index, tw_len, False))
            sub_cc_vecs.append(parse_doc_vec(cc_line, char_emb_index, cc_len, True))
            sub_cw_vecs.append(parse_doc_vec(cw_line, word_emb_index, cw_len, False))

            sub_btm_tw_cw_vecs.append(parse_feature_vec(btm_tw_cw_line))
            sub_btm_tc_vecs.append(parse_feature_vec(btm_tc_line))

            sub_lid_vecs.append(parse_lid_vec(lid_line, class_num))

            index_inds += 1
        index_f += 1

        if part_size == len(sub_lid_vecs):
            sub_tc_vecs = np.asarray(sub_tc_vecs, dtype='int32')
            sub_tw_vecs = np.asarray(sub_tw_vecs, dtype='int32')
            sub_cc_vecs = np.asarray(sub_cc_vecs, dtype='int32')
            sub_cw_vecs = np.asarray(sub_cw_vecs, dtype='int32')

            sub_btm_tw_cw_vecs = np.asarray(sub_btm_tw_cw_vecs, dtype='float32')
            sub_btm_tc_vecs = np.asarray(sub_btm_tc_vecs, dtype='float32')

            sub_lid_vecs = np.asarray(sub_lid_vecs, dtype='int32')
            yield sub_tc_vecs, sub_tw_vecs, sub_cc_vecs, sub_cw_vecs, sub_btm_tw_cw_vecs, sub_btm_tc_vecs, sub_lid_vecs

            sub_tc_vecs = list()
            sub_tw_vecs = list()
            sub_cc_vecs = list()
            sub_cw_vecs = list()
            sub_btm_tw_cw_vecs = list()
            sub_btm_tc_vecs = list()
            sub_lid_vecs = list()


if __name__ == '__main__':
    load_embedding(
        '/Users/houjianpeng/Github/zhihu-machine-learning-challenge-2017/data/embedding/word_embedding.txt.small')
