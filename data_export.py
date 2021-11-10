import glob
from pathlib import Path

import pandas as pd
from icecream import ic
import wfdb

from util import *

# pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 7)


class DataExport:
    """
    Integrate & export collected 12-lead ECG datasets
    """

    def __init__(self, fqs=250):
        """
        :param fqs: (Potentially re-sampling) frequency
        """
        cols = ['dataset', 'patient_name', 'record_name', 'record_path']
        df = pd.DataFrame(columns=cols)

        d_dsets = config('datasets')
        dnms_selected = ['INCART', 'PTB_XL']
        for dnm in dnms_selected:
            d_dset = d_dsets[dnm]
            dir_nm = d_dset['dir_nm']
            path = f'{PATH_BASE}/{DIR_DSET}/{dir_nm}'
            ic(path)
            ic(d_dset['rec_fmt'])

            # def get_get_comment():
            #     def ptb_xl(rec):
            #         ic(rec)
            #
            #     d_f = dict(
            #         INCART=lambda rec: f'{rec.comments[0]}, {rec.comments[2]}',
            #         PTB_XL=ptb_xl
            #     )
            #     return d_f[dnm]

            def get_get_row(fnm_):
                path_r = fnm_.split('/')
                path_r = '/'.join(path_r[path_r.index(dir_nm):-1])  # From `datasets` to record file name, exclusive
                rec_nm = Path(fnm_).stem
                # ic(path_r, rec_nm)
                path_no_ext = fnm_[:fnm_.index('.')]
                rec = wfdb.rdrecord(path_no_ext, sampto=1)  # Don't need to see the signal
                # ic(rec.comments)

                def get_get_pat_num():
                    def incart():
                        return rec.comments[1]

                    def ptb_xl():
                        if not hasattr(ptb_xl, 'rec_labels'):
                            ptb_xl.csv = pd.read_csv(f'{path}/ptbxl_database.csv', usecols='patient_id')
                            ptb_xl.count = 0
                            ic(ptb_xl.csv)

                        pat = ptb_xl.csv[ptb_xl.count]
                        ptb_xl.count += 1
                        return pat

                    d_f = dict(
                        INCART=incart,
                        PTB_XL=ptb_xl
                    )
                    return d_f[dnm]
                if dnm == 'PTB_XL':
                    ic(rec.comments)
                    exit(1)

                # get_comment = get_get_comment()
                get_pat_num = get_get_pat_num()
                # comments = get_comment(rec)
                pat_nm = get_pat_num()
                return [dnm, pat_nm, rec_nm, path_r]

            def incart(fnm_):
                path_r = fnm_.split('/')
                path_r = '/'.join(path_r[path_r.index(dir_nm):-1])  # From `datasets` to record file name, exclusive
                rec_nm = Path(fnm_).stem
                # ic(path_r, rec_nm)
                rec = wfdb.rdrecord(fnm_[:fnm_.index('.')], sampto=1)  # Don't need to see the signal
                # ic(rec.comments)
                ic(rec)
                comments = f'{rec.comments[0]}, {rec.comments[2]}'
                pat_nm = rec.comments[1]
                return [dnm, pat_nm, rec_nm, path_r, comments]

            def ptb_xl(fnm_):
                pass
            recs = sorted(glob.iglob(f'{path}/{d_dset["rec_fmt"]}', recursive=True))
            ic(len(recs), recs[:5])
            ic(get_get_row(recs[0]))
            # ic(recs)
            df_ = pd.concat([pd.DataFrame([get_get_row(fnm)], columns=cols) for fnm in recs], ignore_index=True)
            ic(df_)
        ic(df)


if __name__ == '__main__':
    de = DataExport()