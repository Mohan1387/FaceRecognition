import tensorflow as tf
import cv2
import numpy as np
import os
import random
import sys
import json
import dlib
from sklearn.model_selection import train_test_split

input_dir = './input_img'

size = 64
file_name = 'names.json'
with open(file_name, 'r') as file:
	names = json.load(file)
count = len(names)
imgs = []
labs = []

def getAll(folder):
	assert os.path.exists(folder)
	assert os.path.isdir(folder)
	imageList = os.listdir(folder)
	imageList = [os.path.abspath(item) for item in imageList if os.path.isfile(os.path.join(folder, item))]
	return imageList


def getPaddingSize(img):
	h, w, _ = img.shape
	top, bottom, left, right = (0, 0, 0, 0)
	longest = max(h, w)

	if w < longest:
		tmp = longest - w
		left = tmp // 2
		right = tmp - left
	elif h < longest:
		tmp = longest - h
		top = tmp // 2
		bottom = tmp - top
	else:
		pass
	return top, bottom, left, right


def readData(path, h=size, w=size):
	for filename in os.listdir(path):
		if filename.endswith('.jpg'):
			filename = path + '/' + filename

			img = cv2.imread(filename)

			top, bottom, left, right = getPaddingSize(img)
			img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0])
			img = cv2.resize(img, (h, w))

			imgs.append(img)
			labs.append(path)


nlabs = []
for i in range(count):
	readData(names[i])

a = [0 for i in range(count)]

for index in range(len(labs)):
	for itr in range(len(names)):
		if labs[index] == names[itr]:
			a[itr] = 1
			nlabs.append(a)
			a[itr] = 0
			break

imgs = np.array(imgs)

nlabs = np.array(nlabs)
train_x, test_x, train_y, test_y = train_test_split(imgs, nlabs, test_size=0.05, random_state=random.randint(0, 100))

train_x = train_x.reshape(train_x.shape[0], size, size, 3)
test_x = test_x.reshape(test_x.shape[0], size, size, 3)
train_x = train_x.astype('float32') / 255.0
test_x = test_x.astype('float32') / 255.0

print('train size:%s, test size:%s' % (len(train_x), len(test_x)))
batch_size = 10
num_batch = len(train_x) // batch_size

x = tf.placeholder(tf.float32, [None, size, size, 3])
y_ = tf.placeholder(tf.float32, [None, count])

keep_prob_5 = tf.placeholder(tf.float32)
keep_prob_75 = tf.placeholder(tf.float32)


def weightVariable(shape):
	init = tf.random_normal(shape, stddev=0.01)
	return tf.Variable(init)


def biasVariable(shape):
	init = tf.random_normal(shape)
	return tf.Variable(init)


def conv2d(x, W):
	return tf.nn.conv2d(x, W, strides=[1, 1, 1, 1], padding='SAME')


def maxPool(x):
	return tf.nn.max_pool(x, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')


def dropout(x, keep):
	return tf.nn.dropout(x, keep)


def cnnLayer():
	W1 = weightVariable([3, 3, 3, 32])
	b1 = biasVariable([32])
	conv1 = tf.nn.relu(conv2d(x, W1) + b1)
	pool1 = maxPool(conv1)
	drop1 = dropout(pool1, keep_prob_5)


	W2 = weightVariable([3, 3, 32, 64])
	b2 = biasVariable([64])
	conv2 = tf.nn.relu(conv2d(drop1, W2) + b2)
	pool2 = maxPool(conv2)
	drop2 = dropout(pool2, keep_prob_5)


	W3 = weightVariable([3, 3, 64, 64])
	b3 = biasVariable([64])
	conv3 = tf.nn.relu(conv2d(drop2, W3) + b3)
	pool3 = maxPool(conv3)
	drop3 = dropout(pool3, keep_prob_5)


	Wf = weightVariable([8 * 16 * 32, 512])
	bf = biasVariable([512])
	drop3_flat = tf.reshape(drop3, [-1, 8 * 16 * 32])
	dense = tf.nn.relu(tf.matmul(drop3_flat, Wf) + bf)
	dropf = dropout(dense, keep_prob_75)


	Wout = weightVariable([512, count])
	bout = weightVariable([count])
	out = tf.add(tf.matmul(dropf, Wout), bout)
	return out


output = cnnLayer()
predict = tf.argmax(output, 1)

saver = tf.train.Saver()
sess = tf.Session()
saver.restore(sess, tf.train.latest_checkpoint('.'))


def is_my_face(image):
	res = sess.run(predict, feed_dict={x: [image / 255.0], keep_prob_5: 1.0, keep_prob_75: 1.0})
	for i in res:
		if res[i] == 1:
			return i




detector = dlib.get_frontal_face_detector()

for (path, dirnames, filenames) in os.walk(input_dir):
	for filename in filenames:
		if filename.endswith('.jpg'):
			img_path = path + '/' + filename
			img = cv2.imread(img_path)
			gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
			dets = detector(gray_img, 1)


			for i, d in enumerate(dets):
				x1 = d.top() if d.top() > 0 else 0
				y1 = d.bottom() if d.bottom() > 0 else 0
				x2 = d.left() if d.left() > 0 else 0
				y2 = d.right() if d.right() > 0 else 0
				face = img[x1:y1, x2:y2]
				face = cv2.resize(face, (size, size))

				cv2.imshow('image', face)
				print('This is the number %d student.' % is_my_face(face))
			key = cv2.waitKey(30) & 0xff
			if key == 27:
				sys.exit(0)


sess.close()
