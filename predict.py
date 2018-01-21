import tensorflow as tf 
from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.visible_device_list = "0"
set_session(tf.Session(config=config))

from keras import models
from keras.preprocessing import image 
from keras.models import Model 
import keras.backend as K 
import numpy as np 
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt 
import imgdata as im 
from PIL import Image

img_data_dir = '/home/nsaftarl/Documents/ascii-art/ASCIIArtNN/assets/rgb_in/img_celeba/'
# ascii_data_dir = '/home/nsaftarl/Documents/ascii-art/ASCIIArtNN/assets/ascii_out/'
ascii_data_dir = '/home/nsaftarl/Documents/ascii-art/ASCIIArtNN/assets/ssim_imgs/'


# def weighted_categorical_crossentropy(w):
def loss(y_true, y_pred):
    y_pred /= K.sum(y_pred, axis=-1, keepdims=True)
    y_pred = K.clip(y_pred, K.epsilon(), 1 - K.epsilon())
    loss = y_true * K.log(y_pred) 
    loss = -K.sum(loss, -1)
    return loss
    # return loss 

char_array = np.asarray(['M','N','H','Q', '$', 'O','C', '?','7','>','!',':','-',';','.',' '])
char_dict = {'M':0,'N':1,'H':2,'Q':3,'$':4,'O':5,'C':6,'?':7,'7':8,'>':9,'!':10,':':11,'-':12,';':13,'.':14,' ':15}


base_model = models.load_model('ascii_nn8.h5', custom_objects={'loss':loss})

#Predicts ascii output of a given image
def main(img_name='in_0.jpg'):
	
	img_path = img_data_dir + img_name
	img = image.load_img(img_path, target_size=(224,224))
	x = image.img_to_array(img)
	x = np.expand_dims(x, axis=0)
	n = base_model.predict(x)
	maxes = np.argmax(n,axis=3)
	# print(maxes)
	# print(maxes.shape)

	buff = ''

	for k,whole in enumerate(maxes):
		for i,row in enumerate(whole):
			for j,col in enumerate(row):
				buff += char_array[col]
			buff += '\n'
	print(buff)

def get_patches(imgarray):
	num_of_patches = 35

	patch_size = 28


	result = []
	result = np.zeros((num_of_patches * num_of_patches,patch_size,patch_size))
	x = 0
	y = 0
	# a = [[1,2,3],[4,5,6],[7,8,9]]
	# a = np.asarray(a, dtype='uint8')
	# print(a[0])
	# print(imgarray.shape)
	imgarray = np.asarray(imgarray, dtype='uint8')
	for i in range(num_of_patches):
		for j in range(num_of_patches):
			patch = imgarray[patch_size * i : patch_size * (i+1), patch_size * j : patch_size * (j+1)]
			result[x,:,:] = patch
			x += 1
	result = np.asarray(result,dtype='uint8')
	return result


#Gets per character accuracy of predicted output
def per_char_acc(size=10000, imgrows=224, imgcols=224, textrows=224, textcols=224, dims=16):
	'''
	Inputs:
		size: number of examples to use
		textrows: height of output
		textcols: width of output
		dims: number of characters to use

	Output: Per character, number of times a character was in the right place divided by the total number of characters

	'''

	x_eval = np.zeros((size,imgrows,imgcols,3))

	y_pred = np.zeros((size,textrows,textcols))
	y_eval = np.zeros((size,textrows,textcols))

	total_characters = np.zeros((dims,))
	correct_characters = np.zeros((dims,))


	for n, el in enumerate(y_eval):
		img_name = 'in_' + str(2000 + n) + '.jpg'
		img_path = img_data_dir + img_name
		label_path = ascii_data_dir + img_name + '.txt'

		img = np.asarray(Image.open(img_path), dtype='uint8')
		x_eval[n] = img 


		img_label = get_label(label_path,textrows,textcols,dims)
		y_eval[n] = img_label
		
	y_pred = base_model.predict(x_eval)
	y_pred = np.argmax(y_pred,axis=3)
	

	flattened_labels = np.asarray(y_eval.flatten(), dtype='uint8')


	for n,el in enumerate(flattened_labels):
		total_characters[el] += 1


	for m,element in enumerate(char_array):

		mask = np.full((size,textrows,textcols), fill_value=m)

		z = np.logical_and(np.equal(mask,y_eval), np.equal(mask,y_pred))
		a = np.sum(z == True)
		print((a / total_characters[m]) * 100)

def char_counts(size=8000, textrows=224, textcols=224, dims=16):
	y_labels = im.load_labels(size,textrows,textcols)
	print(y_labels.shape)
	print(np.argmax(y_labels, axis=3))
	y_labels = np.argmax(y_labels,axis=3)

	totals = [0] * dims

	for n, el in enumerate(y_labels):
		label_name = 'in_' + str(2000 + n) + '.jpg.txt'
		label_path = ascii_data_dir + label_name

		y_labels[n] = get_label(label_path, textrows, textcols, dims)

	flattened_labels = np.asarray(y_labels.flatten(), dtype='uint8')

	for n, el in enumerate(flattened_labels):
		totals[el] += 1

	print("#######################################################################")
	print("TOTAL NUMBER OF CHARACTERS: " + str(np.sum(totals)))
	print("#######################################################################")
	print("NUMBER OF TIMES EACH CHARACTER HAS APPEARED")
	print("M: " + str(totals[0]))
	print("N: " + str(totals[1]))
	print("H: " + str(totals[2]))
	print("Q: " + str(totals[3]))
	print("$: " + str(totals[4]))
	print("O: " + str(totals[5]))
	print("C: " + str(totals[6]))
	print("?: " + str(totals[7]))
	print("7: " + str(totals[8]))
	print(">: " + str(totals[9]))
	print("!: " + str(totals[10]))
	print(":: " + str(totals[11]))
	print("-: " + str(totals[12]))
	print(";: " + str(totals[13]))
	print(".: " + str(totals[14]))
	print("SPACE: " + str(totals[15]))
	return(totals)

	


def get_label(label_path,textrows,textcols,dims):
	'''
	Gets the ASCII text file, which corresponds to the ground truth label 

	Inputs:

		label_path: file directory
		textrows: height of file
		textcols: width of file
		dims: number of unique characters 

	Output: 2D array of indices, where each index is a number that represents a character specified by char_dict 

	'''
	# print(label_path)
	f = open(label_path,'r')
	arr = np.zeros((textrows,textcols), dtype='uint8')
	n = 0
	m = 0 
	acc = 0
	for y,row in enumerate(f):
		for x,col in enumerate(row):
			acc+=1
			if x % 28 == 0 and x is not 0:
				n += 1
				m = 0
			if x == 64:
				break
			arr[n][m] = char_dict[col]
			m += 1
	return arr
def in_newline(string):
	buff = ''

	for i,row in enumerate(string):
		if i % 28 ==0:
			buff += '\n'
		buff += row
	print(buff)
def to_text(arr):
	'''
	Given a numpy array of numbers, turns array into ASCII image
	'''
	buff = ''
	for m,row in enumerate(arr):
		for n,col in enumerate(arr):
			if n == 224:
				buff += '\n'
			buff += col
	print(buff)

# per_char_acc(size=8000, imgrows=224, imgcols=224, textrows=28, textcols=28)