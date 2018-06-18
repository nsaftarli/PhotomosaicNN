import tensorflow as tf
import numpy as np


def VarianceRegularizer(y_pred):
    bins = tf.reshape(np.linspace(1, 62, num=62).astype('float32'),
                      [1, 1, 1, 62])
    mean = tf.reduce_sum(bins * y_pred, axis=3)
    mean_2 = tf.reduce_sum(bins ** 2 * y_pred, axis=3)
    variance = mean_2 - mean ** 2
    return tf.reduce_mean(variance)


def EntropyRegularizer(y_pred):
    return tf.reduce_mean(-1.0 * tf.reduce_sum(y_pred * tf.log(y_pred + 1e-8),
                          axis=3))
