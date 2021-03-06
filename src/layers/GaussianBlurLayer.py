import tensorflow as tf
from src.utils import gauss2d_kernel


def GaussianBlurLayer(input, name, k_h, k_w, stride=1, sigma=1):
    with tf.name_scope(name):
        blur_kernel = gauss2d_kernel(shape=(k_h, k_w), sigma=sigma)
        blur_kernel = tf.reshape(tf.constant(blur_kernel, dtype=tf.float32),
                                 [k_h, k_w, 1, 1])
        blur_kernel = tf.tile(blur_kernel, [1, 1, 3, 1])
        return tf.nn.depthwise_conv2d(input, blur_kernel, strides=[1, stride, stride, 1], padding='SAME')
