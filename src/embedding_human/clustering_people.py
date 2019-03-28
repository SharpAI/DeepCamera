# -*- coding: utf-8 -*-

""" Face Cluster """
import tensorflow as tf
import numpy as np
import importlib
import argparse
import facenet
import os
import math
import time
import shutil
from collections import Counter
from collections import OrderedDict

def face_distance(face_encodings, face_to_compare):
    """
    Given a list of face encodings, compare them to a known face encoding and get a euclidean distance
    for each comparison face. The distance tells you how similar the faces are.
    :param faces: List of face encodings to compare
    :param face_to_compare: A face encoding to compare against
    :return: A numpy ndarray with the distance for each face in the same order as the 'faces' array
    """
    import numpy as np
    if len(face_encodings) == 0:
        return np.empty((0))

    #return 1/np.linalg.norm(face_encodings - face_to_compare, axis=1)   #1/0.54
    print("type(face_encodings) = {}".format(type(face_encodings)))
    print("type(face_to_compare) = {}".format(type(face_to_compare)))
    return np.sum(face_encodings*face_to_compare,axis=1)
    '''
    distances = []
    for face_encoding in face_encodings:
        distances.append(np.sqrt(np.sum(np.square(np.subtract(face_encoding, face_to_compare)))))
    return distances
    '''

def load_model(model_dir, meta_file, ckpt_file):
    model_dir_exp = os.path.expanduser(model_dir)
    saver = tf.train.import_meta_graph(os.path.join(model_dir_exp, meta_file))
    saver.restore(tf.get_default_session(), os.path.join(model_dir_exp, ckpt_file))

def compare_faces(encoding_list, face_encoding_to_check):
    #from face_recognition.api import _face_distance
    from random import shuffle
    import networkx as nx
    # Create graph
    nodes = []
    edges = []

    image_paths, encodings = zip(*encoding_list)

    if len(encodings) <= 1:
        print ("No enough encodings to cluster!")
        return []

    #for idx, face_encoding_to_check in enumerate(encodings):
        # Adding node of facial encoding

    compare_encodings = encodings
    distances = face_distance(compare_encodings, face_encoding_to_check)
    return distances


def _chinese_whispers(encoding_list, threshold=0.85, iterations=20):
    """ Chinese Whispers Algorithm
    Modified from Alex Loveless' implementation,
    http://alexloveless.co.uk/data/chinese-whispers-graph-clustering-in-python/
    Inputs:
        encoding_list: a list of facial encodings from face_recognition
        threshold: facial match threshold,default 0.6
        iterations: since chinese whispers is an iterative algorithm, number of times to iterate
    Outputs:
        sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
            sorted by largest cluster to smallest
    """

    #from face_recognition.api import _face_distance
    from random import shuffle
    import networkx as nx
    # Create graph
    nodes = []
    edges = []

    image_paths, encodings = zip(*encoding_list)

    if len(encodings) <= 1:
        print ("No enough encodings to cluster!")
        return []

    for idx, face_encoding_to_check in enumerate(encodings):
        # Adding node of facial encoding
        node_id = idx+1

        # Initialize 'cluster' to unique value (cluster of itself)
        #print('image_paths = ', image_paths)
        node = (node_id, {'cluster': image_paths[idx], 'path': image_paths[idx]})
        nodes.append(node)

        # Facial encodings to compare
        if (idx+1) >= len(encodings):
            # Node is last element, don't create edge
            break

        compare_encodings = encodings[idx+1:]
        distances = face_distance(compare_encodings, face_encoding_to_check)
        encoding_edges = []
        for i, distance in enumerate(distances):
            if distance > threshold:
                # Add edge if facial match
                edge_id = idx+i+2
                encoding_edges.append((node_id, edge_id, {'weight': distance}))

        edges = edges + encoding_edges

    #print("nodes = ", nodes);
    #print("edges = ", edges);

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Iterate
    for _ in range(0, iterations):
        cluster_nodes = G.nodes()
        #print("cluster_nodes=", cluster_nodes)
        #for node in cluster_nodes:
        #    print("cluster_nodes[", node, "]= ", cluster_nodes[node])
        '''
        #shuffle(list(cluster_nodes))
        for node in cluster_nodes:
            print("  node=", cluster_nodes[node])
        _cluster_nodes = list(cluster_nodes)
        shuffle(_cluster_nodes)
        for node in cluster_nodes:
            print("  shuffle node=", node)
            print("  shuffle cluster_nodes[node]=", cluster_nodes[node])

        G_random = nx.Graph()
        for x in _cluster_nodes:
            print("cluster_nodes[", x, "]= ", cluster_nodes[x])
            G_random.add_nodes_from((x, cluster_nodes[x]))
        cluster_nodes = G_random.nodes();
        '''
        cluster_nodes_random = list(cluster_nodes)
        shuffle(cluster_nodes_random)
        #print("shuffle cluster_nodes_random=", cluster_nodes_random)
        #for node in cluster_nodes_random:
        #    print("cluster_nodes[", node, "]= ", cluster_nodes[node])
        for node in cluster_nodes_random:
            neighbors = G[node]
            #print("neighbors=", neighbors)
            clusters = {}

            for ne in neighbors:
                #print(" ne = ", ne)
                if isinstance(ne, int):
                    #print("G[node][ne]['weight']=", G[node][ne]['weight'])
                    if G.node[ne]['cluster'] in clusters:
                        #该节点邻居节点的类别的权重
                        #对应上面的字典cluster的意思就是
                        #对应的某个路径下文件的权重
                        #print(">> clusters[G.node[ne]['cluster']]=", clusters[G.node[ne]['cluster']])
                        clusters[G.node[ne]['cluster']] += G[node][ne]['weight']
                    else:
                        clusters[G.node[ne]['cluster']] = G[node][ne]['weight']
                    #print("G.node[ne]['cluster'] = ", G.node[ne]['cluster'])
                    #print("clusters[G.node[ne]['cluster']] = ", clusters[G.node[ne]['cluster']])

            # find the class with the highest edge weight sum
            edge_weight_sum = 0
            max_cluster = 0
            #将邻居节点的权重最大值对应的文件路径给到当前节点
            #print("clusters = ", clusters)
            for cluster in clusters:
                #print("clusters[cluster]=", clusters[cluster])
                if clusters[cluster] > edge_weight_sum:
                    edge_weight_sum = clusters[cluster]
                    max_cluster = cluster

            # set the class of target node to the winning local class
            #print("max_cluster=", max_cluster)
            G.node[node]['cluster'] = max_cluster

    clusters = {}

    # Prepare cluster output
    #print("        G.node.items() = ", G.node.items())
    for (_, data) in G.node.items():
        cluster = data['cluster']
        path = data['path']
        if cluster:
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(path)
    # Sort cluster output
    sorted_clusters = sorted(clusters.values(), key=len, reverse=True)

    return sorted_clusters

def _chinese_whispers2(encoding_list, threshold=0.91, iterations=20):
    """ Chinese Whispers Algorithm
    Modified from Alex Loveless' implementation,
    http://alexloveless.co.uk/data/chinese-whispers-graph-clustering-in-python/
    Inputs:
        encoding_list: a list of facial encodings from face_recognition
        threshold: facial match threshold,default 0.6
        iterations: since chinese whispers is an iterative algorithm, number of times to iterate
    Outputs:
        sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
            sorted by largest cluster to smallest
    """

    #from face_recognition.api import _face_distance
    from random import shuffle
    import networkx as nx
    # Create graph
    nodes = []
    edges = []

    #(url, (face_id, embedding))
    image_paths, _encodings = zip(*encoding_list)
    face_ids, encodings = zip(*_encodings)
    if len(encodings) <= 1:
        print ("No enough encodings to cluster!")
        return []

    for idx, face_encoding_to_check in enumerate(encodings):
        #print("idx={}, face_encoding_to_check={}".format(idx, face_encoding_to_check))
        # Adding node of facial encoding
        node_id = idx+1

        # Initialize 'cluster' to unique value (cluster of itself)
        #print('image_paths = ', image_paths)
        node = (node_id, {'cluster': image_paths[idx], 'path': image_paths[idx]})
        nodes.append(node)
        # Facial encodings to compare
        if (idx+1) >= len(encodings):
            # Node is last element, don't create edge
            break
        compare_encodings = encodings[idx+1:]
        distances = face_distance(compare_encodings, face_encoding_to_check)
        encoding_edges = []
        for i, distance in enumerate(distances):
            if distance > threshold:
                # Add edge if facial match
                edge_id = idx+i+2
                encoding_edges.append((node_id, edge_id, {'weight': distance}))
        edges = edges + encoding_edges

    #print("nodes = ", nodes);
    #print("edges = ", edges);

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    # Iterate
    for _ in range(0, iterations):
        cluster_nodes = G.nodes()
        cluster_nodes_random = list(cluster_nodes)
        shuffle(cluster_nodes_random)
        #print("shuffle cluster_nodes_random=", cluster_nodes_random)
        #for node in cluster_nodes_random:
        #    print("cluster_nodes[", node, "]= ", cluster_nodes[node])
        for node in cluster_nodes_random:
            neighbors = G[node]
            #print("neighbors=", neighbors)
            clusters = {}

            for ne in neighbors:
                #print(" ne = ", ne)
                if isinstance(ne, int):
                    #print("G[node][ne]['weight']=", G[node][ne]['weight'])
                    if G.node[ne]['cluster'] in clusters:
                        #该节点邻居节点的类别的权重
                        #对应上面的字典cluster的意思就是
                        #对应的某个路径下文件的权重
                        #print(">> clusters[G.node[ne]['cluster']]=", clusters[G.node[ne]['cluster']])
                        clusters[G.node[ne]['cluster']] += G[node][ne]['weight']
                    else:
                        clusters[G.node[ne]['cluster']] = G[node][ne]['weight']
                    #print("G.node[ne]['cluster'] = ", G.node[ne]['cluster'])
                    #print("clusters[G.node[ne]['cluster']] = ", clusters[G.node[ne]['cluster']])

            # find the class with the highest edge weight sum
            edge_weight_sum = 0
            max_cluster = 0
            #将邻居节点的权重最大值对应的文件路径给到当前节点
            #print("clusters = ", clusters)
            for cluster in clusters:
                #print("clusters[cluster]=", clusters[cluster])
                if clusters[cluster] > edge_weight_sum:
                    edge_weight_sum = clusters[cluster]
                    max_cluster = cluster

            # set the class of target node to the winning local class
            #print("max_cluster=", max_cluster)
            G.node[node]['cluster'] = max_cluster

    order_list = OrderedDict()
    clusters = {}

    # Prepare cluster output
    #print("        G.node.items() = ", G.node.items())
    for (_, data) in G.node.items():
        cluster = data['cluster']
        path = data['path']
        if cluster:
            order_list[path] = cluster
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(path)
    # Sort cluster output
    sorted_clusters = sorted(clusters.values(), key=len, reverse=True)

    return sorted_clusters, order_list

def cluster_facial_encodings(facial_encodings):
    """ Cluster facial encodings
        Intended to be an optional switch for different clustering algorithms, as of right now
        only chinese whispers is available.
        Input:
            facial_encodings: (image_path, facial_encoding) dictionary of facial encodings
        Output:
            sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
                sorted by largest cluster to smallest
    """

    if len(facial_encodings) <= 1:
        print ("Number of facial encodings must be greater than one, can't cluster")
        return []

    # Only use the chinese whispers algorithm for now
    sorted_clusters = _chinese_whispers(facial_encodings.items())
    return sorted_clusters

def cluster_facial_encodings2(facial_encodings):
    """ Cluster facial encodings
        Intended to be an optional switch for different clustering algorithms, as of right now
        only chinese whispers is available.
        Input:
            facial_encodings: (image_path, facial_encoding) dictionary of facial encodings
        Output:
            sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
                sorted by largest cluster to smallest
    """

    if len(facial_encodings) <= 1:
        print ("Number of facial encodings must be greater than one, can't cluster")
        return []

    # Only use the chinese whispers algorithm for now
    sorted_clusters, order_list = _chinese_whispers2(facial_encodings.items())
    return sorted_clusters, order_list

def check_accuracy(confident, val):
    c = int(confident*100)
    v = int(val*100)
    if v == c :
        return 0.10
    if v > c :
        return 0.01

    percent = (float(c) - float(v))/float(c)
    if (percent<0.10):
        percent = 0.49
    else:
        percent = percent + 0.50

    if (percent>=1.0):
        percent = 0.99

    percent = round(percent, 2)
    return percent

def find_similar_people(facial_encodings, face_encoding_to_check, threshold=0.85):
    if len(facial_encodings) <= 1:
        print ("Number of facial encodings must be greater than one, can't cluster")
        return []

    # Only use the chinese whispers algorithm for now
    #ordered_facial_encodings = OrderedDict(facial_encodings)
    distances = compare_faces(facial_encodings.items(), face_encoding_to_check)
    #sorted(distances)
    max_distance = 0
    max_index = -1000
    for i, distance in enumerate(distances):
        #distance = check_accuracy(0.67, distance)  # facenet计算的accuracy
        if distance > threshold and distance > max_distance:
            max_distance = distance
            max_index = i
        print("distance=", distance, ", max_index=", max_index)
    
    return max_index

def compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                    embedding_size,nrof_images,nrof_batches,emb_array,batch_size,paths):
    """ Compute Facial Encodings
        Given a set of images, compute the facial encodings of each face detected in the images and
        return them. If no faces, or more than one face found, return nothing for that image.
        Inputs:
            image_paths: a list of image paths
        Outputs:
            facial_encodings: (image_path, facial_encoding) dictionary of facial encodings
    """

    for i in range(nrof_batches):
        start_index = i*batch_size
        end_index = min((i+1)*batch_size, nrof_images)
        paths_batch = paths[start_index:end_index]
        images = facenet.load_data(paths_batch, False, False, image_size)
        feed_dict = { images_placeholder:images, phase_train_placeholder:False }
        emb_array[start_index:end_index,:] = sess.run(embeddings, feed_dict=feed_dict)

    #facial_encodings = {}
    facial_encodings = OrderedDict()
    for x in range(nrof_images):
        facial_encodings[paths[x]] = emb_array[x,:]


    return facial_encodings


def identify_people(args):
    """ Main
    Given a list of images, save out facial encoding data files and copy
    images into folders of face clusters.
    """
    from os.path import join, basename, exists
    from os import makedirs
    import numpy as np
    import shutil
    import sys

    with tf.Graph().as_default():
        with tf.Session() as sess:
            train_set = facenet.get_dataset(args.input)
            #image_list, label_list = facenet.get_image_paths_and_labels(train_set)

            meta_file, ckpt_file = facenet.get_model_filenames(os.path.expanduser(args.model_dir))
            
            print('Metagraph file: %s' % meta_file)
            print('Checkpoint file: %s' % ckpt_file)
            load_model(args.model_dir, meta_file, ckpt_file)
            
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            
            image_size = images_placeholder.get_shape()[1]
            embedding_size = embeddings.get_shape()[1]
        
            # Run forward pass to calculate embeddings
            print('Runnning forward pass on images')

            counter  = 0


            image_paths = []
            #image_paths.append(ImageClass('unknown', args.image_path))
            image_paths.append(args.image_path)
            nrof_images = len(image_paths)
            nrof_batches = 1
            emb_array = np.zeros((nrof_images, embedding_size))
            print("len(image_paths)=", len(image_paths))
            facial_encodings = compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                embedding_size,nrof_images,nrof_batches,emb_array,1,image_paths)
            encoding_list = facial_encodings.items()
            _image_paths, encodings = zip(*encoding_list)
            face_encoding_to_check = encodings[0]
            #print("facial_encodings=", facial_encodings)

            image_paths = []
            for x in range(len(train_set)):
                class_name = train_set[x].name
                _image_paths = train_set[x].image_paths
                for i in range(len(_image_paths)):
                    #image_paths.append(ImageClass(class_name, _image_paths[i]))
                    image_paths.append(_image_paths[i])
            #print("image_paths=", image_paths)


            nrof_images = len(image_paths)
            nrof_batches = int(math.ceil(1.0*nrof_images / args.batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            print("len(image_paths)=", len(image_paths))
            facial_encodings = compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                embedding_size,nrof_images,nrof_batches,emb_array,args.batch_size,image_paths)
            #face_encoding_to_check = facial_encodings[args.image_path]
            #facial_encodings = facial_encodings[1:]
            #print("facial_encodings=", facial_encodings)

            #print("face_encoding_to_check=", face_encoding_to_check)
            #print("facial_encodings=", facial_encodings)
            match_index = find_similar_people(facial_encodings, face_encoding_to_check)
            class_name = "newperson"
            if match_index != -1000:
                image_path = image_paths[match_index]
                #print("image_path=", image_path)
                class_name = os.path.basename(os.path.dirname(image_path))
            return class_name


def identify_and_cluster_people(args):
    """ Main
    Given a list of images, save out facial encoding data files and copy
    images into folders of face clusters.
    """
    from os.path import join, basename, exists
    from os import makedirs
    import numpy as np
    import shutil
    import sys

    newimage_classname = ''

    #if not exists(args.output):
    #    makedirs(args.output)

    with tf.Graph().as_default():
        with tf.Session() as sess:
            train_set = facenet.get_dataset(args.input)
            #image_list, label_list = facenet.get_image_paths_and_labels(train_set)

            #for x in range(len(train_set)):
            #    print("train_set[x].image_paths[", x, "]=", train_set[x].image_paths)
            image_paths = []
            for x in range(len(train_set)):
                class_name = train_set[x].name
                _image_paths = train_set[x].image_paths
                for i in range(len(_image_paths)):
                    image_paths.append(_image_paths[i])
            print("len(image_paths)=", len(image_paths))

            meta_file, ckpt_file = facenet.get_model_filenames(os.path.expanduser(args.model_dir))
            
            print('Metagraph file: %s' % meta_file)
            print('Checkpoint file: %s' % ckpt_file)
            load_model(args.model_dir, meta_file, ckpt_file)
            
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            
            image_size = images_placeholder.get_shape()[1]
            embedding_size = embeddings.get_shape()[1]
        
            # Run forward pass to calculate embeddings
            print('Runnning forward pass on images')


            nrof_images = len(image_paths)
            nrof_batches = int(math.ceil(1.0*nrof_images / args.batch_size))
            emb_array = np.zeros((nrof_images, embedding_size))
            facial_encodings = compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                embedding_size,nrof_images,nrof_batches,emb_array,args.batch_size,image_paths)
            #print("facial_encodings=", facial_encodings)
            sorted_clusters = cluster_facial_encodings(facial_encodings)
            num_cluster = len(sorted_clusters)


            for idx, cluster in enumerate(sorted_clusters):
                for path in cluster:
                    print("path=%s" % path)
                
            # Copy image files to cluster folders
            if args.debugmode is True and args.output is not None:
                shutil.rmtree(args.output)
            used_cluster_name = {}
            for idx, cluster in enumerate(sorted_clusters):
                '''
                if args.debugmode is True:
                    #这个是保存聚类后所有类别
                    label = "newperson_"+str(idx)
                    cluster_dir = join(args.output, label)
                    if not exists(cluster_dir):
                        makedirs(cluster_dir)
                    for path in cluster:
                        if args.image_path is not None and (path.find(args.image_path) >= 0):
                            newimage_classname = os.path.basename(cluster_dir)
                            print("The new photo is in: %s" % newimage_classname)
                        shutil.copy(path, join(cluster_dir, basename(path)))
                else:'''
                path_array = []
                for path in cluster:
                    path_array.append(os.path.dirname(path))
                print("path_array= %s" % path_array)
                path_counts = Counter(path_array)
                top_path = path_counts.most_common(3)
                print("top_path=%s" % top_path)
                if len(top_path) > 0:
                    cluster_dir = top_path[0][0]
                    if args.debugmode is True:
                        cluster_dir = join(args.output, os.path.basename(cluster_dir))
                    if cluster_dir in used_cluster_name:
                        if args.debugmode is True:
                            cluster_dir = join(args.output, "newperson_"+str(idx))
                        else:
                            cluster_dir = join(args.input, "newperson_"+str(idx))
                    print("exist cluster_dir=%s" % cluster_dir)
                else:
                    print("the length of top_path is 0, continue...")
                    continue
                if not exists(cluster_dir):
                    makedirs(cluster_dir)

                used_cluster_name[cluster_dir] = 1
                for path in cluster:
                    if args.image_path is not None and (path.find(args.image_path) >= 0):
                        newimage_classname = os.path.basename(cluster_dir)
                        print("The new photo is in: %s" % newimage_classname)
                    if cluster_dir != os.path.dirname(path):
                        if args.debugmode is True:
                            shutil.copy(path, join(cluster_dir, basename(path)))
                        else:
                            shutil.move(path, join(cluster_dir, basename(path)))

    return newimage_classname


def cluster_unknown_people(facial_encodings, current_order_list):
    """ Main
    Given a list of images, save out facial encoding data files and copy
    images into folders of face clusters.
    """
    from os.path import join, basename, exists
    from os import makedirs
    import numpy as np
    import shutil
    import sys
    reorder_list = OrderedDict()

    start_time = time.time()
    sorted_clusters, order_list = cluster_facial_encodings2(facial_encodings)
    num_cluster = len(sorted_clusters)
    print("cluster_unknown_people cluster costs {} S".format(time.time() - start_time))

    #print("sorted_clusters={}".format(sorted_clusters))
    #face_ids, image_paths = zip(*current_order_list)
    for idx, cluster in enumerate(sorted_clusters):
        for path in cluster:
            print("path=%s" % path)
        
    # Copy image files to cluster folders
    #if args.debugmode is True and args.output is not None:
    #    shutil.rmtree(args.output)
    used_cluster_name = {}
    for idx, cluster in enumerate(sorted_clusters):
        url_array = []
        for url in cluster:
            #path_array.append(os.path.dirname(path))
            url_array.append(current_order_list[url][0])
        #print("url_array= %s" % url_array)
        url_counts = Counter(url_array)
        top_url = url_counts.most_common(4)
        print("top_url=%s" % top_url)
        if len(top_url) > 0:
            cluster_dir = None
            for i in range(0, 3):
                if "unknown" in top_url[i][0]:
                    continue
                else:
                    cluster_dir = top_url[i][0]
                    break
            if cluster_dir is None or cluster_dir in used_cluster_name:
                cluster_dir = "newperson_"+str(idx)

            print("exist cluster_dir=%s" % cluster_dir)
        else:
            print("the length of top_url is 0, continue...")
            continue
        used_cluster_name[cluster_dir] = 1
        for url in cluster:
            reorder_list[url] = cluster_dir

    if False:
        output = None
        for url in reorder_list:
            if output is None:
                output = join(os.path.dirname(os.path.dirname(os.path.dirname(current_order_list[url][1]))), "output")
                print("Test output directory is: {}".format(output))
                if output is not None:
                    shutil.rmtree(output)
            face_id = reorder_list[url];
            cluster_dir = join(output, face_id)
            if not exists(cluster_dir):
                makedirs(cluster_dir)
            print("current_order_list[url][1]={}, dest path={}".format(current_order_list[url][1],join(cluster_dir, basename(url)+".png")))
            if os.path.exists(current_order_list[url][1]):
                shutil.copy(current_order_list[url][1], join(cluster_dir, basename(url)+".png"))
            else:
                print("{} not exists!".format(current_order_list[url][1]))


    results = []
    for url in current_order_list:
        if url in reorder_list and current_order_list[url][0] == reorder_list[url]:
            continue
        from_faceId = ''
        #current_order_list[item["url"]] = item["face_id"], item["filepath"]
        if current_order_list[url][0] is not "unknown":
            from_faceId = current_order_list[url][0]
        to_faceId = ''
        if reorder_list.has_key(url) and reorder_list[url] is not None:
            to_faceId = reorder_list[url]
        if from_faceId != '' and to_faceId != '':
            results.append({"opt":'mv', "url":url, "frm":from_faceId, "to":to_faceId})
            print("-->mv: {},  {}==>{}".format(url, from_faceId, to_faceId))

    print("cluster_unknown_people total cost {}S".format(time.time() - start_time))
    #sendMessage2Group(device_id, toid, '-> Train cost {}s'.format(time.time() - start_time))
    return results


def main(args):
    """ Main
    Given a list of images, save out facial encoding data files and copy
    images into folders of face clusters.
    """
    from os.path import join, basename, exists
    from os import makedirs
    import numpy as np
    import shutil
    import sys

    if args.output is not None and not exists(args.output):
        makedirs(args.output)
    print("args.debugmode is ", args.debugmode)
    if args.debugmode is None or args.debugmode is False:
        args.debugmode = False
        print("args.debugmode is False")
    else:
        args.debugmode = True
        print("args.debugmode is True")
    #class_name = identify_people(args)
    class_name = identify_and_cluster_people(args)
    print("class_name = %s" % class_name)
    return

    with tf.Graph().as_default():
        with tf.Session() as sess:
            train_set = facenet.get_dataset(args.input)
            for x in range(len(train_set)):
                print("train_set[x].image_paths[", x, "]=", train_set[x].image_paths)
            #image_list, label_list = facenet.get_image_paths_and_labels(train_set)

            meta_file, ckpt_file = facenet.get_model_filenames(os.path.expanduser(args.model_dir))
            
            print('Metagraph file: %s' % meta_file)
            print('Checkpoint file: %s' % ckpt_file)
            load_model(args.model_dir, meta_file, ckpt_file)
            
            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            
            image_size = images_placeholder.get_shape()[1]
            embedding_size = embeddings.get_shape()[1]
        
            # Run forward pass to calculate embeddings
            print('Runnning forward pass on images')

            counter  = 0
            
            for x in range(len(train_set)):  
                counter += 1
                print(counter)
                image_paths = train_set[x].image_paths
                nrof_images = len(image_paths)
                nrof_batches = int(math.ceil(1.0*nrof_images / args.batch_size))
                emb_array = np.zeros((nrof_images, embedding_size))
                facial_encodings = compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                    embedding_size,nrof_images,nrof_batches,emb_array,args.batch_size,image_paths)
                sorted_clusters = cluster_facial_encodings(facial_encodings)
                num_cluster = len(sorted_clusters)
                
                dest_dir = join(args.output, train_set[x].name)
                # Copy image files to cluster folders
                for idx, cluster in enumerate(sorted_clusters):
                    #这个是保存聚类后所有类别
                    cluster_dir = join(dest_dir, str(idx))
                    if not exists(cluster_dir):
                        makedirs(cluster_dir)
                    for path in cluster:
                        shutil.copy(path, join(cluster_dir, basename(path)))

    
def parse_args(argv):
    """Parse input arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Get a shape mesh (t-pose)')
    parser.add_argument('--model_dir', type=str, help='model dir', required=True)
    parser.add_argument('--batch_size', type=int, help='batch size', required=30)
    parser.add_argument('--image_path', type=str, help='Input image path needed to be checked', required=False)
    parser.add_argument('--input', type=str, help='Input dir of images', required=True)
    parser.add_argument('--output', type=str, help='Output dir of clusters', required=False)
    parser.add_argument('--debugmode', default=False, help='Copy or move files', type=lambda x: (str(x).lower() == 'true'))
    args = parser.parse_args(argv)

    return args

#if __name__ == '__main__':
#    """ Entry point """
#    main(parse_args())
