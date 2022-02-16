import os
from collections import defaultdict
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split


def initialize_features(dataset, num_nodes, emb_dim):
    features_path = os.path.join('./data', dataset, 'features.pt')
    if os.path.exists(features_path):
        features = torch.load(features_path)
    else:
        features = torch.zeros(num_nodes, emb_dim)
        nn.init.xavier_normal_(features)
        torch.save(features, features_path)
    return features.numpy()


def load_cora(args):
    paper_dict = defaultdict(dict)
    with open(os.path.join('./data/', args.data, 'cora.content'), 'r') as fp:
        for line in fp:
            splitted = line.split()
            paper_id = splitted[0]
            label = splitted[-1]
            feature = list(map(int, splitted[1: -1]))
            paper_dict[paper_id] = {'label': label, 'feature': feature}

    node2idx = {paper_id: idx for idx, paper_id in enumerate(paper_dict.keys())}
    num_nodes = len(node2idx)
    nodes = list(range(num_nodes))

    labels = []
    features = []

    for paper_id, value in paper_dict.items():
        labels.append(value['label'])
        features.append(value['feature'])
    label2idx = {l: idx for idx, l in enumerate(set(labels))}
    labels = np.array([label2idx[l] for l in labels])
    features = np.array(features)

    edges = []
    with open(os.path.join('./data', args.data, 'cora.cites'), 'r') as fp:
        for line in fp:
            e = line.split()
            edges.append((node2idx[e[0]], node2idx[e[1]]))

    if not args.feature:
        features = initialize_features(args.data, num_nodes, args.emb_dim)
    return nodes, edges, features, labels, node2idx, label2idx


def load_data(args):
    if args.data == 'cora':
        nodes, edges, features, labels, node2idx, label2idx = load_cora(args)
        num_nodes = len(nodes)
        num_classes = np.max(labels) + 1

        train_set_path = os.path.join('./data/', args.data, 'train_set.pt')
        valid_set_path = os.path.join('./data/', args.data, 'valid_set.pt')
        test_set_path = os.path.join('./data/', args.data, 'test_set.pt')
        if os.path.exists(train_set_path) and os.path.exists(valid_set_path) and os.path.exists(test_set_path):
            train_set = torch.load(os.path.join('./data', args.data, 'train_set.pt'))
            valid_set = torch.load(os.path.join('./data', args.data, 'valid_set.pt'))
            test_set = torch.load(os.path.join('./data', args.data, 'test_set.pt'))
        else:
            nodes_train, nodes_test, labels_train, labels_test = train_test_split(nodes, labels, test_size=0.2)
            nodes_train, nodes_valid, labels_train, labels_valid = train_test_split(
                nodes_train, labels_train, test_size=0.2)
            train_set = CoraDataset(nodes_train, labels_train)
            valid_set = CoraDataset(nodes_valid, labels_valid)
            test_set = CoraDataset(nodes_test, labels_test)
            torch.save(train_set, train_set_path)
            torch.save(valid_set, valid_set_path)
            torch.save(test_set, test_set_path)

        data = {
            'nodes': nodes,
            'edges': edges,
            'features': features,
            'labels': labels,
            'num_nodes': num_nodes,
            'num_classes': num_classes,
            'node2idx': node2idx,
            'label2idx': label2idx,
            'train_set': train_set,
            'valid_set': valid_set,
            'test_set': test_set,
        }
        return data


class CoraDataset(Dataset):

    def __init__(self, nodes, labels):
        self.nodes = nodes
        self.labels = labels

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, idx):
        return self.nodes[idx], self.labels[idx]
