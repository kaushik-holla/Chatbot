# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 00:50:32 2020

@author: holla
"""

import numpy as np
import tensorflow as tf
import re
import time
tf.disable_v2_behavior()

# Importing the dataset
lines = open('movie_lines.txt').read().split('\n')
conversations = open('movie_conversations.txt').read().split('\n')

# Creating the dictionary that maps each lines with its ID
id2line = {}
for line in lines:
    _line = line.split(' +++$+++ ')
    if len(_line) == 5:
        id2line[_line[0]] = _line[4]
        
# Create a list of all of the conversation. - Chatbot 7
conversations_id = []
for conversation in conversations[:-1]:
    # 1. We are considering the last column.
    # 2. To remove the square brackets, we are taking the range and we are not 
    # including the first index and last index to remove the sqlare brackets
    # 3. Remove the quots. Done by using replacing quots with nothing.
    # 4. Now we remove spaces and we do it in the same way as above.
    _conversation = conversation.split(' +++$+++ ')[-1][1:-1].replace("'", "").replace(" ","")
    # The output from previous line will be separated by "," and when we split it on "," it creates a list
    # This list we are appending to create a list of conversations. 
    conversations_id.append(_conversation.split(','))
    
# Getting seperate questions and answers.
# First we will get question and then answers and note that they both need to be of the same size.
# The answer to question at index i need to be at index i in the answer list.
# If a conversation involves say [A, B, C, D] then A is a question and B is answer to it. B is a question and C is answer to it.
# Note for last element i.e D, there is no answer so make sure to handel this in the loop
# Remember the text of the conversation is stored in id2lines
questions = []
answers = []

for conversation in conversations_id:
    for i in range(len(conversation) - 1):
        questions.append(id2line[conversation[i]])
        answers.append(id2line[conversation[i+1]])

# Cleaning the text. 
def clean_text(text):
    # Convert all the text to lowercase
    text = text.lower()
    text = re.sub(r"i'm", "i am", text)
    text = re.sub(r"he's", "he is", text)
    text = re.sub(r"she's", "she is", text)
    text = re.sub(r"that's", "that is", text)
    text = re.sub(r"what's", "what is", text)
    text = re.sub(r"where's", "where is", text)
    text = re.sub(r"\'ll", " will", text)
    text = re.sub(r"\'ve", " have", text)
    text = re.sub(r"\'re", " are", text)
    text = re.sub(r"\'d", " would", text)
    text = re.sub(r"won't", "will not", text)
    text = re.sub(r"can't", "cannot", text)
    text = re.sub(r"[-()\"#/@;:<>{}+=~|.?,]", "", text)
    return text

# Cleaning the Questions and Answers
clean_questions = []
for question in questions:
    clean_questions.append(clean_text(question))
    
# cleaning answers
clean_answers = []
for answer in answers:
    clean_answers.append(clean_text(answer))

# Removing the high frequency words.
# To do that we create a dictionary that contains words along with its frequence.
word2count = {}
for question in clean_questions:
    # With split we get the word dorectly.
    for word in question.split():
        if word in word2count.keys():
            word2count[word] += 1
        else:
            word2count[word] = 1
            
word2count = {}
for answer in clean_answers:
    # With split we get the word dorectly.
    for word in answer.split():
        if word in word2count.keys():
            word2count[word] += 1
        else:
            word2count[word] = 1
        
#Tokenisation and filtering out non essential words. 
# We will take consider a threshold and we remove all the words that are greater than threshold.
# Along with removing the threshold, we also tokenize the sentence.
# We are taking all the words greater than threshold to a separate dictionary i.e questionswords2int and map them to unique integer..
threshold = 20
questionwords2int = {}
word_number = 0
for word, count in word2count.items():
    if count >= threshold:
        questionwords2int[word] = word_number
        word_number += 1
        
answerwords2int = {}
word_number = 0
for word, count in word2count.items():
    if count >= threshold:
        answerwords2int[word] = word_number
        word_number += 1

# Adding start and end tokens to dictionaries.
# <EOS> end of string
# <SOS> Start of string
tokens = ['<PAD>', '<EOS>', '<SOS>', '<OUT>']
for token in tokens:
    questionwords2int[token] = len(questionwords2int) + 1
for token in tokens:
    answerwords2int[token] = len(answerwords2int) + 1
    
#Chatbot 14
#Creating inverse dictionary of answerwords2int
# This inverse is required for building a sec2sec model
answerint2words = {w_i:w for w, w_i in answerwords2int.items()}

# Adding end of string token to end of every answer
# <EOS> is required for decoding the model in sec2sec
for i in range(len(clean_answers)):
    clean_answers[i] += ' <EOS>'

# Translating all questions and answers into integers 
# and replacing all the words that were filtered out by <OUT>
questions_to_int = []
for questions in clean_questions:
    ints = []
    for words in questions.split():
        if words not in questionwords2int:
            ints.append(questionwords2int['<OUT>'])
        else:
            ints.append(questionwords2int[words])    
    questions_to_int.append(ints)

answers_to_int = []
for answers in clean_answers:
    ints = []
    for words in answers.split():
        if words not in answerwords2int:
            ints.append(answerwords2int['<OUT>'])
        else:
            ints.append(answerwords2int[words])
    answers_to_int.append(ints)

# Sorting question and answers by the length of questions/answers to speed up the training.
sorted_clean_question = []
sorted_clean_answers = []
# Limiting the length of questions to 25 words starting with 1.
for length in range(1, 26):
    for i in enumerate(questions_to_int):
        if len(i[1]) == length:
            sorted_clean_question.append(questions_to_int[i[0]])
            # Since questions and answers need to have the same index, we append answers too
            sorted_clean_answers.append(answers_to_int[i[0]])

# Building Seq2seq model

# Creating placeholders for input and target.
def model_input():
    inputs = tf.placeholder(tf.int32, [None, None], name= 'input')
    targets = tf.placeholder(tf.int32, [None, None], name= 'target')
    lr = tf.placeholder(tf.float32, name= 'learning_rate')
    keep_prob = tf.placeholder(tf.float32, name= 'keep_prob')
    return inputs, targets, lr, keep_prob

# Before creating the encoding and decoding layers, we need to preprocessing the targets
# The decoder only accepts certain form of targets. [ Decoders are nothing but LSTM neural networks]
# The input to decoder must be in batches. It doesnt accept single inputs.
# Each of the answers in the batches must start with <SOS>
def preprocess_targets(targets, word2int, batch_size):
    # Creating a new matrix tensor and filling it with <SOS>
    # Matrix will have batch size number of rows and only one column containing <SOS>
    left_side = tf.fill([batch_size, 1], word2int['<SOS>'])
    # Slicing a part of the matrix 
    # Contains matrix having batchsize number of rows and n-1 columns i.e last column excluded.
    right_side = tf.strided_slice(targets, [0, 0], [batch_size, -1], [1, 1])
    # Now we are concatinating 
    preprocessed_targets = tf.concat([left_side, right_side], 1)
    return preprocessed_targets

# We are creating encoder of RNN model as it comes first in seq2seq model.
# Encoder is created using LSTM
def encoder_rnn_layer(rnn_inputs, rnn_size, number_layers, keep_prob, sequence_length):
    # Input Parameters
    """
    rnn_input: This corresponds to model_inputs i.e the basic inputs that are given to rnn models.
    rnn_size: Size of the rnn input i.e number of input tensors.
    number_layers: Number of layers in neural network
    keep_prob: This is used for dropout regularisation
    sequence_length: List of length of each questions in the batch
    """
    # We will define an object call lstm which calls basic LSTM Cell.    
    lstm = tf.contib.rnn.BasicLSTMCell(rnn_size)
    # Creating a dropout wrapper around lstm. 
    lstm_dropout = tf.contrib.rnn.DropoutWrapper(lstm, input_keep_prob = keep_prob)
    # RNN have cell and state variable so now we are creating cell
    encoder_cell = tf.contrib.rnn.MultiRNNCell([lstm_dropout] * number_layers)
    encoder_output, encoder_state = tf.nn.bidirectional_dynamic_rnn(cell_fw = encoder_cell,
                                                                    cell_bw = encoder_cell,
                                                                    sequence_length = sequence_length,
                                                                    inputs = rnn_inputs,
                                                                    dtype = tf.float32)
    return encoder_state

# Chatbot 21
# Decoder RNN Layer
# This is done in two steps.
# 1. Decode the training set.
# 2. Decode the validation set.

def decode_training_set(encoder_state, decoder_cell, decoder_embadded_input, sequence_length, decoder_scope, output_function, keep_prob, batch_size):
"""
    encoder_state: Returned by encoder_rnn_layer
    decoder_cell: Cell from Decoder Recurrent Neural Network.
    decoder_embadded_input: This is the cell on which we apply embadding. // check embadding from tensorflow document.
    decoder_scope: Refer to tf.variable_scope class in tensorflow. Decoder scope will be an object of variable scope.
    output_function: 
    keep_prob: To apply dropout regularisation
    batch_size: We will be working with batch size.
"""
    # First we will be getting the attention state.
    attention_states = tf.zeros([batch_size, 1, decoder_cell.output_size])
    attention_keys, attention_values, attention_score_function, attention_construct_function = tf.contrib.seq2seq.prepare_attention(attention_states, attention_option = "bahdanau", num_units = decoder_cell.output_size)
    training_decoder_function = tf.contrib.seq2seq.attention_decoder_fn_train(encoder_state[0],
                                                                              attention_keys,
                                                                              attention_values,
                                                                              attention_score_function,
                                                                              attention_construct_function,
                                                                              name = "attn_dec_train")
    decoder_output, decoder_final_state, decoder_final_context_state = tf.contrib.seq2seq.dynamic_rnn_decoder(decoder_cell,
                                                                                                              training_decoder_function,
                                                                                                              decoder_embedded_input,
                                                                                                              sequence_length,
                                                                                                              scope = decoding_scope)
    decoder_output_dropout = tf.nn.dropout(decoder_output, keep_prob)
    return output_function(decoder_output_dropout)






























