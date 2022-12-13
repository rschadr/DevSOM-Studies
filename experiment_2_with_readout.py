# -*- coding: utf-8 -*-


# **Experiment 2:** 
### *Train a 24x24 SOFM on MNIST-b1 for 3m epochs.*

import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime

from load_MNIST import load_mnist_data, blur_images
from SOFM import SOFM, save_model_params, load_model_params

train_img_arr, train_label_arr, test_img_arr, test_label_arr = load_mnist_data("..\\..\\MNIST")

# using black numbers on white background
train_arr_full = 1 - (train_img_arr.reshape(train_img_arr.shape[0], train_img_arr.shape[1] * train_img_arr.shape[2]) / 255)
test_arr_full = 1 - (test_img_arr.reshape(test_img_arr.shape[0], test_img_arr.shape[1] * test_img_arr.shape[2]) / 255)

SIZE_OF_TRAINING_SET = 5000
num_examples = SIZE_OF_TRAINING_SET // 10

# get random balanced subset of full MNIST training dataset 
train_arr_b1 = np.empty((SIZE_OF_TRAINING_SET, 784))

readout_examples = np.ndarray((10, 784))
for i in range(10):
  # get balanced training subset
  idxs = np.where(train_label_arr==i)[0]
  rand_idxs = np.random.choice(idxs, num_examples)
  train_arr_b1[i*num_examples:(i*num_examples)+num_examples] = train_arr_full[rand_idxs]
  # and the first example of each class to be used for Readouts
  first_example = rand_idxs[0]
  readout_examples[i] = train_arr_full[first_example]

np.random.shuffle(train_arr_b1)

# get a subset for MNIST-b3 and MNIST-b5
# where the digit after '-b' indicates the radius of the uniform blurring filter
train_arr_b3 = blur_images(train_arr_b1, img_d1=28, img_d2=28, radius=3)
train_arr_b5 = blur_images(train_arr_b1, img_d1=28, img_d2=28, radius=5)

# create directory for experiment_2
print('Creating experiment_2 directory...')
if not os.path.isdir('experiment_2'):
  os.mkdir('experiment_2')

date_str = datetime.today().strftime('%Y-%m-%d')
run_dir = 'experiment_2\\' + date_str
i = 0
while os.path.isdir(run_dir):
  i += 1
  run_dir = 'experiment_2\\' + date_str + ' (' + str(i) + ')'
os.mkdir(run_dir)

##### STAGE 1 - 6x6 SOFM on MNIST-b5 #####

CURRENT_STAGE = 1

### HYPERPARAMETERS ###
NETWORK_D1 = 6
NETWORK_D2 = 6
LEARNING_RATE = 0.025 
STARTING_NEIGHBORHOOD_SIZE = 3.0
NEIGHBORHOOD_DECAY_RATE = 25
NUM_EPOCHS = 100 # CHANGEME

sofm = SOFM(d1=NETWORK_D1, d2=NETWORK_D2, image_dims=(28,28), sigma_o=STARTING_NEIGHBORHOOD_SIZE, tau_N=NEIGHBORHOOD_DECAY_RATE)

stage_dir = run_dir + f'\\stage{CURRENT_STAGE}'
os.mkdir(stage_dir)
os.mkdir(stage_dir + '\\readouts')

train_start_time = datetime.now()
sofm.train(train_arr_b5, CURRENT_STAGE, NUM_EPOCHS, LEARNING_RATE, readout_interval=10, readout_examples=readout_examples, readout_path=stage_dir+'\\readouts')
train_end_time = datetime.now()

# save model weights
save_model_params(sofm.weights, stage_dir + '\\sofm_weights.xlsx')

# get win percentage of each neuron by class (using training data) - needed for classification metric
train_win_counts, train_win_percentages = sofm.calc_win_percentages(train_arr_full, train_label_arr) # TODO: change this to MNIST-b5

# get total number of wins among all classes for each neuron
total_wins_train = np.sum(train_win_counts, axis=0)

# assign label to each neuron based on for which class it won most often 
# (i.e. which win_percentage for each class is the highest for each neuron)
# if a neuron did not win for any examples, assign a random class label - need this so we can compute classification metric
neuron_labels = np.where(total_wins_train != 0, np.argmax(train_win_percentages, axis=0), np.rint(9 * np.random.rand(NETWORK_D1, NETWORK_D2))).astype(np.int32) 

# plot neuron class tuning labels
sofm.visualize_neuron_classes(neuron_labels, stage_dir + '\\class_tuning')

# plot weights of all neurons
sofm.visualize_weights(stage_dir + '\\weights')

# get win percentage of each neuron by class (using testing data) - needed for entropy and NCL metric
test_win_counts, test_win_percentages = sofm.calc_win_percentages(test_arr_full, test_label_arr)

# calculate entropy of each neuron
entropy = sofm.calc_entropy(test_win_counts)

# create entropy plot
sofm.create_entropy_plot(entropy, stage_dir + '\\entropy')

# classification metric
hit_rate = sofm.calc_classification_metric(test_arr_full, test_label_arr, neuron_labels, 
                                          plot_conf_matrix=True, filename=stage_dir + '\\confusion_matrix')

# normalized category localization (NCL) metric
ncl_score = sofm.calc_ncl_metric(test_win_counts, test_win_percentages)

# plot win percentages on a heatmap for each class
sofm.plot_win_percentages(test_win_percentages, stage_dir + '\\win_percentages')

# write out stats.txt
sofm.write_stats(train_start_time, train_end_time, NUM_EPOCHS, len(train_arr_b1), LEARNING_RATE, ncl_score=ncl_score, classification_score=hit_rate, filename= stage_dir + '\\stats.txt',)

##### STAGE 2 - 12x12 SOFM on MNIST-b3 #####

CURRENT_STAGE = 2

### HYPERPARAMETERS ###
NETWORK_D1 = 12
NETWORK_D2 = 12
LEARNING_RATE = 0.025 
STARTING_NEIGHBORHOOD_SIZE = 3.0
NEIGHBORHOOD_DECAY_RATE = 25
NUM_EPOCHS = 100 # CHANGEME

sofm.complexify(NETWORK_D1, NETWORK_D2, noise_variance=0.2)

stage_dir = run_dir + f'\\stage{CURRENT_STAGE}'
os.mkdir(stage_dir)
os.mkdir(stage_dir + '\\readouts')

train_start_time = datetime.now()
sofm.train(train_arr_b3, CURRENT_STAGE, NUM_EPOCHS, LEARNING_RATE, readout_interval=10, readout_examples=readout_examples, readout_path=stage_dir+'\\readouts')
train_end_time = datetime.now()

# save model weights
save_model_params(sofm.weights, stage_dir + '\\sofm_weights.xlsx')

# get win percentage of each neuron by class (using training data) - needed for classification metric
train_win_counts, train_win_percentages = sofm.calc_win_percentages(train_arr_full, train_label_arr)

# get total number of wins among all classes for each neuron
total_wins_train = np.sum(train_win_counts, axis=0)

# assign label to each neuron based on for which class it won most often 
# (i.e. which win_percentage for each class is the highest for each neuron)
# if a neuron did not win for any examples, assign a random class label - need this so we can compute classification metric
neuron_labels = np.where(total_wins_train != 0, np.argmax(train_win_percentages, axis=0), np.rint(9 * np.random.rand(NETWORK_D1, NETWORK_D2))).astype(np.int32) 

# plot neuron class tuning labels
sofm.visualize_neuron_classes(neuron_labels, stage_dir + '\\class_tuning')

# plot weights of all neurons
sofm.visualize_weights(stage_dir + '\\weights')

# get win percentage of each neuron by class (using testing data) - needed for entropy and NCL metric
test_win_counts, test_win_percentages = sofm.calc_win_percentages(test_arr_full, test_label_arr)

# calculate entropy of each neuron
entropy = sofm.calc_entropy(test_win_counts)

# create entropy plot
sofm.create_entropy_plot(entropy, stage_dir + '\\entropy')

# classification metric
hit_rate = sofm.calc_classification_metric(test_arr_full, test_label_arr, neuron_labels, 
                                          plot_conf_matrix=True, filename=stage_dir + '\\confusion_matrix')

# normalized category localization (NCL) metric
ncl_score = sofm.calc_ncl_metric(test_win_counts, test_win_percentages)

# plot win percentages on a heatmap for each class
sofm.plot_win_percentages(test_win_percentages, stage_dir + '\\win_percentages')

# write out stats.txt
sofm.write_stats(train_start_time, train_end_time, NUM_EPOCHS, len(train_arr_b1), LEARNING_RATE, ncl_score=ncl_score, classification_score=hit_rate, filename=stage_dir + '\\stats.txt',)


##### STAGE 3 - 24x24 SOFM on MNIST-b1 #####

CURRENT_STAGE = 3

### HYPERPARAMETERS ###
NETWORK_D1 = 24
NETWORK_D2 = 24
LEARNING_RATE = 0.025 
STARTING_NEIGHBORHOOD_SIZE = 3.0
NEIGHBORHOOD_DECAY_RATE = 25
NUM_EPOCHS = 100 # CHANGEME

sofm.complexify(NETWORK_D1, NETWORK_D2, noise_variance=0.2)

stage_dir = run_dir + f'\\stage{CURRENT_STAGE}'
os.mkdir(stage_dir)
os.mkdir(stage_dir + '\\readouts')

train_start_time = datetime.now()
sofm.train(train_arr_b1, CURRENT_STAGE, NUM_EPOCHS, LEARNING_RATE, readout_interval=10, readout_examples=readout_examples, readout_path=stage_dir+'\\readouts')
train_end_time = datetime.now()

# save model weights
save_model_params(sofm.weights, stage_dir + '\\sofm_weights.xlsx')

# get win percentage of each neuron by class (using training data) - needed for classification metric
train_win_counts, train_win_percentages = sofm.calc_win_percentages(train_arr_full, train_label_arr)

# get total number of wins among all classes for each neuron
total_wins_train = np.sum(train_win_counts, axis=0)

# assign label to each neuron based on for which class it won most often 
# (i.e. which win_percentage for each class is the highest for each neuron)
# if a neuron did not win for any examples, assign a random class label - need this so we can compute classification metric
neuron_labels = np.where(total_wins_train != 0, np.argmax(train_win_percentages, axis=0), np.rint(9 * np.random.rand(NETWORK_D1, NETWORK_D2))).astype(np.int32) 

# plot neuron class tuning labels
sofm.visualize_neuron_classes(neuron_labels, stage_dir + '\\class_tuning')

# plot weights of all neurons
sofm.visualize_weights(stage_dir + '\\weights')

# get win percentage of each neuron by class (using testing data) - needed for entropy and NCL metric
test_win_counts, test_win_percentages = sofm.calc_win_percentages(test_arr_full, test_label_arr)

# calculate entropy of each neuron
entropy = sofm.calc_entropy(test_win_counts)

# create entropy plot
sofm.create_entropy_plot(entropy, stage_dir + '\\entropy')

# classification metric
hit_rate = sofm.calc_classification_metric(test_arr_full, test_label_arr, neuron_labels, 
                                          plot_conf_matrix=True, filename=stage_dir + '\\confusion_matrix')

# normalized category localization (NCL) metric
ncl_score = sofm.calc_ncl_metric(test_win_counts, test_win_percentages)

# plot win percentages on a heatmap for each class
sofm.plot_win_percentages(test_win_percentages, stage_dir + '\\win_percentages')

# write out stats.txt
sofm.write_stats(train_start_time, train_end_time, NUM_EPOCHS, len(train_arr_b1), LEARNING_RATE, ncl_score=ncl_score, classification_score=hit_rate, filename=stage_dir + '\\stats.txt',)

pass