# -*- coding: UTF-8 -*-
import os
from migrate_db import TrainSet


def clean_droped_embedding(group_id):
    all_drop_dataset = TrainSet.query.filter_by(group_id=group_id, drop=True).all()
    for t in all_drop_dataset:
        filepath = t.filepath
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            #print("remove %s" %filepath)
            embedding_path = filepath.replace('face_dataset', 'face_embedding') + '.txt'
            if os.path.exists(embedding_path):
                os.remove(embedding_path)
                #print("remove %s" %embedding_path)
