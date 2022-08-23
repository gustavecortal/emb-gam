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
    dsets = [d for d in sorted(os.listdir(config.results_dir))
             if not d.endswith('.pkl')]
    for dset_filter in dset_filters:
        dsets = [d for d in dsets if dset_filter in d]
    rs = []
    print('dsets', dsets)
    for dset in dsets:
        print('\tprocessing', dset)
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
        r['layer'] = r['layer'].fillna('pooler_output')
        r = r.fillna('')
        r['dataset'] = dset
        rs.append(r)
    rs = pd.concat(rs)
    return rs

def get_dir_name(args, full_dset=False, ngrams=None, seed=None):
    
    # handle arguments
    subsample = args.subsample
    if full_dset:
        subsample = -1
    if not ngrams:
        ngrams = args.ngrams        
        
    # create dir_name
    dir_name = f"ngram={ngrams}_" + 'sub=' + str(subsample) + '_' + args.checkpoint.replace('/', '-') # + "_" + padding
    
    
    # append extra things
    if not args.layer == 'pooler_output':
        dir_name += '__' + args.layer
    if args.parsing:
        dir_name += '__' + args.parsing
    if seed:
        dir_name += '__' + str(seed)        
    if hasattr(args, 'all') and args.all == 'all':
        dir_name += '-all'
    return dir_name


DSETS_RENAME_DICT = {
    'emotion': 'Emotion',
    'sst2': 'SST2',
    'tweet_eval': 'Tweet (Hate)',
    'rotten_tomatoes': 'Rotten tomatoes',
    'financial_phrasebank': 'Financial phrasebank',
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
    'countvectorizer': 'Bag of ngrams',
    'tfidfvectorizer': 'TF-IDF',    
    'bert-finetuned': 'Emb-grams (BERT finetuned)',
    'bert-base-uncased': 'Emb-grams (BERT)',
    'distilbert-finetuned': 'Emb-grams (DistilBERT finetuned)',  
    'distilbert-base-uncased': 'Emb-grams (DistilBERT)',
    'bert-base-uncased___last_hidden_state_mean': 'Emb-grams (BERT final layer)',
    'bert-finetuned___last_hidden_state_mean': 'Emb-grams (BERT finetuned final layer)',

}