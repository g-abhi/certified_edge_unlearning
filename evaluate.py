from operator import mod
import os
import argparse
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report
from data_loader import load_data
from utils import load_model, sample_edges


def analyze_influence_vs_loss_diff(args):
    df = pd.read_csv(os.path.join('./result', args.data, 'influence_vs_loss-diff.csv'))
    influences = df['influence'].values.astype(float)
    loss_diff = df['loss_diff'].values.astype(float)
    distance = abs(influences - loss_diff)
    num_invalide_infl = len(np.where(distance > 0.1)[0])
    print(f'The mean of distance is {np.mean(distance)}')
    print(f'The number of invalid influence is {num_invalide_infl}')


def inference_comparison(args, data, device):
    edges_to_forget = sample_edges(args, data, args.method, args.edges)
    model_original = load_model(args, data).to(device)
    model_unlearned = load_model(args, data, type='unlearn').to(device)
    model_retrained = load_model(args, data, type='retrain').to(device)

    edge_index = torch.tensor(data['edges'], device=device).t()
    edge_index_prime = torch.tensor([e for e in data['edges'] if e not in edges_to_forget], device=device).t()
    test_loader = DataLoader(data['test_set'], batch_size=1024, shuffle=False)

    result = {
        'original': [],
        'unlearned': [],
        'retrained': [],
        'labels': [],
    }
    model_original.eval()
    model_unlearned.eval()
    model_retrained.eval()
    with torch.no_grad():
        for nodes, labels in test_loader:
            nodes = nodes.to(device)
            labels = labels.to(device)
            y_hat = model_original(nodes, edge_index)
            y_pred = torch.argmax(y_hat, dim=1)
            y_hat_tilde = model_unlearned(nodes, edge_index_prime)
            y_pred_tilde = torch.argmax(y_hat_tilde, dim=1)
            y_hat_prime = model_retrained(nodes, edge_index_prime)
            y_pred_prime = torch.argmax(y_hat_prime, dim=1)
            result['original'].extend(y_pred.cpu().tolist())
            result['unlearned'].extend(y_pred_tilde.cpu().tolist())
            result['retrained'].extend(y_pred_prime.cpu().tolist())
            result['labels'].extend(labels.cpu().tolist())

    for m in ['original', 'unlearned', 'retrained']:
        comparison = classification_report(result['labels'], result[m])
        print('For', m)
        print(comparison)
        print('-' * 40)


def l2_distance(args, data, device):
    # edges_to_forget = sample_edges(args, data, args.method, args.edges)
    model_original = load_model(args, data).to(device)
    model_unlearned = load_model(args, data, type='unlearn').to(device)
    model_retrained = load_model(args, data, type='retrain').to(device)
    result = {'A&A_tilde': [], 'A&A_prime': [], 'A_tilde&A_prime': []}
    for p_original, p_unlearned, p_retrained in zip(model_original.parameters(), model_unlearned.parameters(), model_retrained.parameters()):
        result['A&A_tilde'] = np.linalg.norm(p_original, p_unlearned)
        result['A&A_prime'] = np.linalg.norm(p_original, p_retrained)
        result['A_prime&A_tilde'] = np.linalg.norm(p_retrained, p_unlearned)

    for _, v in result.items():
        v = np.sum(v)
    print('L2 Distance:')
    print('  ', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', dest='data', type=str, default='cora')
    parser.add_argument('-g', dest='gpu', type=int, default=-1)
    parser.add_argument('-l', dest='loss_diff', action='store_true',
                        help='Indicator of running analysis on influence against loss difference')
    parser.add_argument('-i', dest='inference_comparison', action='store_true',
                        help='Indicator of evaluating the unlearning model by inference comparison.')
    parser.add_argument('-l2', dest='l2_distance', action='store_true',
                        help='Indicator of evaluating the unlearning by l2 distance.')

    parser.add_argument('-emb-dim', type=int, default=32)
    parser.add_argument('-feature', dest='feature', action='store_true')
    parser.add_argument('-hidden', type=int, default=32)

    # strategy of sampling edges
    parser.add_argument('-method', type=str, default='degree',
                        help='[random, degree, loss_diff].')
    parser.add_argument('-edges', type=int, default=10,
                        help='in terms of precentage, how many edges to sample.')

    args = parser.parse_args()

    data = load_data(args)
    device = torch.device(f'cuda:{args.gpu}') if torch.cuda.is_available() and args.gpu >= 0 else torch.device('cpu')

    if args.loss_diff:
        analyze_influence_vs_loss_diff(args)

    if args.inference_comparison:
        inference_comparison(args, data, device)
