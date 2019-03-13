#-* -coding: UTF-8 -* -
__author__ = 'Frank'

import os
import pickle
import numpy as np
from collections import Counter
from sklearn.neighbors import KNeighborsClassifier

knn_neigh = None
knn_class_names = None
knn_train_labels = None
knn_labels_counter = None
knn_timestamp = None

__all__ = ['train', 'predict']

#class judge:
def test():
    print("judge test in.")

def train(emb_array, labels, class_names, BASEDIR, timestamp):
    print("judge --> train")
    if len(labels) < 5:
        return
    neigh = KNeighborsClassifier(n_neighbors=5, weights='distance')
    neigh.fit(emb_array, labels)
    score = neigh.score(emb_array, labels, sample_weight=None)
    print("score={}".format(score))

    labels_counter = Counter()
    for x in range(len(labels)):
        labels_counter[labels[x]] += 1
    print("labels_counter={}".format(labels_counter))

    knn_class_names = class_names
    knn_train_labels = labels
    knn_classifier_filename_exp = os.path.expanduser(os.path.join(BASEDIR, "judgeutil.pkl"))
    with open(knn_classifier_filename_exp, 'wb') as outfile:
        pickle.dump((neigh, class_names, labels, labels_counter, timestamp), outfile)
    _load(BASEDIR)

def _load(BASEDIR):
    global knn_neigh
    global knn_class_names
    global knn_train_labels
    global knn_labels_counter
    global knn_timestamp

    knn_classifier_filename_exp = os.path.expanduser(os.path.join(BASEDIR, "judgeutil.pkl"))
    if not os.path.exists(knn_classifier_filename_exp):
        print("No judgeutil.pkl file, return")
        return False
    print("predict knn_classifier_filename_exp={}".format(knn_classifier_filename_exp))
    with open(knn_classifier_filename_exp, 'rb') as infile:
        (knn_neigh, knn_class_names, knn_train_labels, knn_labels_counter, knn_timestamp) = pickle.load(infile)
    return True

def predict(embedding, best_class_indices, BASEDIR, timestamp):
    if knn_neigh is None:
        result = _load(BASEDIR)
        if not result:
            print("Error: no judgeutil.pkl file, return.")
            return -1

    if knn_timestamp != timestamp:
        print("Error: timestamp doesn't match, skip...{}, {}".format(knn_timestamp, timestamp))
        return -1;

    train_size = len(knn_class_names)
    print("train_size={}".format(train_size))
   
    dist, ind = knn_neigh.kneighbors(np.asarray(embedding))
    #print("knn_result={}, best_class_indices[i]={}".format(knn_result, best_class_indices[i]))
    print("neighbors={}, {}".format(dist, ind))
    kneighbors_labels = [knn_train_labels[x] for x in ind[0]]

    print("neighbors_labels={}".format(kneighbors_labels))
    best_class_dist = [dist[0][x] for x in range(len(kneighbors_labels)) if kneighbors_labels[x] == best_class_indices]
    other_class_dist = [dist[0][x] for x in range(len(kneighbors_labels)) if kneighbors_labels[x] != best_class_indices]
    print("best_class_dist={}".format(best_class_dist))
    print("other_class_dist={}".format(other_class_dist))

    total_classnames = []
    for label in kneighbors_labels:
        if label not in total_classnames:
            total_classnames.append(label)
    print("Total names: {}".format(len(total_classnames)))

    knn_match = True
    if (len(best_class_dist) < 2):
        knn_match = False
    elif len(best_class_dist) > 0:
        knn_max_dist = np.argmax(best_class_dist, axis=0)
        knn_min_dist = np.argmin(best_class_dist, axis=0)
        print("max_dist={}".format(knn_max_dist))
        print("min_dist={}".format(knn_min_dist))
        print("!!!best_class_indices={}".format(best_class_indices))
        if knn_labels_counter[best_class_indices] > 3 and len(best_class_dist) < 2:
            knn_match = False
            print("Frank: 1")
        else:
            for x in range(len(other_class_dist)):
                if other_class_dist[x] < best_class_dist[knn_min_dist]+0.01:
                    print("Frank: 2")
                    knn_match = False
                    break

    for k in ind[0]:
        print("{}".format(knn_train_labels[k]))

    print("match={}".format(knn_match))
    if knn_match:
        return 1
    else:
        return 0
