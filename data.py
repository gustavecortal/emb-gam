import datasets
import config
import os
from os.path import join as oj
from tqdm import tqdm
import pandas as pd
import pickle as pkl
import numpy as np
from sklearn.model_selection import train_test_split

def process_data_and_args(args):
    # load dset
    if args.dataset == 'tweet_eval':
        dataset = datasets.load_dataset('tweet_eval', 'hate')
    elif args.dataset == 'financial_phrasebank':
        train = datasets.load_dataset('financial_phrasebank', 'sentences_75agree',
                                      revision='main', split='train')
        idxs_train, idxs_val = train_test_split(np.arange(len(train)), test_size=0.33, random_state=13)
        dataset = datasets.DatasetDict()
        dataset['train'] = train.select(idxs_train)
        dataset['validation'] = train.select(idxs_val)
    else:
        dataset = datasets.load_dataset(args.dataset)
        
    # process dset
    if args.dataset == 'sst2':
        del dataset['test']
        args.dataset_key_text = 'sentence'
    if args.dataset == 'financial_phrasebank':
        args.dataset_key_text = 'sentence'        
    elif args.dataset == 'imdb':
        del dataset['unsupervised']
        dataset['validation'] = dataset['test']
        del dataset['test']
        args.dataset_key_text = 'text'
    elif args.dataset == 'emotion':
        del dataset['test']
        args.dataset_key_text = 'text'
    elif args.dataset == 'rotten_tomatoes':
        del dataset['test']
        args.dataset_key_text = 'text'       
    elif args.dataset == 'tweet_eval':
        del dataset['test']
        args.dataset_key_text = 'text'               
    #if args.subsample > 0:
    #    dataset['train'] = dataset['train'].select(range(args.subsample))
    return dataset, args


def load_fitted_results(fname_filters=['all'], dset_filters=[], drop_model=True):
    """filters must be included in fname to be included.
    Empty list of filters will return everything
    """
    dsets = os.listdir(config.results_dir)
    for dset_filter in dset_filters:
        dsets = [d for d in dsets if dset_filter in d]
    rs = []
    for dset in dsets:
        # depending on how much is saved, this may take a while
        results_dir = oj(config.results_dir, dset)
        dir_names = sorted([fname
                            for fname in os.listdir(results_dir)
                            if os.path.isdir(oj(results_dir, fname))
                            and not '-norm' in fname
                            and 'all' in fname
                           ])
        
        for fname_filter in fname_filters:
            dir_names = [d for d in dir_names if fname_filter in d]
        # print(dir_names)
        
        if drop_model:
            results_list = [pd.Series(pkl.load(open(oj(results_dir, dir_name, 'results.pkl'), "rb"))).drop('model')
                        for dir_name in tqdm(dir_names)]
        else:
            results_list = [pd.Series(pkl.load(open(oj(results_dir, dir_name, 'results.pkl'), "rb")))
                        for dir_name in tqdm(dir_names)]            
        r = pd.concat(results_list, axis=1).T.infer_objects() #.drop(columns='model')
        r['all'] = r['all'].replace('True', 'all')
        r['seed'] = r['seed'].fillna(1)    
        r = r.fillna('')
        r['dataset'] = dset
        rs.append(r)
    rs = pd.concat(rs)
    return rs


DSETS_RENAME_DICT = {
    'emotion': 'Emotion',
    'sst2': 'SST2',
    'tweet_eval': 'Tweet (Hate)',
    'rotten_tomatoes': 'Rotten tomatoes'
}

COLUMNS_RENAME_DICT = {
    'n_train': 'Samples (train)',
    'n_val': 'Samples (val)',
    'n_tokens': 'Unigrams',
    'n_bigrams': 'Bigrams',
    'n_trigrams': 'Trigrams',            
    'num_classes': 'Classes',
    'imbalance': 'Majority class fraction',
    
    # models
    'bert-base-uncased': 'BERT',
    'countvectorizer': 'Bag of ngrams',
    'bert-finetuned': 'BERT finetuned',
    'tfidfvectorizer': 'TF-IDF',
}