'''
    @ Aurther: Kun Wu
    @ Date: Mar 7th, 2022
'''

import argparse

import pandas as pd
import torch

import graph_earser
from data_loader import load_data
from utils import sample_edges


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # common arguments
    parser.add_argument('-seed', type=int, default=522)
    parser.add_argument('-d', dest='data', type=str, default='cora')
    parser.add_argument('-g', dest='gpu', type=int, default=-1)
    parser.add_argument('-b', dest='baseline', type=str, default='grapheraser')
    parser.add_argument('-m', dest='model', type=str, default='gcn')
    parser.add_argument('-hidden', type=int, nargs='+', default=[16])
    parser.add_argument('-no-feature-update', dest='feature_update', action='store_false')
    parser.add_argument('-batch', type=int, default=512)
    parser.add_argument('-test-batch', type=int, default=1024)
    parser.add_argument('-lr', type=float, default=0.001)
    parser.add_argument('-l2', type=float, default=1E-5)
    parser.add_argument('-p', dest='patience', type=int, default=10)
    parser.add_argument('-method', type=str, default='degree')
    parser.add_argument('-edges', type=int, nargs='+', default=[500],
                        help='the number of edges need to forget.')

    # task
    parser.add_argument('-train', action='store_true')
    parser.add_argument('-retrain', action='store_true')
    parser.add_argument('-unlearn', action='store_true')

    # for data
    parser.add_argument('-feature', dest='feature', action='store_true')
    parser.add_argument('-emb-dim', type=int, default=32)

    # Arugments for GraphEraser
    parser.add_argument('-epochs', dest='epochs', type=int, default=100)
    parser.add_argument('-partitions', type=str, nargs='+', default=['blpa', 'bekm'])
    parser.add_argument('-aggr-methods', type=str, nargs='+', default=['majority', 'mean'])
    parser.add_argument('-k', dest='num_shards', type=int, default=20)
    parser.add_argument('-t', dest='max_t', type=int, default=10)
    # parser.add_argument('-aggr', type=str, default='majority')

    args = parser.parse_args()
    print('Parameters:', vars(args))

    # random.seed(args.seed)
    # np.random.seed(args.seed)
    # torch.manual_seed(args.seed)

    device = torch.device(f'cuda:{args.gpu}') if torch.cuda.is_available() and args.gpu >= 0 else torch.device('cpu')
    data = load_data(args)

    if args.train:
        for num_edges in args.edges:
            for partition in args.partitions:
                args.partition = partition
                for aggr in args.aggr_methods:
                    args.aggr = aggr
                    acc, f1 = graph_earser.train(args, data, device)
                    print(f'Setting {partition}-{aggr}: {acc:.4f}, {f1:.4f}.')

    if args.unlearn:
        args.max_degree = False
        edges = sample_edges(args, data, method=args.method)
        d = {}
        for num_edges in args.edges:
            edges_to_forget = edges[:num_edges]
            for partition in args.partitions:
                args.partition = partition
                for aggr in args.aggr_methods:
                    args.aggr = aggr
                    duration, acc, f1 = graph_earser.unlearn(args, data, edges_to_forget, device)
                    d[f'{partition}-{aggr}-acc'] = acc
                    d[f'{partition}-{aggr}-time'] = duration
                    d[f'{partition}-{aggr}-f1'] = f1

        df = pd.DataFrame(d, index=args.edges)
        df.to_csv(f'./{args.model}_{args.data}_rq1_grapheraser.csv')
        # print('The number of edges to be forgottn is:', len(edges_to_forget))
