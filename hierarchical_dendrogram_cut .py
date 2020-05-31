# Imports
import pandas as pd
import numpy as np
from scipy.spatial import distance as ssd
from dtaidistance import dtw
from scipy.cluster.hierarchy import linkage, dendrogram, inconsistent
import matplotlib.pyplot as plt
import time

import warnings
warnings.filterwarnings("ignore")

# variable to adjust the number of clusters, takes values >= 1
# Ideal values should be 1 , but for smaller datasets, can be set little higher to reduce the number of clusters
BIN_FACTOR = 2


def _cluster(df):

    flow_df = df.copy()
    sites = df['Site'].to_list()
    sites_len = len(sites)

    df = df.fillna(0).drop(columns=["Site", "Flow"])
    df = df.to_numpy()

    try:
        distance = dtw.distance_matrix_fast(df, compact=True)
    except Exception as e:
            print('Distance calculation failed, shoudnt continue')
            exit(99)

    distance_ssd = ssd.squareform(distance)

    # Hierarchical clustering - linkage matrix Z
    Z = linkage(distance_ssd, "average")

    # Inconsistent matrix - has mean-distance, standard dev's for each linkage
    IN = inconsistent(Z)

    # Creating a temporary data-frame to extract clusters from linkage and inconsistent matrices
    cols = ['pt1', 'pt2', 'dist', 'tot_pts', 'mean_dist', 'SD_dist', 'cls_level', 'co_eff']
    temp_df = pd.DataFrame(np.hstack([Z, IN]), columns=cols)

    # get the bin's - only using the range from the first level clustering distances
    # Further clustering level will increase linkages' mean distance
    # points that fall above first level mean-distances are deemed as outliers
    cls_level_1_distances = temp_df.loc[temp_df['cls_level'] == 1, 'mean_dist']
    q1, q3 = np.percentile(cls_level_1_distances, [25, 75])
    IQR = q3 - q1

    # Handy formula to calculate bin width - to make sure bin counts are minimal but represents the spread well
    bw = 2 * IQR/ int(round(sites_len ** (1. / 3))) * BIN_FACTOR

    bins_ = (np.arange(min(cls_level_1_distances)- 0.1, max(cls_level_1_distances) + bw, bw))

    # hierarchical clustering groups data till it reaches a single cluster that has all data points
    # we don't need rows from linkage matrix, which represents higher level clustering,
    # keeping link rows only the leaf_nodes (i.e single site data point)
    temp_df = temp_df[(temp_df['pt1'] < sites_len) | (temp_df['pt2'] < sites_len) ]

    # apply the bins
    temp_df['bins'] = pd.cut(temp_df['mean_dist'], bins_ ).astype('str')

    # Map digits to intervals , for readability
    map_dict = {str(value):counter for counter, value in enumerate(temp_df['bins'].unique()) if value != 'nan'}
    temp_df['Cluster'] = temp_df['bins'].map(map_dict)

    # NaNs are the outliers , treat them as singleton cluster, giving name to each NAN
    total_nans = (temp_df['Cluster'].isna().sum())
    temp_df.loc[temp_df['Cluster'].isna(), 'Cluster'] = [ 'O' + str(i) for i in range(1,total_nans+1) ]

    # Combine linkage matrix columns - to create a single column view of, site vs cluster mapping
    df1 = temp_df.loc[temp_df['pt1'] < sites_len, ['pt1', 'Cluster']].rename(columns={'pt1':'Site'}).copy()
    df2 = temp_df.loc[temp_df['pt2'] < sites_len, ['pt2', 'Cluster']].rename(columns={'pt2':'Site'}).copy()
    temp_df = pd.concat([df1, df2]).sort_values(by='Site').reset_index(drop=True)
    flow_df['Cluster'] = temp_df['Cluster']

    # # visualizing
    # sites_n = [(str(site) + '-' + str(i)) for site, i in enumerate(sites)]
    # fig, ax = plt.subplots()
    # fig.set_size_inches(20,40)
    # dend = dendrogram(Z, leaf_rotation=90, leaf_font_size=8, labels=sites_n, ax=ax)
    # plt.show()
    return flow_df


# ----------------  exposed method ----------------------------------

def cluster(df):

    print("Clustering: Creating clusters by flow groups...")
    starttime = time.time()

    flows = df['Flow'].unique()
    out_df = pd.DataFrame()

    for flow in flows:
        print('running for the flow ', flow)
        flow_df = df[df["Flow"] == flow]
        temp_df = _cluster(flow_df)
        temp_df['Flow'] = flow

        out_df = out_df.append(temp_df)

    # keep a mapping of store vs cluster
    store_map = out_df[['Flow', 'Site', 'Cluster']].reset_index(drop=True).copy()
    out_df = out_df.drop(columns=['Site'])

    # Take the mean values for the given flow-cluster
    clustered_df = out_df.groupby(['Flow', 'Cluster'], as_index=False).mean()

    print(f"------------ Clustering complete ------------")
    print(f"Task completed in {(time.time() - starttime) / 60:8.2f} minutes")

    return clustered_df, store_map