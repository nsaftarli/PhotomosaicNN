import tensorflow as tf
import numpy as np
from layers import *
from utils import *
from VGG16 import *


'''Data constants'''
const = constants.Constants()
img_data_dir = const.img_data_dir
ascii_data_dir = const.ascii_data_dir
val_data_dir = const.val_data_dir
char_array = const.char_array
char_dict = const.char_dict
img_rows = const.img_rows
img_cols = const.img_cols
text_rows = const.text_rows
text_cols = const.text_cols
dims = const.char_count
experiments_dir = const.experiments_dir
coco_dir = const.coco_dir
img_new_size = const.img_new_size
patch_size = const.patch_size
num_patches = const.num_patches





VGG_MEAN = [103.939, 116.779, 123.68]
NUM_TEMPLATES = 62
PATCH_SIZE = 8
IM_SHAPE = 512
norm_type = 'group'

w = tf.reshape(tf.constant(gauss2d_kernel(shape=(patch_size, patch_size), sigma=3), dtype=tf.float32),
               [patch_size, patch_size, 1, 1])


class ASCIINet:

    def __init__(self,
                 images,
                 templates,
                 weight_path='./weights/vgg16.npy',
                 batch_size=6,
                 trainable=True,
                 rgb=False):
        self.net = self.build_network(images, templates, batch_size=batch_size, trainable=trainable, rgb=rgb)

    def build_network(self, input, templates, batch_size, trainable, rgb):

        self.input = tf.image.resize_images(input, [IM_SHAPE, IM_SHAPE], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

        # Get grayscale version of image
        with tf.name_scope('grayscale_input'):
            # self.gray_input = tf.tile(tf.reduce_mean(self.input, axis=-1, keep_dims=True), [1, 1, 1, 3])
            self.gray_input = rgb_to_gray(input)

        # ################Encoder##################################################################################
        with tf.name_scope('VGG_Encoder'):
            self.encoder = VGG16(input=self.input)
            self.decoder_in = self.encoder.pool3

        # ################Decoder##################################################################################
        with tf.name_scope("Decoder"):
            self.conv6, _ = ConvLayer(self.decoder_in, name='conv6', ksize=1, stride=1, out_channels=4096,  norm_type=norm_type, trainable=trainable)
            self.conv7, _ = ConvLayer(self.conv6, name='conv7', ksize=1, stride=1, out_channels=1024,  norm_type=norm_type, trainable=trainable)
            self.conv8, _ = ConvLayer(self.conv7, name='conv8', ksize=1, stride=1, out_channels=512,  norm_type=norm_type, trainable=trainable)
            self.conv9, _ = ConvLayer(self.conv8, name='conv9', ksize=1, stride=1, out_channels=256,  norm_type=norm_type, trainable=trainable)
            self.conv10, _ = ConvLayer(self.conv9, name='conv10', ksize=1, stride=1, out_channels=128,  norm_type=norm_type, trainable=trainable)
            self.conv11, _ = ConvLayer(self.conv10, name='conv11', ksize=1, stride=1, out_channels=64,  norm_type=norm_type, trainable=trainable)
            self.conv12, _ = ConvLayer(self.conv11, name='conv12', ksize=1, stride=1, out_channels=NUM_TEMPLATES,  norm_type=norm_type, trainable=trainable, layer_type='Softmax')

        # ################Other Inputs#############################################################################
        self.temp = tf.placeholder(tf.float32, shape=[])
        if not rgb:
            self.template_tensor = TemplateLayer(templates, rgb=False)
        else:
            self.r, self.g, self.b = TemplateLayer(templates, rgb=True, new_size=patch_size)
            r = tf.expand_dims(self.r, axis=3)
            g = tf.expand_dims(self.g, axis=3)
            b = tf.expand_dims(self.b, axis=3)
        self.temps = tf.concat([r, g, b], axis=3)
        # #################Colour templates##############################
        self.r = tf.transpose(tf.reshape(self.r, [-1, patch_size ** 2, NUM_TEMPLATES]), perm=[0, 2, 1])
        self.r = tf.tile(self.r, [batch_size, 1, 1])

        self.g = tf.transpose(tf.reshape(self.g, [-1, patch_size ** 2, NUM_TEMPLATES]), perm=[0, 2, 1])
        self.g = tf.tile(self.g, [batch_size, 1, 1])

        self.b = tf.transpose(tf.reshape(self.b, [-1, patch_size ** 2, NUM_TEMPLATES]), perm=[0, 2, 1])
        self.b = tf.tile(self.b, [batch_size, 1, 1])

        ##########################################################################################################

        # ###############Softmax###################################################################################
        self.softmax = tf.nn.softmax(self.conv12 * self.temp)
        self.softmax_size = self.softmax.get_shape().as_list()[1]
        self.reshaped_softmax = tf.reshape(self.softmax,[-1, self.softmax_size ** 2, NUM_TEMPLATES])
        print('****************************')
        print(self.softmax.get_shape())
        print(self.r.get_shape())
        print(self.reshaped_softmax.get_shape())
        print('*********************************')
        ##########################################################################################################

        ###############Output#####################################################################################
        with tf.name_scope('output_and_tile'):
            self.output_r = tf.matmul(self.reshaped_softmax, self.r)
            print(self.output_r.get_shape())
            self.output_r = tf.reshape(tf.transpose(tf.reshape(
                self.output_r, [batch_size, self.softmax_size, self.softmax_size, patch_size, patch_size]),
                perm=[0, 1, 3, 2, 4]), [batch_size, IM_SHAPE * 2, IM_SHAPE * 2, 1])

            self.output_g = tf.matmul(self.reshaped_softmax, self.g)
            self.output_g = tf.reshape(tf.transpose(tf.reshape(
                self.output_g, [batch_size, self.softmax_size, self.softmax_size, patch_size, patch_size]),
                perm=[0, 1, 3, 2, 4]), [batch_size, IM_SHAPE * 2, IM_SHAPE * 2, 1])

            self.output_b = tf.matmul(self.reshaped_softmax, self.b)
            self.output_b = tf.reshape(tf.transpose(tf.reshape(
                self.output_b, [batch_size, self.softmax_size, self.softmax_size, patch_size, patch_size]),
                perm=[0, 1, 3, 2, 4]), [batch_size, IM_SHAPE * 2, IM_SHAPE * 2, 1])

        with tf.name_scope('soft_output'):
            self.view_output = tf.concat([self.output_r, self.output_g, self.output_b], axis=3)

        with tf.name_scope('blurred_out'):
            self.blurred_out = self.blur_recombine(self.view_output, w, stride=2)

        ##########################################################################################################

        ################Gaussian Pyramid###########################################################################
        self.in_d1 = self.blur_recombine(self.input, w, stride=2)
        self.in_d2 = self.blur_recombine(self.in_d1, w, stride=2)
        self.out_d1 = self.blur_recombine(self.blurred_out, w, stride=2)
        self.out_d2 = self.blur_recombine(self.out_d1, w, stride=2)

        # ##############Loss and Regularizers######################################################################
        with tf.name_scope('multiscale_structure_features'):
            self.vgg2 = VGG16(input=self.blurred_out, trainable=False)

            self.vgg_in_d1 = VGG16(input=self.in_d1, trainable=False)
            self.vgg_in_d2 = VGG16(input=self.in_d2, trainable=False)
            self.vgg_out_d1 = VGG16(input=self.out_d1, trainable=False)
            self.vgg_out_d2 = VGG16(input=self.out_d2, trainable=False)

        ################Structure Loss############################################################################
        self.f_loss1 = tf.losses.mean_squared_error(self.encoder.conv1_1, self.vgg2.conv1_1)
        self.f_loss2 = tf.losses.mean_squared_error(self.encoder.conv2_1, self.vgg2.conv2_1)
        self.f_loss3 = tf.losses.mean_squared_error(self.encoder.conv3_1, self.vgg2.conv3_1)
        self.f_loss4 = tf.losses.mean_squared_error(self.encoder.conv4_1, self.vgg2.conv4_1)
        self.f_loss5 = tf.losses.mean_squared_error(self.encoder.conv5_1, self.vgg2.conv5_1)

        self.blur_loss = (tf.losses.mean_squared_error(self.vgg_in_d1.conv1_1, self.vgg_out_d1.conv1_1)) + \
                         (tf.losses.mean_squared_error(self.vgg_in_d1.conv2_1, self.vgg_out_d1.conv2_1)) + \
                         (tf.losses.mean_squared_error(self.vgg_in_d2.conv1_1, self.vgg_out_d2.conv1_1)) + \
                         (tf.losses.mean_squared_error(self.vgg_in_d2.conv2_1, self.vgg_out_d2.conv2_1))
        self.structure_loss = self.f_loss1 + self.f_loss2 + self.f_loss3 + self.f_loss4 + self.f_loss5 #+ self.blur_loss
        ###########################################################################################################
        self.tLoss = self.structure_loss + self.blur_loss
        ##########################################################################################################

        self.entropy = EntropyRegularizer(self.softmax) * 1e3
        self.variance = VarianceRegularizer(self.softmax, num_temps=NUM_TEMPLATES) * 1e2
        self.build_summaries()


    def get_avg_colour(self, input):
        return tf.nn.avg_pool(input, ksize=[1, patch_size, patch_size, 1], strides=[1, patch_size, patch_size, 1], padding='VALID')


    def build_summaries(self):
        tf.summary.image('target', tf.cast(self.input, tf.uint8), max_outputs=6)
        tf.summary.image('output', tf.cast(self.view_output, tf.uint8), max_outputs=6)
        # tf.summary.image('downsampled_in', self.im1)
        # tf.summary.image('downsampled_out', self.im2)
        # tf.summary.image('blurred_out', self.blurred_out)

        tf.summary.scalar('entropy', self.entropy)
        tf.summary.scalar('variance', self.variance)
        tf.summary.scalar('temperature', self.temp)
        # tf.summary.scalar('vgg_loss', self.loss)
        tf.summary.scalar('total_loss', self.tLoss)
        tf.summary.scalar('Struct_loss', self.structure_loss)
        # tf.summary.scalar('Colour_loss', self.colour_loss)

        # tf.summary.image('e_1', tf.reduce_mean(self.encoder.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('e_2', tf.reduce_mean(self.encoder.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('e_3', tf.reduce_mean(self.encoder.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('e_4', tf.reduce_mean(self.encoder.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('e_5', tf.reduce_mean(self.encoder.conv5_1, axis=-1, keep_dims=True))

        # tf.summary.image('v_1', tf.reduce_mean(self.vgg2.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('v_2', tf.reduce_mean(self.vgg2.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('v_3', tf.reduce_mean(self.vgg2.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('v_4', tf.reduce_mean(self.vgg2.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('v_5', tf.reduce_mean(self.vgg2.conv5_1, axis=-1, keep_dims=True))





        # tf.summary.image('downsample_target_conv_1', tf.reduce_mean(self.vgg4.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_target_conv_2', tf.reduce_mean(self.vgg4.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_target_conv_3', tf.reduce_mean(self.vgg4.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_target_conv_4', tf.reduce_mean(self.vgg4.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_target_conv_5', tf.reduce_mean(self.vgg4.conv5_1, axis=-1, keep_dims=True))

        # tf.summary.image('downsample_output_conv_1', tf.reduce_mean(self.vgg5.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_output_conv_2', tf.reduce_mean(self.vgg5.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_output_conv_3', tf.reduce_mean(self.vgg5.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_output_conv_4', tf.reduce_mean(self.vgg5.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample_output_conv_5', tf.reduce_mean(self.vgg5.conv5_1, axis=-1, keep_dims=True))

        # tf.summary.image('downsample2_target', self.im3)
        # tf.summary.image('downsample2_target_conv_1', tf.reduce_mean(self.vgg6.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_target_conv_2', tf.reduce_mean(self.vgg6.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_target_conv_3', tf.reduce_mean(self.vgg6.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_target_conv_4', tf.reduce_mean(self.vgg6.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_target_conv_5', tf.reduce_mean(self.vgg6.conv5_1, axis=-1, keep_dims=True))

        # tf.summary.image('downsample2_output', self.im4)
        # tf.summary.image('downsample2_output_conv_1', tf.reduce_mean(self.vgg7.conv1_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_output_conv_2', tf.reduce_mean(self.vgg7.conv2_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_output_conv_3', tf.reduce_mean(self.vgg7.conv3_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_output_conv_4', tf.reduce_mean(self.vgg7.conv4_1, axis=-1, keep_dims=True))
        # tf.summary.image('downsample2_output_conv_5', tf.reduce_mean(self.vgg7.conv5_1, axis=-1, keep_dims=True))

        self.summaries = tf.summary.merge_all()

    def blur_recombine(self, input, w, stride=1):
        with tf.name_scope('input'):
            r, g, b = tf.split(input, 3, axis=3)
            r = tf.nn.conv2d(r, w, strides=[1, stride, stride, 1], padding='SAME')
            g = tf.nn.conv2d(g, w, strides=[1, stride, stride, 1], padding='SAME')
            b = tf.nn.conv2d(b, w, strides=[1, stride, stride, 1], padding='SAME')

            return tf.concat([r, g, b], axis=3)






    def print_architecture(self):
        print(self.conv1_1.get_shape())
        print(self.conv1_2.get_shape())
        # print(self.pool1.get_shape())
        print(self.conv2_1.get_shape())
        print(self.conv2_2.get_shape())
        # print(self.pool2.get_shape())
        print(self.conv3_1.get_shape())
        print(self.conv3_2.get_shape())
        print(self.conv3_3.get_shape())
        # print(self.pool3.get_shape())
        print(self.conv4_1.get_shape())
        print(self.conv4_2.get_shape())
        print(self.conv4_3.get_shape())
        # print(self.pool4.get_shape())
        print(self.conv5_1.get_shape())
        print(self.conv5_2.get_shape())
        print(self.conv5_3.get_shape())
        # print(self.pool5.get_shape())

        print('################################')
        # print(self.up6.get_shape())
        print(self.conv6_1.get_shape())
        print(self.conv6_2.get_shape())
        print(self.conv6_3.get_shape())
        print(self.conv7_3.get_shape())
        print(self.conv7_2.get_shape())
        print(self.conv7_3.get_shape())
        print(self.conv8_1.get_shape())
        print(self.conv8_2.get_shape())
        print(self.conv8_3.get_shape())
        print(self.conv9_1.get_shape())
        print(self.conv9_2.get_shape())
        # print(self.conv9_3.get_shape())
        print(self.conv10_1.get_shape())
        print(self.conv10_2.get_shape())
        print(self.softmax.get_shape())
        # print(self.prediction.get_shape())
        print(self.flat_softmax.get_shape())
        print(self.r.get_shape())
        print(self.conv11.get_shape())
        # print(self.tloss.get_shape())
        print(tf.trainable_variables())


if __name__ == '__main__':
    m = ASCIINet()