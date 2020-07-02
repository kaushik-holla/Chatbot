# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 00:50:32 2020

@author: holla
"""

import numpy as np
import tensorflow as tf
import re
import time

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
    
# Chatbot 8
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

# Chatbot 9
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

# Chatbot 10
# Cleaning the Questions and Answers
clean_questions = []
for question in questions:
    clean_questions.append(clean_text(question))
    
# cleaning answers
clean_answers = []
for answer in answers:
    clean_answers.append(clean_text(answer))

# Chatbot 11
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
        
# chatbot 12
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

#Chatbot 13
# Adding start and end tokens to dictionaries.
# <EOS> end of string
# <SOS> Start of string
tokens = ['<PAD>', '<EOS>', '<SOS>', 'OUT']
for token in tokens:
    questionwords2int[token] = len(questionwords2int) + 1
for token in tokens:
    answerwords2int[token] = len(answerwords2int) + 1
    
#Chatbot 14
#Creating inverse dictionary of answerwords2int
# This inverse is required for building a sec2sec model
answerint2words = {w_i:w for w, w_i in answerwords2int.items()}

#Chatbot 15
# Adding end of string token to end of every answer
# <EOS> is required for decoding the model in sec2sec
for i in range(len(clean_answers)):
    clean_answers[i] += ' <EOS>'

#Chatbot 16










































