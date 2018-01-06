import tensorflow as tf 
from keras.backend.tensorflow_backend import set_session
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.visible_device_list = "0"
set_session(tf.Session(config=config))

from keras import models
from keras.preprocessing import image 
from keras.models import Model 
import numpy as np 

from PIL import Image

img_data_dir = '/home/nsaftarli/Documents/ascii-art/ASCIIArtNN/assets/rgb_in/img_celeba/'
ascii_data_dir = '/home/nsaftarli/Documents/ascii-art/ASCIIArtNN/assets/ascii_out/'

# char_array = np.asarray(['M','N','H','Q', '$', 'O','C', '?','7','>','!',':','-',';','.',' '])
char_array = np.asarray(['#', ' '])
char_dict = {'M':0,'N':1,'H':2,'Q':3,'$':4,'O':5,'C':6,'?':7,'7':8,'>':9,'!':10,':':11,'-':12,';':13,'.':14,' ':15}


base_model = models.load_model('ascii_nn4.h5')

#Predicts ascii output of a single image
def main(model='ascii_nn4.h5', img_name='in_0.jpg'):
	
	img_path = img_data_dir + img_name
	img = image.load_img(img_path, target_size=(224,224))
	x = image.img_to_array(img)
	x = np.expand_dims(x, axis=0)
	n = base_model.predict(x)
	maxes = np.argmax(n,axis=3)
	print(maxes)
	print(maxes.shape)

	buff = ''

	for k,whole in enumerate(maxes):
		for i,row in enumerate(whole):
			for j,col in enumerate(row):
				buff += char_array[col]
			buff += '\n'
	print(buff)

#Gets per character accuracy of predicted output
def per_char_acc(name,arr, size=1, textrows=224, textcols=224, dims=16):

	x_eval = np.zeros((size,textrows,textcols,3))

	y_pred = np.zeros((size,textrows,textcols,3))
	y_eval = np.zeros((size,textrows,textcols))

	total_characters = np.zeros((dims,))
	correct_characters = np.zeros((dims,))

	for n, el in enumerate(y_eval):
		img_name = 'in_' + str(2000 + n) + '.jpg'
		img_path = img_data_dir + img_name
		label_path = ascii_data_dir + img_name

		img = np.asarray(Image.open(img_path), dtype='uint8')
		x_eval[n] = img 


		img_label = get_label(label_path,textrows,textcols,dims)
		y_eval[n] = img_label
		
	y_pred = base_model.predict(x_eval)
	y_pred = np.argmax(y_pred,axis=3)

	to_text(y_pred[0])
	

	flattened_labels = np.asarray(y_eval.flatten(), dtype='uint8')


	for n,el in enumerate(flattened_labels):
		total_characters[el] += 1


	for m,element in enumerate(char_array):

		mask = np.full((size,textrows,textcols), fill_value=m)

		z = np.logical_and(np.equal(mask,y_eval), np.equal(mask,y_pred))
		a = np.sum(z == True)
		print((a / total_characters[m]) * 100)



def get_label(label_path,textrows,textcols,dims):
	f = open(label_path,'r')
	buff = ''
	arr = np.zeros((textrows,textcols), dtype='uint8')
	n = 0
	m = 0
	for y,row in enumerate(f):
		for x,col in enumerate(row):
			if x % 224 == 0 and x is not 0:
				n += 1
				m = 0
			arr[n][m] = char_dict[col]
			m += 1
	return arr

def to_text(arr):
	buff = ''
	for m,row in enumerate(arr):
		for n,col in enumerate(arr):
			if n == 224:
				buff += '\n'
			buff += col
	print(buff)

# per_char_acc(2,3)

