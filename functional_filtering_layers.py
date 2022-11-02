# -*- coding: utf-8 -*-
"""Functional_Filtering_LAYERS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ifd8a2G8nbkqKqYnxgMSsz_TsRzVKeKy
"""

import keras
import numpy as np
import tensorflow as tf
from skimage.filters import gabor_kernel
import cv2
from PIL import Image
from PIL import ImageFilter

class GaborFilterBank(keras.layers.Layer):    # Requiere imagen con forma [#,h,w,c]
  def __init__(self):
    super().__init__()
  
  def build(self, input_shape):
    # assumption: shape is NHWC 
    self.n_channel = input_shape[-1]
    self.kernels = []
    for theta in range(4):
      theta = theta / 4.0 * np.pi
      for sigma in (1, 3):
        for frequency in (0.05, 0.25):
          kernel = np.real(gabor_kernel(frequency, theta=theta, sigma_x=sigma, sigma_y=sigma)).astype(np.float32)
          # tf.nn.conv2d does crosscorrelation, not convolution, so flipping 
          # the kernel is needed
          kernel = np.flip(kernel)
          # we stack the kernel on itself to match the number of channel of
          # the input
          kernel = np.stack((kernel,)*self.n_channel, axis=-1)
          # print(kernel.shape)
          # adding the number of out channel, here 1.
          kernel = kernel[:, :, : , np.newaxis] 
          # because the kernel shapes are different, we can't do the conv op
          # in one go, so we stack the kernels in a list
          self.kernels.append(tf.Variable(kernel, trainable=False))

  def call(self, x):
    out_list = []
    for kernel in self.kernels:
        out_list.append(tf.nn.conv2d(x, kernel, strides=1, padding="SAME"))
    # output is [batch_size, H, W, 16] where 16 is the number of filters
    # 16 = n_theta * n_sigma * n_freq = 4 * 2 * 2 
    return tf.concat(out_list,axis=-1)

class ContrastFilter(keras.layers.Layer):
  def __init__(self,contrast_factor):     # contrast_factor debe estar en el intervalo (-inf, inf)
    super().__init__()
    self.contrast_factor = contrast_factor

  def call(self, x):
    output = tf.image.adjust_contrast(x, self.contrast_factor)
    return output

class GammaFilter(keras.layers.Layer):
  """
  Para gamma superior a 1, el histograma se desplazará hacia la izquierda y la 
  imagen de salida será más oscura que la imagen de entrada. Para gamma inferior 
  a 1, el histograma se desplazará hacia la derecha y la imagen de salida será 
  más brillante que la imagen de entrada.
  """
  def __init__(self,gamma,gain):
    super().__init__()
    self.gamma = gamma
    self.gain = gain

  def call(self, x):
    output = tf.image.adjust_gamma(x, self.gamma, self.gain)
    return output

class BrighFilter(keras.layers.Layer):
  def __init__(self,delta):     # delta debe estar en el rango [-1,1]
    super().__init__()
    self.delta = delta

  def call(self, x):
    output = tf.image.adjust_brightness(x, self.delta)
    return output