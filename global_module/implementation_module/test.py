import os
import random
import sys
import time

import numpy as np
import tensorflow as tf

from global_module.implementation_module import model
from global_module.implementation_module import reader
from global_module.settings_module import set_params, set_dir, set_dict

iter_train = 0
iter_valid = 0


def run_epoch(session, eval_op, model_obj, dict_obj, verbose=False):
    global summary, iter_train, iter_valid
    epoch_combined_loss = 0.0
    total_correct = 0.0
    total_instances = 0.0
    print('\nrun epoch')

    output_file = open(set_dir.Directory('TE').test_cost_path, 'w')

    params = model_obj.params
    dir_obj = model_obj.dir_obj
    data_filename = dir_obj.data_filename
    label_filename = dir_obj.label_filename

    for step, (ctx_arr, ctx_len_arr, num_ctx_arr, resp_arr, resp_len_arr, label_arr) \
            in enumerate(reader.data_iterator(params, data_filename, label_filename, model_obj.params.indices, dict_obj)):

        feed_dict = {model_obj.ctx: ctx_arr,
                     model_obj.ctx_len_placeholders: ctx_len_arr,
                     model_obj.num_ctx_placeholders: num_ctx_arr,
                     model_obj.resp: resp_arr,
                     model_obj.resp_len_placeholders: resp_len_arr,
                     model_obj.label: label_arr
                     }

        loss, prediction, probabilities, accuracy, _ = session.run([model_obj.loss,
                                                                    model_obj.prediction,
                                                                    model_obj.probabilities,
                                                                    model_obj.accuracy,
                                                                    eval_op],
                                                                   feed_dict=feed_dict)

        total_correct += np.sum(prediction == label_arr)
        total_instances += params.batch_size
        epoch_combined_loss += loss

        for idx, each_pred in enumerate(probabilities):
            # output_file.write(str(each_pred) + '\t'  + str(probabilities[idx]) + '\n')
            output_file.write(str(each_pred[1]) + '\n')
    print 'CE loss: %.4f, Accuracy: %.4f' % (epoch_combined_loss, (total_correct / total_instances) * 100)
    return epoch_combined_loss


def get_length(filename):
    print('Reading :', filename)
    data_file = open(filename, 'r')
    count = 0
    for _ in data_file:
        count += 1
    data_file.close()
    return count, np.arange(count)


def init_test(dict_obj):
    mode_train, mode_test = 'TR', 'TE'

    params_train = set_params.ParamsClass(mode=mode_train)
    dir_train = set_dir.Directory(mode_train)

    # test object

    params_test = set_params.ParamsClass(mode=mode_test)
    dir_test = set_dir.Directory(mode_test)
    params_test.num_instances, params_test.indices = get_length(dir_test.data_filename)
    # params_test.batch_size = 1

    params_train.num_classes = params_test.num_classes = len(dict_obj.label_dict)

    min_loss = sys.float_info.max

    word_emb_path = dir_train.word_embedding
    word_emb_matrix = np.float32(np.genfromtxt(word_emb_path, delimiter=' '))
    params_train.vocab_size = params_test.vocab_size = len(word_emb_matrix)

    print('***** INITIALIZING TF GRAPH *****')

    session = tf.Session()
    # train_writer = tf.summary.FileWriter(dir_train.log_path + '/train', session.graph)
    # test_writer = tf.summary.FileWriter(dir_train.log_path + '/test')

    # random_uniform_initializer = tf.random_uniform_initializer(-params_train.init_scale, params_train.init_scale)
    # xavier_initializer = tf.contrib.layers.xavier_initializer(uniform=True, seed=None, dtype=tf.float32)

    with tf.variable_scope("classifier", reuse=None):
        test_obj = model.SMN(params_test, dir_test)

    model_saver = tf.train.Saver()
    print('Loading model ...')
    model_saver.restore(session, set_dir.Directory('TE').test_model)

    print('**** MODEL LOADED ****\n')

    return session, test_obj


def run_test(session, test_obj, dict_obj):
    start_time = time.time()

    print("Starting test computation\n")
    test_loss = run_epoch(session, tf.no_op(), test_obj, dict_obj)

    curr_time = time.time()
    print('1 epoch run takes ' + str(((curr_time - start_time) / 60)) + ' minutes.')

# def main():
#     dict_obj = set_dict.Dictionary()
#     run_test(dict_obj)
#
#
# if __name__ == "__main__":
#     main()
