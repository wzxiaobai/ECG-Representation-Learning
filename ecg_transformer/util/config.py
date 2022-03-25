# import os
# import math
# import glob
# from typing import List, Dict, Tuple, Optional
#
# import pandas as pd
# import wfdb

from ecg_transformer.util import *
# from ecg_transformer.util import PATH_BASE, DIR_PROJ, DIR_DSET
# from ecg_transformer.util import get, set_, keys, get_my_rec_labels  # TODO


config_dict = {
    'meta': dict(
        path_base=PATH_BASE,
        dir_proj=DIR_PROJ,
        dir_dset=DIR_DSET
    ),
    DIR_DSET: dict(
        BIH_MVED=dict(
            nm='MIT-BIH Malignant Ventricular Ectopy Database',
            dir_nm='MIT-BIH-MVED'
        ),
        INCART=dict(
            dir_nm='St-Petersburg-INCART',
            nm='St Petersburg INCART 12-lead Arrhythmia Database',
            rec_fmt='*.dat',  # For glob search
        ),
        PTB_XL=dict(
            nm='PTB-XL, a large publicly available electrocardiography dataset',
            dir_nm='PTB-XL',
            rec_fmt='records500/**/*.dat',  # the 500Hz signals
        ),
        PTB_Diagnostic=dict(
            nm='PTB Diagnostic ECG Database',
            dir_nm='PTB-Diagnostic',
            rec_fmt='**/*.dat',
            path_label='RECORDS'
        ),
        CSPC=dict(
            nm='China Physiological Signal Challenge 2018',
            dir_nm='CSPC-2018',
            rec_fmt='*.mat',
        ),
        CSPC_CinC=dict(
            nm='China Physiological Signal Challenge 2018 - from CinC',
            dir_nm='CSPC-2018-CinC',
            rec_fmt='*.mat',
        ),
        CSPC_Extra_CinC=dict(
            nm='China Physiological Signal Challenge 2018, unused/extra - from CinC',
            dir_nm='CSPC-2018-Extra-CinC',
            rec_fmt='*.mat',
        ),
        G12EC=dict(
            nm='Georgia 12-lead ECG Challenge (G12EC) Database',
            dir_nm='Georgia-12-Lead',
            rec_fmt='*.mat',
        ),
        CHAP_SHAO=dict(
            nm='Chapman University, Shaoxing People’s Hospital 12-lead ECG Database',
            dir_nm='Chapman-Shaoxing',
            rec_fmt='ECGData/*.csv',
            # Taken from paper
            # *A 12-lead electrocardiogram database for arrhythmia research covering more than 10,000 patients*
            fqs=500
        ),
        CODE_TEST=dict(
            nm='CODE-test: An annotated 12-lead ECG dataset',
            dir_nm='CODE-test',
            rec_fmt='ecg_tracings.hdf5',
            fqs=400
        ),
        my=dict(
            nm='Stefan-12-Lead-Combined',
            dir_nm='Stef-Combined',
            fnm_labels='records.csv',
            rec_fmt='%s-combined.hdf5',
            rec_fmt_denoised='%s-denoised.hdf5',
        )
    ),
    'datasets_export': dict(
        total=['INCART', 'PTB_XL', 'PTB_Diagnostic', 'CSPC_CinC', 'CSPC_Extra_CinC', 'G12EC', 'CHAP_SHAO', 'CODE_TEST'],
        support_wfdb=['INCART', 'PTB_XL', 'PTB_Diagnostic', 'CSPC_CinC', 'CSPC_Extra_CinC', 'G12EC']
    ),
    'random_seed': 77,
    'pre_processing': dict(
        zheng=dict(
            low_pass=dict(
                passband=50,
                stopband=60,
                passband_ripple=1,
                stopband_attenuation=2.5
            ),
            nlm=dict(
                smooth_factor=1.5,
                window_size=10
            )
        )
    )
}


def extract_ptb_codes():
    # Set supervised downstream task, PTB-XL, label information
    def is_nan(x) -> bool:
        return not isinstance(x, str) and math.isnan(x)

    def map_row(row: pd.Series) -> Dict:
        return dict(
            aspects=[k for k, v in row.iteritems() if k in ('diagnostic', 'form', 'rhythm') and v == 1],
            diagnostic_class=row.diagnostic_class if not is_nan(row.diagnostic_class) else None,
            diagnostic_subclass=row.diagnostic_subclass if not is_nan(row.diagnostic_subclass) else None
        )
    path_ptb = os.path.join(PATH_BASE, DIR_DSET, get(config_dict, f'{DIR_DSET}.PTB_XL.dir_nm'))
    df_ptb = pd.read_csv(
        os.path.join(path_ptb, 'scp_statements.csv'),
        usecols=['Unnamed: 0', 'diagnostic', 'form', 'rhythm', 'diagnostic_class', 'diagnostic_subclass'],
        index_col=0
    )
    codes = {code: map_row(row) for code, row in df_ptb.iterrows()}
    id2code = list(df_ptb.index)  # Stick to the same ordering
    assert len(id2code) == 71
    code2id = {c: i for i, c in enumerate(id2code)}
    # from icecream import ic  # TODO: remove
    # ic(codes, code2id)
    set_(config_dict, 'datasets.PTB_XL.code', dict(codes=codes, code2id=code2id, id2code=id2code))
    # exit(1)


def extract_datasets_meta():
    # Extract more metadata per dataset
    df_label = get_my_rec_labels()
    sup = config_dict['datasets_export']['support_wfdb']
    for dnm in config_dict['datasets_export']['total']:
        df_ = df_label[df_label['dataset'] == dnm]
        d_dset = config_dict[DIR_DSET][dnm]

        d_dset['n_rec'] = df_.shape[0]

        uniqs = df_['patient_name'].unique()
        d_dset['n_pat'] = 'Unknown' if len(uniqs) == 1 and math.isnan(uniqs[0]) else len(uniqs)

        if dnm in sup:
            path_ = f'{PATH_BASE}/{DIR_DSET}/{d_dset["dir_nm"]}'
            rec_path = next(glob.iglob(f'{path_}/{d_dset["rec_fmt"]}', recursive=True))
            d_dset['fqs'] = wfdb.rdrecord(rec_path[:rec_path.index('.')], sampto=1).fs


def set_paths():
    # Accommodate other OS
    for key in keys(config_dict):
        from icecream import ic
        ic(key)
        val = get(config_dict, key)
        if key[key.rfind('.')+1:] == 'dir_nm':
            set_(config_dict, key, os.path.join(*val.split('/')))


def wrap_config():
    for dnm, d in config_dict[DIR_DSET].items():
        if 'rec_fmt' in d:
            fmt = d['rec_fmt']
            d['rec_ext'] = fmt[fmt.index('.'):]


extract_ptb_codes()
extract_datasets_meta()
set_paths()
wrap_config()
config_dict: Dict
d_my = config_dict['datasets']['my']
config_dict['path-export']: str = os.path.join(PATH_BASE, DIR_DSET, d_my['dir_nm'])


if __name__ == '__main__':
    import json

    from icecream import ic

    fl_nm = 'config.json'
    ic(config_dict)
    with open(f'{PATH_BASE}/{DIR_PROJ}/{fl_nm}', 'w') as f:
        json.dump(config_dict, f, indent=4)